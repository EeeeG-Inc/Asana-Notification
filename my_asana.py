import asana
from unittest import result
from config import Config
import datetime
import json
from pprint import pprint
import requests
import time
from zoneinfo import ZoneInfo
import sys

class MyAsana():
    DEFAUL_LIMIT = 14

    def __init__(self):
        self.config = Config()
        self.today = datetime.date.today()
        self.jst_today = datetime.datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d")
        self.default_limit = self.DEFAUL_LIMIT

    """
    ワークスペースに参加しているユーザ全員を取得する
    """
    def get_users(self):
        return self.config.client.users.get_users_for_workspace(self.config.workspace_id)

    """
    プロジェクト情報を取得する
    内在しているタスク、プロジェクト名称など取得できる
    """
    def get_project(self, project_id):
        return self.config.client.projects.get_project(project_id)

    """
    単一プロジェクトに紐付いたセクションを取得する
    """
    def find_sections_for_project(self, project_id):
        return self.config.client.sections.get_sections_for_project(project_id)

    """
    単一プロジェクトに紐付いたタスクを取得する
    """
    def find_tasks_by_project(self, project_id):
        opt_fields = [
            'name',
            'due_on',
            'custom_fields',
            'assignee',
            'assignee.name',
            'memberships.section',
            'memberships.section.name'
        ],
        return self.config.client.tasks.get_tasks_for_project(project_id, opt_fields=opt_fields, completed_since='now')

    """
    従業員に紐付いた、全てのプロジェクトのタスクを取得する
    """
    def find_tasks_by_assignee(self, assignee_id):
        opt_fields = [
            'name',
            'due_on',
            'custom_fields',
            'assignee',
            'assignee.name',
            'memberships.section',
            'memberships.section.name'
        ]
        return self.config.client.tasks.get_tasks(assignee=assignee_id, workspace=self.config.workspace_id, opt_fields=opt_fields, completed_since='now')

    """
    Slack 投稿用のテキストを作成
    """
    def get_str_deadline_tasks(self, project_id, section_ids):
        text = '期限切れのタスク一覧\n'
        count = 0

        tasks = self.find_tasks_by_project(project_id)
        for task in tasks:
            section = self.get_section(section_ids, task)

            # 期限が今日までタスクを取得
            if not self.is_within_limit(task, 0):
                continue

            section_name = section['name'] if section is not None else None
            name = task['name']
            assignee_name = task['assignee']['name'] if task['assignee'] is not None else None
            due_on = task['due_on']
            gid = task['gid']

            text += f'■ [{section_name}]\t' + \
                f'{name}\t' + \
                f'{assignee_name}\t' + \
                f'{due_on}\t' +\
                f'https://app.asana.com/0/{project_id}/{gid}' + \
                '\n'

            count += 1

        if count == 0:
            text = None

        return text

    """
    Notion に貼り付けるとインラインデータベースになる Markdown テーブル書式のテキストを作成 (個別でタスクを表示)
    is_plaintext を True にすると、Slack 通知用の形式で取得できる
    """
    def get_str_assignee_tasks(self, section_ids, assignee, is_plaintext=False, limit=DEFAUL_LIMIT, is_simple=False):
        assignee_id = assignee['gid']
        tasks = self.find_tasks_by_assignee(assignee_id)
        # ジェネレーターは使うと消失するので、リストで永続化する
        tasks = list(tasks)

        if len(tasks) < 1:
            texts = {
                self.config.NOTION: self.get_text_for_no_task(assignee),
                self.config.TICKTICK: self.get_text_for_no_task(assignee),
            }
            return texts

        texts = {
            self.config.NOTION: self.init_text(assignee, is_plaintext, self.config.NOTION, is_simple),
            self.config.TICKTICK: self.init_text(assignee, is_plaintext, self.config.TICKTICK, is_simple)
        }

        for task in tasks:
            if not self.is_within_limit(task, limit):
                continue

            section = self.get_section(section_ids, task)
            texts = self.add_task_to_text(task, texts, section, is_simple)

        return self.end_text(texts, is_plaintext)

    """
    Notion に貼り付けるとインラインデータベースになる Markdown テーブル書式のテキストを作成 (全員のタスクを表示)
    is_plaintext を True にすると、Slack 通知用の形式で取得できる
    """
    def get_str_assignee_tasks_for_all(self, section_ids, assignees, is_plaintext=False, limit=DEFAUL_LIMIT):
        text = self.init_text_for_all()

        for assignee in assignees:
            assignee_id = assignee['gid']
            tasks = self.find_tasks_by_assignee(assignee_id)
            for task in tasks:
                if not self.is_within_limit(task, limit):
                    continue

                section = self.get_section(section_ids, task)
                text = self.add_task_to_text_for_all(task, text, section)

        return text

    """
    Asana でとってきたタスクにセクションを設定する
    ※ EeeeG では Open / Icebox / Backlog / In Progress / Closed / Milestone といった Board 情報が該当する
    事前に find_sections_for_project でセクションを取得していないと None になってしまう
    """
    def get_section(self, section_ids, task):
        if task['memberships'] is None:
            return None

        for membership in task['memberships']:
            if membership['section'] is None:
                continue

            if membership['section']['gid'] in section_ids:
                return membership['section']

        return None

    """
    今日から何日後以降のタスクは不要、という判定を作成できる
    """
    def is_within_limit(self, task, limit=0):
        if task['due_on'] is None:
            return False

        due_on = datetime.datetime.strptime(task['due_on'], "%Y-%m-%d")
        due_on_time = time.localtime(datetime.datetime(due_on.year, due_on.month, due_on.day).timestamp())
        after_week = time.strptime(str(self.today + datetime.timedelta(days=limit)), "%Y-%m-%d")

        if due_on_time > after_week:
            return False

        return True

    """
    Slack API (Slack App) でチャンネル情報を取得する
    """
    def get_slack_channels_via_api(self):
        channels = []

        # private チャンネルのデータを取るには、作成した Slack したアプリをチャンネルに追加しないといけない
        res = requests.post('https://slack.com/api/conversations.list', data={
            'token': self.config.slack_app_token,
            'types': 'public_channel,private_channel',
        }).json()

        if res['channels'] is None:
            return None

        for channel in res['channels']:
            channels.append({
                'name': channel['name'],
                'id': channel['id'],
            })

        return channels

    """
    Slack API (Slack App) で該当する Slack チャンネルに Post する
    """
    def slack_post_via_api(self, text, bot_name, bot_emoji, channel_id, is_snipet=True):
        if self.config.is_debug:
            channel_id = self.config.channel_ids['default']

        if is_snipet:
            # content にスニペット内容を指定すればファイル生成しなくて済む
            requests.post('https://slack.com/api/files.upload', data={
                'token': self.config.slack_app_token,
                'channels': channel_id,
                'title': str(self.jst_today) + '-todo.md',
                'filename': str(self.jst_today) + "-todo.md",
                'filetype': "markdown",
                'content': text,
            })
        else:
            requests.post('https://slack.com/api/chat.postMessage', data={
                'token': self.config.slack_app_token,
                'channel': channel_id,
                'text': text,
                'filename': 'test.md',
                'username': bot_name,
                'icon_emoji': bot_emoji,
                # ポストされるメンションの有効化
                'link_names': 1,
            })

    """
    Webhook で該当する Slack チャンネルに Post する
    specify_webhook_url で直接 webhook_url を指定することも可能
    """
    def slack_post_via_webhook(self, project_id, text, bot_name, bot_emoji, specify_webhook_url=None):
        webhook_url = None

        if specify_webhook_url is None:
            # project_id に紐づく webhook_url を検索
            for key, val in self.config.project_ids.items():
                if val == project_id:
                    webhook_url = self.config.webhook_urls[key]
                    break
        else:
            webhook_url = specify_webhook_url

        # 紐づく webhook_url がなかった場合、もしくはデバッグモード有効の場合はデフォルトチャンネルに通知する
        if (webhook_url is None) or (self.config.is_debug):
            webhook_url = self.config.webhook_urls['default']

        requests.post(webhook_url, json.dumps({
            'text': text,
            'username': bot_name,
            'icon_emoji': bot_emoji,
            # ポストされるメンションの有効化
            'link_names': 1,
        }))

    def get_text_for_no_task(self, assignee):
        name = assignee['name']

        text = f'*{name}*\n'
        text += '```'
        text += 'Nothing\n'
        text += '```'
        return text

    """
    get_str_assignee_tasks のメッセージ初期化
    """
    def init_text(self, assignee, is_plaintext, target, is_simple):
        text = ''
        name = assignee['name']

        if is_plaintext:
            text += f'*{name}*\n'
            text += '```'

        if target == self.config.NOTION:
            if not is_simple:
                text += '|Priority|Task|Due on|MTG date|Workload|Progress (%)|Section|Note|Exported|\n'
                text += '|:-|:-|:-|:-|:-|:-|:-|:-|:-|\n'

        return text

    """
    get_str_assignee_tasks のメッセージ初期化
    """
    def init_text_for_all(self):
        text = '|Priority|Task|Due on|MTG date|Assignee|Workload|Progress (%)|Section|Note|Exported|\n'
        text += '|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|\n'

        return text

    """
    get_str_assignee_tasks のメッセージにタスク追加
    """
    def add_task_to_text(self, task, texts, section, is_simple):
        custom_field_values = self.__get_customfield_values(task)
        note = custom_field_values['note']
        mtg_date = custom_field_values['mtg_date']
        workload = custom_field_values['workload']
        progress = custom_field_values['progress']
        gid = task['gid']
        due_on = task['due_on']
        name = task['name']
        section_name = section['name'] if section is not None else None

        # Notion 用のテキスト整形
        if is_simple:
            # 数値リスト
            texts[self.config.NOTION] += '1. ' + \
                f'[{name}](https://app.asana.com/0/0/{gid})' + \
                '\n'
        else:
            # テーブル
            texts[self.config.NOTION] += '|' + \
                f'|[{name}](https://app.asana.com/0/0/{gid})' + \
                f'|{due_on}' +\
                f'|{mtg_date}' + \
                f'|{workload}' + \
                f'|{progress}' + \
                f'|{section_name}' + \
                f'|{note}' + \
                f'|{str(self.jst_today)}' + \
                '|\n'

        # TickTick 用のテキスト整形
        texts[self.config.TICKTICK] += f'{due_on} ' + \
            f'[{name}]' + \
            f'(https://app.asana.com/0/0/{gid}) ' + \
            f'exported on {str(self.jst_today)}' + \
            '\n'

        return texts

    """
    get_str_assignee_tasks のメッセージにタスク追加
    """
    def add_task_to_text_for_all(self, task, text, section):
        custom_field_values = self.__get_customfield_values(task)

        assignee = task.assignee.name
        note = custom_field_values['note']
        mtg_date = custom_field_values['mtg_date']
        workload = custom_field_values['workload']
        progress = custom_field_values['progress']
        gid = task['gid']
        due_on = task['due_on']
        name = task['name']
        section_name = section['name'] if section is not None else None

        # Notion 用のテキスト整形
        text += '|' + \
            f'|[{name}](https://app.asana.com/0/0/{gid})' + \
            f'|{due_on}' +\
            f'|{mtg_date}' + \
            f'|{assignee}' + \
            f'|{workload}' + \
            f'|{progress}' + \
            f'|{section_name}' + \
            f'|{note}' + \
            f'|{str(self.jst_today)}' + \
            '|\n'

        return text

    """
    get_str_assignee_tasks のメッセージ終了部分
    """
    def end_text(self, texts, is_plaintext):
        for id, text in texts.items():
            if is_plaintext:
                text += '```'
                texts[id] = text

        return texts

    def __get_customfield_values(self, task):
        custom_field_values = {
            'note': '',
            'mtg_date': '',
            'workload': 0,
            'progress': 0,
        }

        if not task['custom_fields']:
            return custom_field_values

        for custom_field in task['custom_fields']:
            # ほしいカスタムフィールド名を指定する
            if custom_field['name'] == 'Note':
                note = custom_field['text_value'] if custom_field['text_value'] is not None else ''
                # 改行コードがあると、Notion でテーブルが崩れてしまう
                custom_field_values['note'] = note.replace('\n', ' ')
            if custom_field['name'] == 'MTG Date':
                custom_field_values['mtg_date'] = custom_field['date_value'].date if custom_field['date_value'] is not None else ''
            if custom_field['name'] == 'Workload':
                custom_field_values['workload'] = custom_field['number_value'] if custom_field['number_value'] is not None else 0
            if custom_field['name'] == 'Progress (%)':
                custom_field_values['progress'] = custom_field['number_value'] * 100 if custom_field['number_value'] is not None else 0

        return custom_field_values

from config import Config
import datetime
import json
import requests
import time


class MyAsana():
    def __init__(self):
        self.config = Config()
        self.today = datetime.date.today()

    """
    ワークスペースに参加しているユーザ全員を取得する
    """
    def get_users(self):
        return list(self.config.client.users.get_users({'workspace': self.config.workspace_id}, opt_pretty=True))

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
        return self.config.client.sections.get_sections_for_project(project_id, {}, opt_pretty=True)

    """
    単一プロジェクトに紐付いたタスクを取得する
    """
    def find_tasks_by_project(self, project_id):
        param = {
            'completed_since': 'now',
            'project': project_id,
            'opt_fields': [
                'this.name',
                'this.due_on',
                'this.custom_fields',
                'this.assignee',
                'this.assignee.name',
                'this.memberships.section',
                'this.memberships.section.name'
            ],
        }

        return self.config.client.tasks.get_tasks(param, opt_pretty=False)

    """
    従業員に紐付いた、全てのプロジェクトのタスクを取得する
    """
    def find_tasks_by_assignee(self, assignee_id):
        param = {
            'completed_since': 'now',
            'opt_fields': [
                'this.name',
                'this.due_on',
                'this.custom_fields',
                'this.assignee',
                'this.assignee.name',
                'this.memberships.section',
                'this.memberships.section.name'
            ],
        }

        if assignee_id:
            param['assignee'] = assignee_id
            param['workspace'] = self.config.workspace_id

        return self.config.client.tasks.get_tasks(param, opt_pretty=False)

    """
    Slack 投稿用のテキストを作成
    """
    def get_str_deadline_tasks(self, project_id, section_ids):
        text = '期限切れのタスク一覧\n'
        count = 0

        for task in self.find_tasks_by_project(project_id):
            section = self.get_section(section_ids, task)

            # 期限が今日までタスクを取得
            if not self.is_within_limit(task, 0):
                continue

            text += f'■ [{section["name"] if section is not None else None}]\t' + \
                f'{task["name"]}\t' + \
                f'{task["assignee"]["name"] if task["assignee"] is not None else None}\t' + \
                f'{task["due_on"]}\t' +\
                f'https://app.asana.com/0/{project_id}/{task["gid"]}' + \
                '\n'

            count += 1

        if count == 0:
            text = None

        return text

    """
    Notion に貼り付けるとインラインデータベースになる Markdown テーブル書式のテキストを作成
    is_plaintext を True にすると、Slack 通知用の形式で取得できる
    """
    def get_str_assignee_tasks(self, section_ids, assignee, is_plaintext=False, limit=7):
        assignee_id = assignee['gid']
        texts = {
            self.config.NOTION: self.init_text(assignee, is_plaintext, self.config.NOTION),
            self.config.TICKTICK: self.init_text(assignee, is_plaintext, self.config.TICKTICK)
        }

        for task in self.find_tasks_by_assignee(assignee_id):
            # デフォルトでは、期限が 1 週間先までのタスクを取得
            if not self.is_within_limit(task, limit):
                continue

            section = self.get_section(section_ids, task)
            texts = self.add_task_to_text(task, texts, section)

        return self.end_text(texts, is_plaintext)

    """
    Asana でとってきたタスクにセクションを設定する
    ※ EeeeG では Open / Icebox / Backlog / In Progress / Closed / Milestone といった Board 情報が該当する
    事前に find_sections_for_project でセクションを取得していないと None になってしまう
    """
    def get_section(self, section_ids, task):
        sections = list(
            filter(
                lambda x: x['section']['gid'] in section_ids,
                filter(lambda x: 'section' in x, task['memberships'])
            )
        )
        return sections[0]['section'] if len(sections) > 0 else None

    """
    今日から何日後以降のタスクは不要、という判定を作成できる
    """
    def is_within_limit(self, task, limit=0):
        if task["due_on"] is None:
            return False

        due_on = time.strptime(task["due_on"], "%Y-%m-%d")
        after_week = time.strptime(str(self.today + datetime.timedelta(days=limit)), "%Y-%m-%d")

        if due_on > after_week:
            return False

        return True

    """
    該当する Slack チャンネルに Post する
    specify_webhook_url で直接 webhook_url を指定することも可能
    """
    def slack_post(self, project_id, text, bot_name, bot_emoji, specify_webhook_url=None):
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

    """
    get_str_assignee_tasks のメッセージ初期化
    """
    def init_text(self, assignee, is_plaintext, target):
        text = ''

        if is_plaintext:
            text += f'*{assignee["name"]}*\n'
            text += '```'

        if target == self.config.NOTION:
            text += '|Task|Due on|Priority|Workload|Section|URL|Note|Exported|\n'
            text += '|:-|:-|:-|:-|:-|:-|:-|:-|\n'

        return text

    """
    get_str_assignee_tasks のメッセージにタスク追加
    """
    def add_task_to_text(self, task, texts, section):
        # Notion 用のテキスト整形
        texts[self.config.NOTION] += f'|{task["name"]}' + \
            f'|{task["due_on"]}' +\
            '|99' + \
            '|0' + \
            f'|{section["name"] if section is not None else None}' + \
            f'|https://app.asana.com/0/0/{task["gid"]}' + \
            '|' + \
            '|' + \
            f'{str(self.today)}' + \
            '\n'

        # TickTick 用のテキスト整形
        texts[self.config.TICKTICK] += f'{task["due_on"]} ' + \
            f'[{task["name"]}]' + \
            f'(https://app.asana.com/0/0/{task["gid"]}) ' + \
            f'exported on {str(self.today)}'  + \
            '\n'

        return texts

    """
    get_str_assignee_tasks のメッセージ終了部分
    """
    def end_text(self, texts, is_plaintext):
        for id, text in texts.items():
            if is_plaintext:
                text += '```'
                texts[id] = text

        return texts

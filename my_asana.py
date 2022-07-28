from config import Config
import datetime
from dotenv import load_dotenv
import json
import requests
import time


load_dotenv()


class MyAsana():
    def __init__(self):
        self.config = Config()

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
    def find_tasks_for_slack(self, project_id):
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
    def find_tasks_for_notion(self, project_id, assignee_id):
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

        # Assginee + Workspace ※ この絞り込みは project を同時に指定できない
        if assignee_id:
            param['assignee'] = assignee_id
            param['workspace'] = self.config.workspace_id
        else:
            param['project'] = project_id

        return self.config.client.tasks.get_tasks(param, opt_pretty=False)

    """
    Slack 投稿用のテキストを作成
    """
    def get_str_tasks_for_slack(self, project_id, section_ids):
        text = '期限切れのタスク一覧\n'

        for task in self.find_tasks_for_slack(project_id):
            section = self.get_section(section_ids, task)

            # 期限が今日までタスクを取得
            if not self.is_within_limit(task, 0):
                continue

            text += f'■ [{section["name"] if section is not None else None}]\t' + \
                f'{task["name"]}\t' + \
                f'{task["assignee"]["name"] if task["assignee"] is not None else None}\t' + \
                f'{task["due_on"]}\t' +\
                f'https://app.asana.com/0/{project_id}/{task["gid"]}'
            text += "\n"

        return text

    """
    Notion に貼り付けるとインラインデータベースになる Markdown テーブル書式のテキストを作成
    """
    def get_str_tasks_for_notion(self, project_id, section_ids, assignee_id, isSlackNotification=False):
        if isSlackNotification:
            text = '```'
        else:
            text = ''

        text += '|Priority|Section|Task|Name|Due On|Workload|URL|Note|\n'
        text += '|:-|:-|:-|:-|:-|:-|:-|:-|\n'

        for task in self.find_tasks_for_notion(project_id, assignee_id):

            # 期限が 1 週間先までのタスクを取得
            if not self.is_within_limit(task, 7):
                continue

            section = self.get_section(section_ids, task)

            text += '|99' + \
                f'|{section["name"] if section is not None else None}' + \
                f'|{task["name"]}' + \
                f'|{task["assignee"]["name"] if task["assignee"] is not None else None}' + \
                f'|{task["due_on"]}' +\
                '|0' + \
                f'|https://app.asana.com/0/{project_id}/{task["gid"]}' + \
                '|'
            text += "|\n"

        if isSlackNotification:
            text += '```'

        return text

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
        today = datetime.date.today()
        after_week = time.strptime(str(today + datetime.timedelta(days=limit)), "%Y-%m-%d")

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

        # 紐づく webhook_url がなかった場合、デフォルトのチャンネルに通知する
        if webhook_url is None:
            webhook_url = self.config.webhook_urls['default']

        requests.post(webhook_url, json.dumps({
            'text': text,
            'username': bot_name,
            'icon_emoji': bot_emoji,
            # ポストされるメンションの有効化
            'link_names': 1,
        }))

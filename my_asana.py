import asana
import os
import time
import datetime
from dotenv import load_dotenv
import requests
import json

load_dotenv()


class MyAsana():
    def __init__(self):
        self.client = asana.Client.access_token(os.getenv('PERSONAL_ACCESS_TOKEN'))
        self.workspace_id = os.getenv('WORKSPACE_ID')
        self.project_ids = {
            'develop': os.getenv('PROJIECT_ID_DEVELOP'),
            'design': os.getenv('PROJIECT_ID_DESIGN'),
            'general_affairs': os.getenv('PROJIECT_ID_GENERAL_AFFAIRS'),
            'sales': os.getenv('PROJIECT_ID_SALES'),
            'human_resource': os.getenv('PROJIECT_ID_HUMAN_RESOURCE'),
        }
        self.web_hook_urls = {
            'develop': os.getenv('WEBHOOK_URL_DEVELOP'),
            'design': os.getenv('WEBHOOK_URL_DESIGN'),
            'general_affairs': os.getenv('WEBHOOK_URL_GENERAL_AFFAIRS'),
            'sales': os.getenv('WEBHOOK_URL_SALES'),
            'human_resource': os.getenv('WEBHOOK_URL_HUMAN_RESOURCE'),
        }
        self.bot_name = 'Asana Deadline Tasks'
        self.bot_emoji = ':skull:'

    def get_users(self):
        return list(self.client.users.get_users({'workspace': self.workspace_id}, opt_pretty=True))

    def get_project(self, project_id):
        return self.client.projects.get_project(project_id)

    def find_sections_for_project(self, project_id):
        return self.client.sections.get_sections_for_project(project_id, {}, opt_pretty=True)

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

        return self.client.tasks.get_tasks(param, opt_pretty=False)

    """
    指定した担当者の 1 週間以内の期日のタスクを返却する
    """
    def find_tasks_for_notion(self, project_id, assignee_id=None):
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

        # Assginee + Workspace ※ project を同時に指定できない
        if assignee_id:
            param['assignee'] = assignee_id
            param['workspace'] = self.workspace_id
        else:
            param['project'] = project_id

        return self.client.tasks.get_tasks(param, opt_pretty=False)

    def get_str_tasks_for_slack(self, project_id, section_ids):
        text = '期限切れのタスク一覧\n'

        for task in self.find_tasks_for_slack(project_id):
            section = self.get_section(section_ids, task)

            # 期限が 1 週間より先のタスクは無視する
            if not self.is_within_limit(task):
                continue

            text += f'■[{section["name"] if section is not None else None}]\t' + \
                f'{task["name"]}\t' + \
                f'{task["assignee"]["name"] if task["assignee"] is not None else None}\t' + \
                f'{task["due_on"]}\t' +\
                f'https://app.asana.com/0/{project_id}/{task["gid"]}'
            text += "\n"

        return text

    def get_str_tasks_for_notion(self, project_id, section_ids, assignee_id):
        text = '|Priority|Section|Task|Name|Due On|Workload|URL|\n'
        text += '|:-|:-|:-|:-|:-|:-|:-|\n'

        for task in self.find_tasks_for_notion(project_id, assignee_id):

            # 期限が 1 週間より先のタスクは無視する
            if not self.is_within_limit(task, 0):
                continue

            section = self.get_section(section_ids, task)

            text += '|99' + \
                f'|{section["name"] if section is not None else None}' + \
                f'|{task["name"]}' + \
                f'|{task["assignee"]["name"] if task["assignee"] is not None else None}' + \
                f'|{task["due_on"]}' +\
                '|0' + \
                f'|https://app.asana.com/0/{project_id}/{task["gid"]}'
            text += "|\n"

        return text

    def get_section(self, section_ids, task):
        sections = list(
            filter(
                lambda x: x['section']['gid'] in section_ids,
                filter(lambda x: 'section' in x, task['memberships'])
            )
        )
        return sections[0]['section'] if len(sections) > 0 else None

    def is_within_limit(self, task, limit=0):
        if task["due_on"] is None:
            return False

        due_on = time.strptime(task["due_on"], "%Y-%m-%d")
        today = datetime.date.today()
        after_week = time.strptime(str(today + datetime.timedelta(days=limit)), "%Y-%m-%d")

        if due_on > after_week:
            return False

        return True

    def slack_post(self, project_id, text):
        for key, val in self.project_ids.items():
            if val == project_id:
                web_hook_url = self.web_hook_urls[key]
                break

        requests.post(web_hook_url, json.dumps({
            'text': text,
            'username': self.bot_name,
            'icon_emoji': self.bot_emoji,
            # ポストされるメンションの有効化
            'link_names': 1,
        }))

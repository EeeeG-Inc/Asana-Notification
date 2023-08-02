import asana
from dotenv import load_dotenv
import os

load_dotenv()


class Config():
    # project_id と webhook_url は同じ定数キーで紐付けています
    DEVELOP = 'develop'
    DESIGN = 'design'
    MOVIE = 'movie'
    GENERAL_AFFAIRS = 'general_affairs'
    SALES = 'sales'
    HUMAN_RESOURCE = 'human_resource'

    NOTION = 1
    TICKTICK = 2

    def __init__(self):
        is_debug = os.getenv('IS_DEBUG')

        if is_debug is None:
            self.is_debug = False
        else:
            self.is_debug = bool(int(is_debug))

        self.client = asana.Client.access_token(os.getenv('PERSONAL_ACCESS_TOKEN'))
        self.workspace_id = os.getenv('WORKSPACE_ID')
        self.project_ids = {
            self.DEVELOP: os.getenv('PROJIECT_ID_DEVELOP'),
            self.DESIGN: os.getenv('PROJIECT_ID_DESIGN'),
            self.MOVIE: os.getenv('PROJIECT_ID_MOVIE'),
            self.GENERAL_AFFAIRS: os.getenv('PROJIECT_ID_GENERAL_AFFAIRS'),
            self.SALES: os.getenv('PROJIECT_ID_SALES'),
            self.HUMAN_RESOURCE: os.getenv('PROJIECT_ID_HUMAN_RESOURCE'),
        }
        self.webhook_urls = {
            self.DEVELOP: os.getenv('WEBHOOK_URL_DEVELOP'),
            self.DESIGN: os.getenv('WEBHOOK_URL_DESIGN'),
            self.MOVIE: os.getenv('WEBHOOK_URL_MOVIE'),
            self.GENERAL_AFFAIRS: os.getenv('WEBHOOK_URL_GENERAL_AFFAIRS'),
            self.SALES: os.getenv('WEBHOOK_URL_SALES'),
            self.HUMAN_RESOURCE: os.getenv('WEBHOOK_URL_HUMAN_RESOURCE'),
            'default': os.getenv('WEBHOOK_URL_DEFAULT'),
            'weekly_todo_for_notion': os.getenv('WEBHOOK_URL_WEEKLY_TODO_FOR_NOTION'),
            'weekly_todo_for_ticktick': os.getenv('WEBHOOK_URL_WEEKLY_TODO_FOR_TICKTICK'),
        }

        self.channel_ids = {
            'default': os.getenv('CHANNEL_ID_DEFAULT'),
            'weekly_todo_for_notion': os.getenv('CHANNEL_ID_WEEKLY_TODO_NOTIFICATION_FOR_NOTION'),
        }

        self.slack_app_token = os.getenv('SLACK_APP_TOKEN'),

        # 通知不要な退職者などの氏名
        skip_user_names = os.getenv('SKIP_USER_NAMES')
        self.skip_user_names = skip_user_names.split(',')

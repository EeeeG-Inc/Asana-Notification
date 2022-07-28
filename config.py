import asana
from dotenv import load_dotenv
import os

load_dotenv()


class Config():
    # project_id と webhook_url は同じ定数キーで紐付けています
    DEVELOP = 'develop'
    DESIGN = 'design'
    GENERAL_AFFAIRS = 'general_affairs'
    SALES = 'sales'
    HUMAN_RESOURCE = 'human_resource'

    def __init__(self):
        self.client = asana.Client.access_token(os.getenv('PERSONAL_ACCESS_TOKEN'))
        self.workspace_id = os.getenv('WORKSPACE_ID')
        self.project_ids = {
            self.DEVELOP: os.getenv('PROJIECT_ID_DEVELOP'),
            self.DESIGN: os.getenv('PROJIECT_ID_DESIGN'),
            self.GENERAL_AFFAIRS: os.getenv('PROJIECT_ID_GENERAL_AFFAIRS'),
            self.SALES: os.getenv('PROJIECT_ID_SALES'),
            self.HUMAN_RESOURCE: os.getenv('PROJIECT_ID_HUMAN_RESOURCE'),
        }
        self.webhook_urls = {
            self.DEVELOP: os.getenv('WEBHOOK_URL_DEVELOP'),
            self.DESIGN: os.getenv('WEBHOOK_URL_DESIGN'),
            self.GENERAL_AFFAIRS: os.getenv('WEBHOOK_URL_GENERAL_AFFAIRS'),
            self.SALES: os.getenv('WEBHOOK_URL_SALES'),
            self.HUMAN_RESOURCE: os.getenv('WEBHOOK_URL_HUMAN_RESOURCE'),
            'default': os.getenv('WEBHOOK_URL_DEFAULT'),
            'weekly_todo': os.getenv('WEBHOOK_URL_WEEKLY_TODO'),
        }

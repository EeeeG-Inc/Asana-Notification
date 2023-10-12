from my_asana import MyAsana
from pprint import pprint


class AsanaWeeklyTodoNotificationForSlack():

    def run(self):
        asana = MyAsana()
        section_ids_of_all_projects = []
        users = asana.get_users()

        for _, project_id in asana.config.project_ids.items():
            sections = asana.find_sections_for_project(project_id)
            section_ids = [section['gid'] for section in sections]
            for section_id in section_ids:
                section_ids_of_all_projects.append(section_id)

        # text = asana.get_str_assignee_tasks_for_all(section_ids_of_all_projects, users, True)
        # NOTE: Slack が Markdown → インラインデータベースのサポートをやめてしまったのでスニペット通知をするメリットがなくなってしまった
        # asana.slack_post_via_api(text, 'Asana Weekly TODO for ALL', ':calendar:', asana.config.channel_ids['weekly_todo_for_notion'], True)

        # NOTE: Notion で Table の Markdown が上手く表示されなくない場合、ここで True を渡すと箇条書きの Markdown になる
        is_simple = False

        for user in users:
            if user['name'] in asana.config.skip_user_names:
                continue

            texts = asana.get_str_assignee_tasks(
                section_ids_of_all_projects,
                user,
                True,
                asana.DEFAUL_LIMIT,
                is_simple
            )
            asana.slack_post_via_webhook(None, texts[asana.config.NOTION], 'Asana Weekly TODO', ':calendar:', asana.config.webhook_urls['weekly_todo_for_notion'])
            asana.slack_post_via_webhook(None, texts[asana.config.TICKTICK], 'Asana Weekly TODO', ':calendar:', asana.config.webhook_urls['weekly_todo_for_ticktick'])

        print('Slack Post About Weekly TODO Done!')


asana_weekly_todo_notification_for_slack = AsanaWeeklyTodoNotificationForSlack()
asana_weekly_todo_notification_for_slack.run()

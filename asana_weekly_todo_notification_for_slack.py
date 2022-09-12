from my_asana import MyAsana


class AsanaWeeklyTodoNotificationForSlack():

    def run(self):
        asana = MyAsana()
        section_ids_of_all_projects = []
        users = list(asana.get_users())

        for _, project_id in asana.config.project_ids.items():
            section_ids = [section['gid'] for section in asana.find_sections_for_project(project_id)]
            for section_id in section_ids:
                section_ids_of_all_projects.append(section_id)

        # text = asana.get_str_assignee_tasks_for_all(section_ids_of_all_projects, users, True)
        # NOTE: Slack が Markdown → インラインデータベースのサポートをやめてしまったのでスニペット通知をするメリットがなくなってしまった
        # asana.slack_post_via_api(text, 'Asana Weekly TODO for ALL', ':calendar:', asana.config.channel_ids['weekly_todo_for_notion'], True)

        for user in users:
            texts = asana.get_str_assignee_tasks(section_ids_of_all_projects, user, True)
            asana.slack_post_via_webhook(None, texts[asana.config.NOTION], 'Asana Weekly TODO', ':calendar:', asana.config.webhook_urls['weekly_todo_for_notion'])
            asana.slack_post_via_webhook(None, texts[asana.config.TICKTICK], 'Asana Weekly TODO', ':calendar:', asana.config.webhook_urls['weekly_todo_for_ticktick'])

        print('Slack Post About Weekly TODO Done!')


asana_weekly_todo_notification_for_slack = AsanaWeeklyTodoNotificationForSlack()
asana_weekly_todo_notification_for_slack.run()

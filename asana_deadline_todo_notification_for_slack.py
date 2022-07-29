from my_asana import MyAsana


class AsanaDeadlineTodoNotificationForSlack:
    def run(self):
        asana = MyAsana()

        for _, project_id in asana.config.project_ids.items():
            section_ids = [section['gid'] for section in asana.find_sections_for_project(project_id)]
            text = asana.get_str_deadline_tasks_for_slack(project_id, section_ids)
            asana.slack_post(project_id, text, 'Asana Deadline TODO', ':skull:', None)

        print('Slack Post About Deadline Done!')


asana_deadline_todo_notification_for_slack = AsanaDeadlineTodoNotificationForSlack()
asana_deadline_todo_notification_for_slack.run()

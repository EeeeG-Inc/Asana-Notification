from my_asana import MyAsana


class AsanaDeadlineTodoNotificationForSlack:
    def run(self):
        asana = MyAsana()

        for _, project_id in asana.config.project_ids.items():
            sections = asana.find_sections_for_project(project_id)
            section_ids = [section['gid'] for section in sections]
            text = asana.get_str_deadline_tasks(project_id, section_ids)

            if text is not None:
                asana.slack_post_via_webhook(project_id, text, 'Asana Deadline TODO', ':skull:', None)

        print('Slack Post About Deadline Done!')


asana_deadline_todo_notification_for_slack = AsanaDeadlineTodoNotificationForSlack()
asana_deadline_todo_notification_for_slack.run()

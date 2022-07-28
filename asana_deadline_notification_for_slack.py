from my_asana import MyAsana


class AsanaNotificationForSlack:
    def run():
        asana = MyAsana()

        for _, project_id in asana.config.project_ids.items():
            section_ids = [section['gid'] for section in asana.find_sections_for_project(project_id)]
            text = asana.get_str_tasks_for_slack(project_id, section_ids)
            asana.slack_post(project_id, text, 'Asana Deadline Tasks', ':skull:')

        print('Slack Post Done!')


asana_notification_for_slack = AsanaNotificationForSlack()
asana_notification_for_slack.run()

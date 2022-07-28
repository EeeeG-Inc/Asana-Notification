from my_asana import MyAsana

asana = MyAsana()

for department, project_id in asana.project_ids.items():
    section_ids = [section['gid'] for section in asana.find_sections_for_project(project_id)]
    text = asana.get_str_tasks_for_slack(project_id, section_ids)
    asana.slack_post(project_id, text)

print('Slack Post Done!')

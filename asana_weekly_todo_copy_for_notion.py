from my_asana import MyAsana
import pyperclip


class AsanaWeeklyTodoCopyForNotion():

    def run(self):
        asana = MyAsana()
        users = list(asana.get_users())
        users_for_prompt = {}
        user_id = 1
        section_ids_of_all_projects = []

        print('データが欲しい担当者の番号を入力してください')

        for user in users:
            users_for_prompt[user_id] = {
                'gid': user['gid'],
                'name': user['name'],
            }
            print(str(user_id) + '. ' + user['name'])
            user_id += 1

        while True:
            input_user_id = int(input('番号入力: '))
            if input_user_id in users_for_prompt:
                break
            else:
                print('不正な番号です')

        for _, project_id in asana.config.project_ids.items():
            section_ids = [section['gid'] for section in asana.find_sections_for_project(project_id)]
            for section_id in section_ids:
                section_ids_of_all_projects.append(section_id)

        text = asana.get_str_assignee_tasks_for_notion(section_ids_of_all_projects, users_for_prompt[input_user_id])

        pyperclip.copy(text)

        print('Clipboad Copied!')


asana_weekly_todo_copy_for_notion = AsanaWeeklyTodoCopyForNotion()
asana_weekly_todo_copy_for_notion.run()

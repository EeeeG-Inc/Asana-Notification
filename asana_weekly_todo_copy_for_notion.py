from my_asana import MyAsana
import pyperclip


class AsanaWeeklyTodoCopyForNotion():

    def run(self):
        asana = MyAsana()
        section_ids_of_all_projects = []
        users = list(asana.get_users())
        users_for_prompt = self.get_users_for_prompt(users)

        input_user_id = self.input_user_id(users, users_for_prompt)
        input_format_id = self.input_format_id(asana)

        for _, project_id in asana.config.project_ids.items():
            section_ids = [section['gid'] for section in asana.find_sections_for_project(project_id)]
            for section_id in section_ids:
                section_ids_of_all_projects.append(section_id)

        texts = asana.get_str_assignee_tasks(section_ids_of_all_projects, users_for_prompt[input_user_id])

        if input_format_id == asana.config.NOTION:
            pyperclip.copy(texts[asana.config.NOTION])
        else:
            pyperclip.copy(texts[asana.config.TICKTICK])

        print('Clipboad Copied!')

    def input_user_id(self, users, users_for_prompt):
        print('データが欲しい担当者の番号を入力してください')

        for user_id, user in users_for_prompt.items():
            print(str(user_id) + '. ' + user['name'])

        while True:
            input_user_id = int(input('担当者番号入力: '))
            if input_user_id in users_for_prompt:
                break
            else:
                print('不正な番号です')

        return input_user_id

    def input_format_id(self, asana):
        targets_for_prompt = {
            asana.config.NOTION: 'Notion',
            asana.config.TICKTICK: 'TickTick',
        }
        target_id = 0

        print('データのフォーマットを選択してください')

        for target_id, target_name in targets_for_prompt.items():
            print(str(target_id) + '. ' + target_name)

        while True:
            input_format_id = int(input('フォーマット番号入力: '))
            if input_format_id in targets_for_prompt:
                break
            else:
                print('不正な番号です')

        return input_format_id

    def get_users_for_prompt(self, users):
        users_for_prompt = {}
        user_id = 1

        for user in users:
            users_for_prompt[user_id] = {
                'gid': user['gid'],
                'name': user['name'],
            }
            user_id += 1

        return users_for_prompt

asana_weekly_todo_copy_for_notion = AsanaWeeklyTodoCopyForNotion()
asana_weekly_todo_copy_for_notion.run()

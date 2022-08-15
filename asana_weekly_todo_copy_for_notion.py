from my_asana import MyAsana
import pyperclip


class AsanaWeeklyTodoCopyForNotion():

    def run(self):
        is_all = False
        asana = MyAsana()
        section_ids_of_all_projects = []
        users = list(asana.get_users())
        users_for_prompt = self.get_users_for_prompt(users)

        input_user_id = self.input_user_id(users, users_for_prompt)
        input_limit = self.input_limit(asana)

        if input_user_id == 0:
            is_all = True
        else:
            input_format_id = self.input_format_id(asana)

        for _, project_id in asana.config.project_ids.items():
            section_ids = [section['gid'] for section in asana.find_sections_for_project(project_id)]
            for section_id in section_ids:
                section_ids_of_all_projects.append(section_id)

        if is_all:
            text = asana.get_str_assignee_tasks_for_all(section_ids_of_all_projects, users, False, input_limit)
            pyperclip.copy(text)
        else:
            texts = asana.get_str_assignee_tasks(section_ids_of_all_projects, users_for_prompt[input_user_id], False, input_limit)
            if input_format_id == asana.config.NOTION:
                pyperclip.copy(texts[asana.config.NOTION])
            else:
                pyperclip.copy(texts[asana.config.TICKTICK])

        print('\n')
        print('Clipboad Copied!')

    def input_user_id(self, users, users_for_prompt):
        print('データが欲しい担当者の番号を入力してください')
        print('0. ALL [Notion only]')

        for user_id, user in users_for_prompt.items():
            print(str(user_id) + '. ' + user['name'])

        while True:
            input_user_id = int(input('担当者番号入力: '))
            if input_user_id in users_for_prompt:
                break
            elif input_user_id == 0:
                break
            else:
                print('不正な番号です')

        return input_user_id

    def input_limit(self, asana):
        print('\n')
        print('何日以内の期限のタスクを取得しますか (0 - 365 の日数で入力してください)')
        print(f'※ 未入力の場合は {asana.default_limit} 日になります')

        while True:
            limit = input('日数入力: ')

            if (limit == '') or (limit is None):
                limit = asana.default_limit
                print(f'日数入力: {asana.default_limit}')
                break

            if not limit.isdigit():
                print('整数値を入力してください')
                continue

            limit = int(limit)

            if -1 < limit < 366:
                break
            else:
                print('0 - 365 の数値を入力してください')

        return limit

    def input_format_id(self, asana):
        targets_for_prompt = {
            asana.config.NOTION: 'Notion',
            asana.config.TICKTICK: 'TickTick',
        }
        target_id = 0

        print('\n')
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

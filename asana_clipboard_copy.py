from my_asana import MyAsana
import pyperclip

asana = MyAsana()
users = {}
user_id = 1
all_section_ids = []

print('データが欲しい担当者の番号を入力してください')

for user in list(asana.get_users()):
    users[user_id] = user['gid']
    print(str(user_id) + '. ' + user['name'])
    user_id += 1

while True:
    str_user_id = input('番号入力: ')
    if int(str_user_id) in users:
        break
    else:
        print('不正な番号です')

for department, project_id in asana.project_ids.items():
    section_ids = [section['gid'] for section in asana.find_sections_for_project(project_id)]
    for section_id in section_ids:
        all_section_ids.append(section_id)

text = asana.get_str_tasks_for_notion(project_id, all_section_ids, users[int(str_user_id)])

pyperclip.copy(text)

print('Clipboad Copied!')

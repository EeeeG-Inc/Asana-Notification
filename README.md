# Asasna-Notification

- Asana タスクを Slack に通知します
    - GitHub Actions で crontab を設定中
- タスク情報をクリップボードにコピーすることもできます

## 動作環境

```sh
pipenv install
pipenv shell
```

- Python 3.9.6
- Library
    - [asana](https://github.com/Asana/python-asana)
        - Asana ライブラリ
        - Document
            - https://developers.asana.com/docs
    - [pyperclip](https://github.com/asweigart/pyperclip)
        - Python 経由でクリップボードに文字列をコピーしたり、ペーストしたりできる
        - クリップボードが更新されたときに文字列を取得する監視処理も可能
    - [python-dotenv](https://github.com/theskumar/python-dotenv)
        - ローカルで実行するときに `.env` を読み込む

## 環境変数

- Workspace ID
    - https://app.asana.com/api/1.0/workspaces
- Project ID などは URL からとれる

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

### 環境変数

- Asana の Credential
    - Personal Access Token を取得
    - Workspace ID は下記参照
        - https://app.asana.com/api/1.0/workspaces
    - その他の Project ID などは URL から取得可能
- 環境変数の設定
    - GitHub の Repository Secrets に設定
    - `config.py` に設定
    - .`github/workflows/asana_notification_for_slack.yml` の env エントリに設定
    - ローカルで動かしたい場合は `.env` に設定

## スクリプト

- `asana_deadline_notification_for_slack.py`
    - Asana のワークスペース EeeeG, Inc. の特定プロジェクトごとに、本日期限のタスクを専用 Slack チャンネルにお知らせする
    - GitHub Actions の cron で毎日実行中
- `asana_weekly_todo_notification_for_slack.py`
    - Asana のワークスペース EeeeG, Inc. 全体から、従業員ごとに、期限が 1 週間以内のタスクを Slackの `weekly_todo_notification` チャンネルにお知らせする
    - GitHub Actions の cron で毎日実行中
- `asana_weekly_todo_copy_for_notion.py`
    - ローカルで実行すると `asana_weekly_todo_notification_for_slack.py` の内容をクリップボードに保存できる
    - Asana をメンテするミーティングなどで、リアルタイムで TODO が知りたい場合に活用

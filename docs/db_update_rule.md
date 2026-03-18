テーブル追加時のチェックリスト:

models.py でクラスを定義する。

app.py の from models import ... にクラス名を追加する。

db.create_all() で実際のデータベースファイルにテーブルを作成する。
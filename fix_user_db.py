import sqlite3
import os
from datetime import datetime

# アプリのディレクトリ設定
base_dir = os.path.abspath(os.path.dirname(__file__))
# ユーザーDBのパス (app.pyの設定に合わせる)
db_path = os.path.join(base_dir, "users.db")

def fix_database():
    """既存のusers.dbに不足しているカラムを追加する"""
    print(f"対象データベース: {db_path}")

    if not os.path.exists(db_path):
        print("⚠️ データベースファイルが見つかりません。アプリを起動して初期化してください。")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. api_token_count カラムの確認と追加
        try:
            cursor.execute("SELECT api_token_count FROM users LIMIT 1")
            print("✅ api_token_count カラムは既に存在します。")
        except sqlite3.OperationalError:
            print("➕ api_token_count カラムを追加しています...")
            # デフォルト値 100 で追加
            cursor.execute("ALTER TABLE users ADD COLUMN api_token_count INTEGER DEFAULT 100")
            print("   -> 追加完了")

        # 2. last_token_reset カラムの確認と追加
        try:
            cursor.execute("SELECT last_token_reset FROM users LIMIT 1")
            print("✅ last_token_reset カラムは既に存在します。")
        except sqlite3.OperationalError:
            print("➕ last_token_reset カラムを追加しています...")
            # SQLiteではALTER TABLEでNOT NULL制約をつけるのが難しいため、まずはそのまま追加
            # データが入った後にアプリ側のロジック(before_request)が日付をセットします
            cursor.execute("ALTER TABLE users ADD COLUMN last_token_reset TIMESTAMP")
            print("   -> 追加完了")

        conn.commit()
        print("\n🎉 データベースの修正が完了しました！アプリを再起動してください。")

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()

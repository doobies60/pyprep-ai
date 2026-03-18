import sqlite3
import json
import os
print("現在の作業場所:", os.getcwd())
print("フォルダの中身:", os.listdir())

def update_database():
    db_name = 'python_exam_v2.db'
    json_name = 'questions.json'

    # JSONファイルが存在するかチェック
    if not os.path.exists(json_name):
        print(f"エラー: {json_name} が見つかりません。")
        return

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # 既存テーブルをリセット
    cursor.execute("DROP TABLE IF EXISTS questions")
    cursor.execute('''
    CREATE TABLE questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter INTEGER,
        difficulty TEXT,
        question TEXT,
        choice_a TEXT,
        choice_b TEXT,
        choice_c TEXT,
        choice_d TEXT,
        answer TEXT,
        explanation_a TEXT,
        explanation_b TEXT,
        explanation_c TEXT,
        explanation_d TEXT,
        common_explanation TEXT
    )
    ''')

    # JSONを読み込んで登録
    with open(json_name, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for q in data:
        cursor.execute('''
        INSERT INTO questions (chapter, difficulty, question, choice_a, choice_b, choice_c, choice_d, answer, 
                               explanation_a, explanation_b, explanation_c, explanation_d, common_explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (q['chapter'], q['difficulty'], q['question'], q['choice_a'], q['choice_b'], q['choice_c'], q['choice_d'], q['answer'],
              q['explanation_a'], q['explanation_b'], q['explanation_c'], q['explanation_d'], q['common_explanation']))

    conn.commit()
    conn.close()
    print(f"成功: {len(data)} 問を {db_name} に反映しました。")

if __name__ == "__main__":
    update_database()
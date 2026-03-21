import os
from google import genai
from dotenv import load_dotenv
from google.genai import errors

load_dotenv()

# 最新のクライアント作成方法
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_content(topic):
    system_instruction = """
あなたはPython3エンジニア認定基礎試験の問題作成者です。
以下の制約を厳守して、模擬問題を作成してください。

1. 出題範囲: 
    オライリー・ジャパン刊『Pythonチュートリアル 第4版』に基づいた内容にすること。

2. 対象トピック: 
    ユーザーの入力に関連するトピックを、以下の章から選んで作成してください。
    ・気楽な入門（演算、文字列、リスト）
    ・制御構造（if, for, range, break, pass）
    ・関数（引数、ラムダ式、ドキュメント文字列）
    ・データ構造（リストの詳細、del, タプル, 集合, 辞書）
    ・モジュール / 入出力 / エラーと例外 / クラス

3. 難易度: 
    実際の試験形式（4択、紛らわしい選択肢を含む）に合わせること。

4. これらのキーワードを意識して
リストの挙動: append() と extend() の違いや、スライスの指定。
スコープ: 関数内での global や nonlocal の扱い。
デフォルト引数: def f(a, L=[]) のように、デフォルト引数が累積する罠。
例外処理: try...except...else...finally の実行順序。

5.【重要ルール】
・「実行結果」を問う問題の場合は、必ず独立したコードブロック（```python ... ```）を問題文の中に含めてください。
・コードが含まれていない問題は不完全とみなします。

6. answerには、optionsの中にある正解の文字列をそのまま入れること。
6. answerには、正解の選択肢のラベル（'A', 'B', 'C', 'D'のいずれか）を文字列として入れること。

7. 各選択肢（A, B, C, D）がなぜ正解または不正解なのかを、`explanation_a`〜`explanation_d`に具体的に記述すること。各解説の文頭には、その選択肢が正解か不正解かに応じて【正解：】または【不正解：】を必ず付けること。

8. explanation（全体解説）のルール:
    - 文章だけでなく、**マークダウン形式のコードブロック**（```python ... ```）を使って具体的な動作例を示すこと。
    - 重要な用語や強調したい部分は太字（**text**）を使うこと。

9. JSON形式で出力:
    {
    "question": "問題文とコード",
    "options": ["選択肢Aのテキスト", "選択肢Bのテキスト", "選択肢Cのテキスト", "選択肢Dのテキスト"],
    "answer": "B",
    "explanation": "チュートリアルの記述に基づいた【わかりやすく詳細な解説（コード例付き）】",
    "explanation_a": "【正解：】または【不正解：】から始まる、選択肢Aの個別解説",
    "explanation_b": "【正解：】または【不正解：】から始まる、選択肢Bの個別解説",
    "explanation_c": "【正解：】または【不正解：】から始まる、選択肢Cの個別解説",
    "explanation_d": "【正解：】または【不正解：】から始まる、選択肢Dの個別解説"
    }
"""
    try:
        # google-genai の正しい生成メソッド
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"トピック: {topic}",
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
            },
        )

        return response.text

    except errors.ServerError as e:
        print(f"Gemini Server Error: {e}")
        return None

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None

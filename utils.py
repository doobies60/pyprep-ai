def get_chapters_data():
    """章の静的データを返す"""
    return [
        {
            "id": "1",
            "title": "1. 食欲をそそってみようか",
            "desc": "Pythonの概要と特徴について",
            "level": 1,
        },
        {
            "id": "2",
            "title": "2. Pythonインタープリタの使い方",
            "desc": "起動、引数、対話モードの基本",
            "level": 1,
        },
        {
            "id": "3",
            "title": "3. 気楽な入門",
            "desc": "数値、文字列、リストの基本操作",
            "level": 1,
        },
        {
            "id": "4",
            "title": "4. 制御構造",
            "desc": "if, for, range, 関数定義、引数",
            "level": 1,
        },
        {
            "id": "5",
            "title": "5. データ構造",
            "desc": "リストのメソッド、del, タプル, 集合, 辞書",
            "level": 1,
        },
        {
            "id": "6",
            "title": "6. モジュール",
            "desc": "import, パッケージ, dir()関数",
            "level": 2,
        },
        {
            "id": "7",
            "title": "7. 入出力",
            "desc": "f-string, str.format(), ファイル操作",
            "level": 2,
        },
        {
            "id": "8",
            "title": "8. エラーと例外",
            "desc": "構文エラー、try-except, raise",
            "level": 2,
        },
        {
            "id": "9",
            "title": "9. クラス",
            "desc": "スコープ, クラス定義, 継承",
            "level": 2,
        },
        {
            "id": "10",
            "title": "10. 標準ライブラリめぐり",
            "desc": "OSインターフェース, 数学, ネットアクセス",
            "level": 2,
        },
        {
            "id": "11",
            "title": "11. 標準ライブラリめぐり - Part II",
            "desc": "ログ, マルチスレッド, 弱参照",
            "level": 3,
        },
        {
            "id": "12",
            "title": "12. 仮想環境とパッケージ",
            "desc": "venv, pipによる環境構築",
            "level": 3,
        },
        {
            "id": "13",
            "title": "13. 入力行編集とヒストリ置換",
            "desc": "対話モードの効率化機能",
            "level": 3,
        },
        {
            "id": "14",
            "title": "14. 次に読もう",
            "desc": "さらなる学習へのガイドライン",
            "level": 3,
        },
        {
            "id": "mock",
            "title": "🏆 最終模擬テスト (40問形式)",
            "desc": "全範囲からランダムに出題される総合テスト",
            "special": True,
        },
    ]


def create_ai_prompt(topic):
    """AIに問題を生成させるための、詳細な指示付きプロンプトを作成する"""
    return f"Pythonの「{topic}」に関する、少し応用的な4択問題を1問作って。システム指示のJSON形式に従って、各選択肢の解説（explanation_a〜d）も含めて返してください。"
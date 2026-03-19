import streamlit as st

st.set_page_config(
    page_title="🐍 Python3 基礎演習アカデミー 技術スタック", layout="wide"
)

st.title("🐍 Python3 基礎演習アカデミー: アプリケーション技術スタック")
st.info(
    "このドキュメントは、アプリケーションで使用されている主要な言語・技術・機能をまとめたものです。"
)

st.header("📌 アプリケーション概要")
st.markdown(
    """
*   **アプリ名:** 🐍 Python3 基礎演習アカデミー
*   **目的:** Python3エンジニア認定基礎試験の合格を目指す学習支援Webアプリ
*   **特徴:** 従来のデータベース問題と、生成AIによる無限の問題生成・解説を組み合わせたハイブリッド学習システム
"""
)

st.header("🛠️ 使用言語・技術スタック")

col1, col2 = st.columns(2)

with col1:
    st.subheader("サーバーサイド (Backend)")
    st.markdown(
        """
    *   **言語:** Python 3.12+
    *   **フレームワーク:** Flask
        *   **Blueprint:** 機能ごと（`auth`, `main`, `admin`）に分割。
    *   **Webフレームワーク:** Flask
        *   **Blueprint:** アプリケーションを機能単位（`auth`, `main`, `admin`）で分割・管理。
        *   **Flask-SQLAlchemy:** データベース操作 (ORM)。
        *   **Flask-Migrate:** DBマイグレーション (スキーマ変更管理)。
        *   **Flask-Login:** ユーザー認証・セッション管理。
        *   **Flask-WTF:** フォーム作成・バリデーション。
    """
    )

    st.subheader("データベース (Database)")
    st.markdown(
        """
    *   **SQLite:** 軽量リレーショナルデータベース
        *   `python_exam_v2.db`: 試験問題データ。
        *   `users.db`: ユーザー情報、学習履歴。
    """
    )

    # with col2:
    st.subheader("フロントエンド (Frontend)")
    st.markdown(
        """
    *   **テンプレート:** Jinja2
    *   **UI/UX:** HTML5, CSS3, JavaScript
    """
    )

    st.subheader("AI・機械学習 (AI Integration)")
    st.markdown(
        """
    *   **モデル:** Google Gemini (`gemini-3-flash`)
    *   **ライブラリ:** `google-generativeai`
    *   **機能:** AIクイズ生成、深掘り解説。
    """
    )


st.subheader("データ形式 (Data Format)")
st.markdown(
    """
*   **JSON (JavaScript Object Notation):**
    *   **AIとの通信:** Gemini APIとのリクエスト・レスポンスの標準形式。
    *   **DB初期データ:** `questions.json` に問題の元データを格納。
    *   **API応答:** フロントエンドのJavaScriptへ結果を返す際に使用 (`jsonify`)。
"""
)


st.header("🔧 設計・開発ツール")
st.markdown(
    """
*   **Streamlit:**
    *   **画面遷移図 (`diagram.py`):** 画面フローの可視化。
    *   **モックアップ (`mockup.py`):** UIイメージ共有。
    *   **DB検証ツール (`check_db.py`):** DBの中身をGUIで確認 (**pandas** を使用した集計・可視化)。
    *   **DB検証ツール (`check_db.py`):** DBデータの閲覧・管理ダッシュボード。
    *   **技術スタック表示 (このファイル):** プロジェクト構成のドキュメント。
*   **データ処理・分析:**
    *   **pandas:** 管理ツール（`check_db.py`）におけるデータの構造化、統計、グラフ描画用データの作成に使用。
    *   **pandas:** `check_db.py` における学習ログの集計、統計分析、グラフ描画用データの生成に使用。
*   **管理ツール:**
    *   `pip` / `requirements.txt`: パッケージ管理。
    *   `python-dotenv`: 環境変数（APIキー等）の管理。
    *   `update_db.py`: `questions.json` からのDB初期化。
"""
)

st.header("📱 主要機能一覧")
st.markdown(
    """
*   **認証機能:** ユーザー登録、ログイン、ログアウト（Blueprint `auth` で実装）。
*   **学習モード:**
    *   章別演習 / レベル別演習 / 模擬試験 / AIハイブリッド演習
*   **学習サポート:**
    *   成績管理（ダッシュボード）
    *   間違えた問題の復習機能
    *   AIによる深掘り解説
"""
)

st.sidebar.success("技術スタックビューアが選択されています。")

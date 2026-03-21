Python3 基礎演習アカデミー 🐍

Python 3 エンジニア認定基礎試験の合格を強力にサポートする、AI（Gemini）搭載の演習アプリケーションです。

🌟 概要

本プロジェクトは、開発者自らが試験に合格するために「ドッグフーディング（自社製品を自ら使うこと）」手法を取り入れて開発されました。
公式シラバスに基づいた問題データベースと、Google Gemini APIによる動的な解説・問題生成を組み合わせたハイブリッド学習システムです。

🚀 主な機能

セキュアな認証システム: Flask-Loginとハッシュ化（SHA-256）を用いたユーザー管理。

公式シラバス準拠: 出題割合をシラバスに合わせ、本番に近い演習環境を提供。

AIによる深掘り解説: Gemini APIが、正解・不正解の理由をPythonの基本理念（Zen of Python）に基づいて丁寧に解説。

学習履歴の可視化: 苦手な章や進捗度をダッシュボードで確認可能。

🛠 技術スタック

Backend: Python 3.12 / Flask

Database: SQLite / SQLAlchemy (ORM)

AI Integration: Google Gemini 3.1 flash-lite

Frontend: Jinja2 / CSS3 (Responsive Design)

Support Tools: Streamlit (DB管理・可視化用)

📦 セットアップ（開発環境）

リポジトリをクローン

git clone [https://github.com/doobie60/pyprep-ai.git](https://github.com/doobie60/pyprep-ai.git)
cd pyprep-ai


仮想環境の作成とライブラリのインストール

python -m venv .venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate
pip install -r requirements.txt


環境変数の設定
.env ファイルを作成し、以下の項目を設定してください。

GEMINI_API_KEY=あなたのAPIキー
SECRET_KEY=任意の文字列


アプリの起動

python app.py


📝 開発のこだわり

「Simple is better than complex.」というPythonの哲学に基づき、学習者がノイズを感じることなく、最短ルートで理解を深められるUI/UXを追求しました。

👤 著者

鈴木 (@doobie60)

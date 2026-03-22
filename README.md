# Python3 基礎演習アカデミー  
Python学習者向けの「演習・AI解説・学習ログ管理」アプリです。  
Flask / PostgreSQL / Render / Gemini API を使用し、実務に近い構成で開発しました。

## ■ スクリーンショット
<img width="675" height="864" alt="image" src="https://github.com/user-attachments/assets/adb07334-f39a-4f70-9ee7-a92ffc1231fa" />
<img width="1004" height="886" alt="image" src="https://github.com/user-attachments/assets/c3050444-71f8-4d78-ba4b-ff64c1fb3990" />
<img width="986" height="905" alt="image" src="https://github.com/user-attachments/assets/5c57af72-3a78-40ea-a96c-491a136d795d" />

---

## ■ アプリ概要
Python3 エンジニア認定基礎試験の学習をサポートする Web アプリです。  
120問の演習問題、AIによる解説生成、学習ログの記録など、学習効率を高める機能を備えています。

また、**管理者向けの分析ツールを Streamlit で別途開発**し、  
学習データの可視化やユーザーの進捗分析も可能です。

---

## ■ 主な機能

### ● 学習機能
- 章別演習（120問）
- レベル別ランダム演習（初級 / 中級 / 上級）
- 全範囲ランダム演習
- 最終模擬テスト（40問）

### ● AI 機能
- Gemini API による解説生成
- 問題文の要約・補足説明
- DB問題とAI生成問題を組み合わせたハイブリッド出題方式
- AI生成が失敗した場合はDB問題に自動フォールバック
- ユーザーごとの AI 利用回数管理（1日100トークン制限）

### ● ユーザー管理
- 新規登録 / ログイン（Flask-Login）
- パスワードは **Werkzeug によるハッシュ化**で安全に保存
- Flask-WTF によるフォームバリデーション
- CSRF 対策（Flask-WTF の CSRFProtect）

### ● 管理者向け分析ツール（Streamlit）
- 学習ログの可視化
- ユーザーごとの進捗分析
- 正答率・苦手分野の把握
- 本体アプリとは独立した管理ツールとして運用

### ● デプロイ / 運用
- Render による本番デプロイ
- PostgreSQL を使用した本番DB運用
- ローカルと本番で DB を自動切り替え

---

## ■ 技術スタック

### Backend
- Python 3
- Flask
- SQLAlchemy / Flask-Migrate
- PostgreSQL（Render）
- Werkzeug（パスワードハッシュ化）
- Flask-WTF（フォームバリデーション / CSRF）

### Frontend
- HTML / CSS / Bootstrap
- Jinja2 Template

### AI
- Gemini API（genai）

### DevOps
- Render（Webサービス / DB）
- GitHub（バージョン管理）

### 管理ツール
- Streamlit（学習ログ分析）

---

## ■ 工夫した点（実務を意識した設計）

### ● 1. Render 環境での DB 初期化問題を解決  
Render では `if __name__ == "__main__":` が実行されないため、  
DB 初期化コードが動かず、問題データが投入されない課題が発生。  
ログ解析により原因を特定し、  
**Blueprint登録後に app_context を使って自動投入する仕組み**を実装。

### ● 2. AI API のモデル非推奨化に対応  
Gemini API の旧モデルが非推奨化されたため、  
エラー内容を解析し、  
**最新モデル（gemini-2.5-flash）へ移行**。  
例外処理も追加し安定性を向上。

### ● 3. 本番とローカルで DB を自動切り替え  
環境変数 `DATABASE_URL` の有無で  
PostgreSQL / SQLite を自動切り替え。  
実務でよくある構成を再現。

### ● 4. Blueprint 構成で可読性を向上  
`auth / main / admin` に分割し、  
機能ごとに責務を明確化。

### ● 5. セキュリティ対策  
- パスワードは **Werkzeug の generate_password_hash** で保存  
- Flask-WTF による **CSRF トークン**  
- バリデーションによる不正入力防止  
- API の悪用防止として **1ユーザー1日100トークン制限**

### ● 6. UI/UX の改善  
- 進捗バー  
- 完了バッジ  
- 難易度選択ドロップダウン  
- ローディング表示  
- レイアウト調整  

学習アプリとしての使いやすさを重視。

### ● 7. 管理者向け分析ツール（Streamlit）
- 学習ログをグラフ化  
- ユーザーごとの弱点分析  
- 本体アプリと分離し、安全な運用を実現

### ● 8. DB問題とAI生成問題を組み合わせたハイブリッド出題方式
安定性とコスト最適化を両立するため、DB問題とAI生成問題を組み合わせた
ハイブリッド出題方式を採用しています。

- DB：120問の精査済み問題を安定提供  
- AI：Gemini API による新規問題生成  
- 出題時に確率的に切り替え  
- AI生成が失敗した場合はDB問題に自動フォールバック  
- **APIを無駄に消費しないため、AI出題は必要な場面に限定**

これにより、APIコストを抑えつつ、多様で柔軟な出題が可能になっています。

---

## ■ 苦労した点と解決方法（企業が最も評価する部分）

### ● デプロイ後に問題が表示されない  
→ ログを読み、DB 初期化コードが実行されていないことを特定  
→ app_context の位置を修正し自動投入を実装

### ● AI API のエラー  
→ モデル非推奨化が原因  
→ 新モデルへ移行し、例外処理を追加

### ● Blueprint の循環 import  
→ 構造を見直し、依存関係を整理

### ● UI の崩れ  
→ Bootstrap と独自 CSS を調整し改善

### ● API の悪用対策  
→ 1ユーザー1日100トークン制限を実装  
→ before_request で軽量にチェック

---

## ■ 注意事項
本アプリに収録されている問題・解説は現在も精査中です。  
Python3 エンジニア認定基礎試験の公式問題とは異なり、  
本試験の完全な再現を保証するものではありません。  
学習補助ツールとしてご利用ください。

---

## ■ デモURL
https://pyprep-ai-2-0.onrender.com/

---

## ■ 今後の改善予定
- 問題の追加
- ユーザーごとの弱点分析
- AI による自動問題生成
- スマホUIの最適化
- 管理ツールの機能拡張

👤 著者

鈴木 進

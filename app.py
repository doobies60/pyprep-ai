from forms import RegistrationForm, LoginForm
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash,
)
from summarize import generate_content
from models import db, Question, User, StudyLog  # ★追加：設計図と学習ログを呼ぶ
from utils import get_chapters_data, create_ai_prompt  # ★追加: 共通関数をインポート
from flask_migrate import Migrate  # ★★★ 追加: データベースマイグレーションツール

# --- Blueprints ---
from auth import auth_bp
from blueprints.admin import admin_bp
from blueprints.main import main_bp
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    current_user,
    login_required,
)
import google.generativeai as google_genai
from google.api_core import exceptions
from dotenv import load_dotenv
import os, datetime
import json
import random

app = Flask(__name__)

# ★追加: 環境変数を読み込み、AIのAPIキーを設定
load_dotenv()
google_genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# ★修正: ハードコードは避け、環境変数からSECRET_KEYを読み込むのが安全です
app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY", "a-secure-default-key-for-development-only"
)

login_manager = LoginManager()
login_manager.init_app(app)
# ログインしていない場合に飛ばす先を指定（関数名）
# ★修正: Blueprint名.関数名 に変更
login_manager.login_view = "auth.login"


@app.before_request
def before_request_handler():
    """毎リクエスト前に実行し、必要であればユーザーのAPIトークンをリセットする"""
    if current_user.is_authenticated:
        now_utc = datetime.datetime.utcnow()
        # この機能が追加される前の既存ユーザーのための初期化処理
        if (
            not hasattr(current_user, "last_token_reset")
            or current_user.last_token_reset is None
        ):
            current_user.last_token_reset = now_utc
            current_user.api_token_count = 100
            db.session.add(current_user)
            db.session.commit()
            return

        # 日付が変わっていたらトークンを100にリセット
        if current_user.last_token_reset.date() < now_utc.date():
            current_user.api_token_count = 100
            current_user.last_token_reset = now_utc
            db.session.add(current_user)
            db.session.commit()


# --- データベース設定（ここが心臓部） ---
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    base_dir, "python_exam_v2.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 2. ユーザーDB（追加分）
app.config["SQLALCHEMY_BINDS"] = {
    "users_db": "sqlite:///" + os.path.join(base_dir, "users.db")
}


@login_manager.user_loader
def load_user(user_id):
    # user_id は文字列として渡されることが多いので、int型に変えるのが安全
    # SQLAlchemyの「IDで1件取得する」メソッド（get）を使って、Userを返す
    return db.session.get(User, int(user_id))


db.init_app(app)  # ★追加：アプリとDBを紐付け
migrate = Migrate(app, db)  # ★★★ 追加: アプリとDBをマイグレーションツールに紐付け

# ★追加: Blueprintの登録
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)


# ★修正: テンプレート等が url_for('index') を呼んだ場合の互換性対応
@app.route("/legacy_index_redirect", endpoint="index")
def legacy_index_redirect():
    return redirect(url_for("main.index"))


# ★★★ 削除: Flask-Migrateで管理するため、自動作成は不要になる
# with app.app_context():
#     db.create_all()


# --- CLIコマンドの定義 ---
@app.cli.command("init-db")
def init_db_command():
    """データベーステーブルを作成し、初期データを投入します。"""
    with app.app_context():
        db.create_all()

        # questions.json からデータを読み込んで投入
        try:
            with open(
                os.path.join(base_dir, "questions.json"), "r", encoding="utf-8"
            ) as f:
                questions_data = json.load(f)

            # データが空の場合のみ追加（簡易的な重複防止）
            if Question.query.count() == 0:
                for q_data in questions_data:
                    # jsonのキーとモデルのフィールド名を合わせる必要があればここで調整
                    db.session.add(Question(**q_data))
                db.session.commit()
                print("データベースを初期化し、問題データを投入しました。")
            else:
                print("データベースは既に存在します。")
        except Exception as e:
            print(f"初期化中にエラーが発生しました: {e}")


@app.cli.command("create-test-user")
def create_test_user_command():
    """テスト用のユーザーを作成します。"""
    with app.app_context():
        if User.query.filter_by(username="testuser").first():
            print("ユーザー 'testuser' は既に存在します。")
            return
        new_user = User(username="testuser", email="test@example.com")
        new_user.set_password("password123")
        db.session.add(new_user)
        db.session.commit()
        print("テストユーザー 'testuser' を作成しました。")


# --- ★★★ 追加: DB問題オブジェクトを共通辞書形式に変換するヘルパー関数 ★★★ ---
def normalize_question(q_obj):
    """SQLAlchemyのQuestionオブジェクトをテンプレートで使える共通辞書形式に変換する"""
    if not q_obj:
        return None

    all_chapters = get_chapters_data()
    chapter_info = next(
        (c for c in all_chapters if c["id"] == str(q_obj.chapter)), None
    )
    chapter_name = chapter_info["title"] if chapter_info else f"Chapter {q_obj.chapter}"

    return {
        "id": q_obj.id,
        "question": q_obj.question,
        "options": [q_obj.choice_a, q_obj.choice_b, q_obj.choice_c, q_obj.choice_d],
        "answer": q_obj.answer.lower(),
        "explanation": q_obj.common_explanation,
        "is_ai": False,
        "chapter_name": chapter_name,
        "chapter": q_obj.chapter,
        "difficulty": q_obj.difficulty,
        "individual_explanations": [
            q_obj.explanation_a,
            q_obj.explanation_b,
            q_obj.explanation_c,
            q_obj.explanation_d,
        ],
    }


@app.route("/save_result", methods=["POST"])
@login_required  # ★ログイン必須にする
def save_result():
    # ★修正: フォームデータだけでなくJSONデータも受け取れるようにする
    data = request.form if request.form else request.get_json(silent=True) or {}

    q_id = data.get("question_id")
    u_ans = data.get("answer")
    is_correct_val = data.get("is_correct")
    is_correct = str(is_correct_val).lower() == "true" or is_correct_val is True
    chapter_id = data.get("chapter_id")

    # ★AI問題用の補完ロジック: IDから章を復元する
    if not chapter_id and q_id and str(q_id).startswith("ai_"):
        parts = str(q_id).split("_")
        # "ai_{chapter_id}_{random}" の形式を期待
        if len(parts) == 3:
            chapter_id = parts[1]

    # ★補完ロジック: chapter_idが送られてこなかった場合、DB問題なら補完する
    if not chapter_id and q_id and not str(q_id).startswith("ai_"):
        q = db.session.get(Question, int(q_id))
        if q:
            chapter_id = str(q.chapter)

    # ★ログインしているユーザーのIDを取得
    user_id = current_user.id

    # StudyLogに保存
    new_log = StudyLog(
        chapter_id=chapter_id,  # ★追加
        question_id=q_id,
        user_id=user_id,  # ★ユーザーIDを追加
        user_answer=u_ans,
        is_correct=is_correct,
    )
    db.session.add(new_log)
    db.session.commit()

    return jsonify({"status": "success"})


@app.route("/ai_quiz")
@login_required
def ai_quiz():
    # ★追加: トークンチェック
    if current_user.api_token_count <= 0:
        flash(
            "本日のAI機能の利用上限（100回）に達しました。明日またお試しください。",
            "warning",
        )
        return redirect(url_for("main.index"))

    # 1. どの章の問題を作るか決める（例：ランダムに1〜14章）
    chapter_num = random.randint(1, 14)

    # ★章情報からトピックを作成
    all_chapters = get_chapters_data()
    chapter_info = next((c for c in all_chapters if c["id"] == str(chapter_num)), None)
    topic = f"第{chapter_num}章"
    if chapter_info:
        topic = f"{chapter_info['title']} ({chapter_info['desc']})"

    prompt = create_ai_prompt(topic)
    # 2. AIから回答をもらう
    try:
        response_text = generate_content(prompt)
        # ★追加: 成功したらトークンを消費
        current_user.api_token_count -= 1
        db.session.add(current_user)
        db.session.commit()
    except Exception as e:
        print(f"AI API Error in ai_quiz: {e}")
        flash(
            "AIサーバーが応答しませんでした。時間をおいて再度お試しください。", "danger"
        )
        return redirect(url_for("main.index"))

    # 3. JSONを掃除して辞書に変換（既存のresultのロジックを流用）
    cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
    try:
        quiz_data = json.loads(cleaned_text)
        # 4. AI専用の画面（または共通の演習画面）を表示
        quiz_data["chapter_name"] = f"Chapter {chapter_num} (AI)"
        quiz_data["chapter"] = chapter_num  # テンプレートで章番号を使えるように追加
        quiz_data["is_ai"] = True
        return render_template("exercise.html", q=quiz_data)
    except:
        return redirect(url_for("main.index"))  # エラー時はTOPへ


# --- 間違えた問題一覧と再挑戦機能 ---
@app.route("/incorrect_questions")
@login_required
def incorrect_questions():
    # ログインユーザーの不正解ログを取得
    incorrect_logs = (
        StudyLog.query.filter_by(user_id=current_user.id, is_correct=False)
        .order_by(StudyLog.timestamp.desc())
        .all()
    )

    questions_to_display = []
    # ★追加：処理済みの問題ID（DB問題）または章ID（AI問題）を記録し、重複表示を防ぐ
    processed_keys = set()

    for log in incorrect_logs:
        # ★追加: IDが保存されていない不正なログはスキップ（エラー防止）
        if not log.question_id:
            continue

        if log.question_id.startswith("ai_"):
            # AI問題の場合、キーは「章ID」で重複をチェック
            key = f"ai_{log.chapter_id}"
            if key in processed_keys:
                continue  # この章のAI問題は既に追加済みなのでスキップ
            processed_keys.add(key)

            # chapter_idから元の章情報を取得
            chapter_info = next(
                (c for c in get_chapters_data() if c["id"] == str(log.chapter_id)),
                None,
            )
            chapter_title = (
                chapter_info["title"] if chapter_info else f"Chapter {log.chapter_id}"
            )

            questions_to_display.append(
                {
                    "type": "ai",
                    "log_id": log.id,
                    "question_id": log.question_id,
                    "chapter_id": log.chapter_id,
                    "chapter_title": chapter_title,
                    "user_answer": log.user_answer,
                    "timestamp": log.timestamp,
                    "display_text": f"AI生成問題 (章: {chapter_title})",
                    "re_attempt_url": url_for(
                        "ai_quiz_by_chapter", chapter_id=log.chapter_id
                    ),
                }
            )
        else:
            # DB問題の場合、キーは「問題ID」で重複をチェック
            key = log.question_id
            if not key or key in processed_keys:
                continue  # IDがないか、既に処理済みの場合はスキップ
            processed_keys.add(key)

            # ★追加: IDが数値に変換できない場合はスキップ
            try:
                q_id_int = int(log.question_id)
            except (ValueError, TypeError):
                continue

            db_question = db.session.get(Question, q_id_int)
            if db_question:
                questions_to_display.append(
                    {
                        "type": "db",
                        "log_id": log.id,
                        "question_id": db_question.id,
                        "question_text": db_question.question,
                        "user_answer": log.user_answer,
                        "correct_answer": db_question.answer,
                        "timestamp": log.timestamp,
                        "display_text": db_question.question,
                        "re_attempt_url": url_for(
                            "exercise_specific", question_id=db_question.id
                        ),
                    }
                )

    return render_template("incorrect_questions.html", questions=questions_to_display)


@app.route("/exercise/specific/<int:question_id>")
@login_required
def exercise_specific(question_id):
    question = db.session.get(Question, question_id)
    if not question:
        return redirect(url_for("main.index"))

    # ★修正: DB問題を共通形式の辞書に変換
    display_data = normalize_question(question)

    return render_template(
        "exercise.html",
        q=display_data,
        chapter_id=str(question.chapter),  # chapter_idを明示的に渡す
        current_level=None,
        current_difficulty=None,
    )


@app.route("/ai_quiz_by_chapter/<chapter_id>")
@login_required
def ai_quiz_by_chapter(chapter_id):
    # ★追加: トークンチェック
    if current_user.api_token_count <= 0:
        flash(
            "本日のAI機能の利用上限（100回）に達しました。明日またお試しください。",
            "warning",
        )
        return redirect(url_for("incorrect_questions"))

    all_chapters = get_chapters_data()
    chapter_info = next((c for c in all_chapters if c["id"] == chapter_id), None)

    if not chapter_info:
        flash("無効な章が指定されました。", "warning")
        return redirect(url_for("main.index"))  # 無効なchapter_idの場合

    topic = f"{chapter_info['title']} ({chapter_info['desc']})"
    prompt = create_ai_prompt(topic)

    try:
        response_text = generate_content(prompt)
        # ★追加: 成功したらトークンを消費
        current_user.api_token_count -= 1
        db.session.add(current_user)
        db.session.commit()
    except exceptions.ServerError as e:
        print(f"AI API Server Error: {e}")
        flash(
            "AIサーバーが現在大変混み合っています。しばらく時間をおいてから、再度お試しください。",
            "warning",
        )
        return redirect(url_for("incorrect_questions"))
    except Exception as e:
        print(f"AI問題の生成中に予期せぬエラーが発生しました: {e}")
        flash(
            "AI問題の生成中に予期せぬエラーが発生しました。しばらくしてからもう一度お試しください。",
            "danger",
        )
        return redirect(url_for("incorrect_questions"))

    cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
    try:
        quiz_data = json.loads(cleaned_text)
        quiz_data["id"] = (
            f"ai_{chapter_id}_{random.randint(1000, 9999)}"  # 新しいAI IDを割り当てる
        )
        quiz_data["chapter_name"] = f"{chapter_info['title']} (AI応用)"
        quiz_data["chapter"] = chapter_id  # chapter_idを明示的に渡す
        quiz_data["is_ai"] = True
        quiz_data["difficulty"] = "AI"
        quiz_data["individual_explanations"] = [
            quiz_data.get("explanation_a"),
            quiz_data.get("explanation_b"),
            quiz_data.get("explanation_c"),
            quiz_data.get("explanation_d"),
        ]
        return render_template("exercise.html", q=quiz_data, chapter_id=chapter_id)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"AI問題のJSONパースに失敗しました: {e}")
        flash(
            "AIが生成した問題の形式が正しくありませんでした。もう一度お試しください。",
            "danger",
        )
        return redirect(url_for("incorrect_questions"))


# --- 2. AI出題の結果を表示する役割 (ハイブリッド出題) ---
@app.route("/result", methods=["GET", "POST"])
@login_required
def result():
    if request.method == "POST":
        # ★追加: トークンチェック
        if current_user.api_token_count <= 0:
            flash(
                "本日のAI機能の利用上限（100回）に達しました。明日またお試しください。",
                "warning",
            )
            return redirect(url_for("main.index"))

        prompt = request.form.get("prompt")
        # AIから回答を取得
        response_text = generate_content(prompt)

        # ★追加: 成功したらトークンを消費
        current_user.api_token_count -= 1
        db.session.add(current_user)
        db.session.commit()

        # JSONを綺麗にする処理
        cleaned_text = response_text.replace("```json", "").replace("```", "").strip()

        try:
            # 文字列を辞書データに変換
            quiz_data = json.loads(cleaned_text)
            # 成功したら結果画面を表示
            return render_template("result.html", q=quiz_data)
        except Exception as e:
            # 失敗したらエラー内容を表示
            return f"エラーが発生しました: {e}<br>AIの回答: {response_text}"

    # POST（送信）以外でこのURLに来たらTOPへ追い返す
    return redirect(url_for("main.index"))


@app.route("/check_answer", methods=["POST"])
@login_required
def check_answer():
    # ★修正: フォームデータだけでなくJSONデータも受け取れるようにする
    data = request.form if request.form else request.get_json(silent=True) or {}

    q_id = data.get("question_id")
    u_ans = data.get("answer")  # ユーザーが選んだ a, b, c, d

    # AI問題などが誤ってここに来た場合のガード
    if not q_id or str(q_id).startswith("ai_"):
        return jsonify({"error": "Invalid question ID"}), 400

    question = db.session.get(Question, int(q_id)) if str(q_id).isdigit() else None
    if not question:
        return jsonify({"error": "Question not found"}), 404

    is_correct = u_ans == question.answer.lower()

    # DBに結果を保存
    chapter_id = data.get("chapter_id")
    if not chapter_id:
        chapter_id = str(question.chapter)

    log = StudyLog(
        question_id=q_id,
        user_answer=u_ans,
        is_correct=is_correct,
        user_id=current_user.id,
        chapter_id=chapter_id,
    )
    db.session.add(log)
    db.session.commit()

    # 判定結果をJSONで返す（画面をリロードせずに判定するため）
    return jsonify(
        {"is_correct": is_correct, "correct_answer": question.answer.upper()}
    )


@app.route("/hybrid_quiz")
@login_required
def hybrid_quiz():
    # ★追加: トークンチェック (AIモードになる可能性があるので先に行う)
    if current_user.api_token_count <= 0:
        flash(
            "本日のAI機能の利用上限（100回）に達しました。明日またお試しください。",
            "warning",
        )
        return redirect(url_for("main.index"))

    mode = random.choice(["db", "ai"])

    if mode == "db":
        q = Question.query.order_by(db.func.random()).first()
        # ★修正: 共通ヘルパー関数を使い、データ形式を完全に統一する
        display_data = normalize_question(q)
    else:
        # AIに作らせる（exerciseルートのロジックを参考に、章を特定して出題）
        chapter_num = random.randint(1, 14)
        all_chapters = get_chapters_data()
        chapter_info = next(
            (c for c in all_chapters if c["id"] == str(chapter_num)), None
        )
        topic = f"{chapter_info['title']} ({chapter_info['desc']})"
        prompt = create_ai_prompt(topic)
        try:
            response_text = generate_content(prompt)
            cleaned_text = (
                response_text.replace("```json", "").replace("```", "").strip()
            )
            # ★追加: 成功したらトークンを消費
            current_user.api_token_count -= 1
            db.session.add(current_user)
            db.session.commit()

            quiz_data = json.loads(cleaned_text)
            display_data = {
                "id": f"ai_{random.randint(1000, 9999)}",
                "question": quiz_data["question"],
                "options": quiz_data["options"],  # AIには最初からリストで返させる
                "answer": quiz_data["answer"].lower(),
                "explanation": quiz_data["explanation"],
                "is_ai": True,
                "chapter_name": f"{chapter_info['title']} (AI応用)",
                "chapter": chapter_num,
                "difficulty": "AI",  # ★追加
                "individual_explanations": [
                    quiz_data.get("explanation_a"),
                    quiz_data.get("explanation_b"),
                    quiz_data.get("explanation_c"),
                    quiz_data.get("explanation_d"),
                ],
            }
        except (json.JSONDecodeError, KeyError) as e:
            # AIの回答が壊れていた時の保険
            print(f"JSONパースエラー: {e}")
            return redirect(url_for("main.index"))

    return render_template("exercise.html", q=display_data)


@app.route("/exercise/<chapter_id>")
@login_required  # ★ログイン必須にする
def exercise(chapter_id):
    # --- ★★★ 模擬テスト（40問一括形式）の特別処理 ★★★ ---
    if chapter_id == "mock":
        # 40問をランダムに取得
        questions = Question.query.order_by(db.func.random()).limit(40).all()

        # 問題数が足りない場合のガード
        if len(questions) < 40:
            flash(
                "問題が40問に満たないため、模擬テストを開始できません。各章の問題を解いてください。",
                "warning",
            )
            return redirect(url_for("main.index"))

        # セッションに問題IDリストを保存して、採点時に利用
        session["mock_test_question_ids"] = [q.id for q in questions]

        # 模擬テスト専用のテンプレートをレンダリング
        return render_template("mock_test.html", questions=questions)

    current_id = request.args.get(
        "current_id"
    )  # AIのID('ai_xxxx')も考慮し、文字列で受け取る
    difficulty_code = request.args.get("difficulty")  # URLパラメータから難易度を取得

    # --- ★ハイブリッド出題ロジック (50%の確率でAI問題) ---
    # 模擬テストや、直前の問題がAI生成だった場合は、DBから問題を取得
    is_from_ai = str(current_id).startswith("ai_")
    is_mock_test = chapter_id == "mock"  # 模擬テストかどうかを判定
    use_ai = random.choices([True, False], weights=[0.5, 0.5], k=1)[0]

    if chapter_id != "mock" and not is_from_ai and use_ai:
        # ★追加: トークンチェック
        if current_user.api_token_count <= 0:
            # トークンがなくてもDB問題にフォールバックするので、ここではエラーにしない
            pass
        else:
            all_chapters = get_chapters_data()
            chapter_info = next(
                (c for c in all_chapters if c["id"] == chapter_id), None
            )

            if chapter_info:
                topic = f"{chapter_info['title']} ({chapter_info['desc']})"
                prompt = create_ai_prompt(topic)
                try:
                    response_text = generate_content(prompt)
                    cleaned_text = (
                        response_text.replace("```json", "").replace("```", "").strip()
                    )
                    # ★追加: 成功したらトークンを消費
                    current_user.api_token_count -= 1
                    db.session.add(current_user)
                    db.session.commit()

                    quiz_data = json.loads(cleaned_text)

                    # AI問題用のデータ形式を整える
                    display_data = {
                        "id": f"ai_{chapter_id}_{random.randint(1000, 9999)}",
                        "question": quiz_data["question"],
                        "options": quiz_data["options"],
                        "answer": quiz_data["answer"].lower(),
                        "explanation": quiz_data["explanation"],
                        "is_ai": True,
                        "chapter_name": f"{chapter_info['title']} (AI応用)",
                        "chapter": chapter_id,  # AI問題にも章番号を付与
                        "difficulty": "AI",
                        # 個別解説がない場合も考慮
                        "individual_explanations": [
                            quiz_data.get("explanation_a"),
                            quiz_data.get("explanation_b"),
                            quiz_data.get("explanation_c"),
                            quiz_data.get("explanation_d"),
                        ],
                    }
                    return render_template(
                        "exercise.html",
                        q=display_data,
                        chapter_id=chapter_id,
                        current_level=None,
                        current_difficulty=difficulty_code,
                        is_mock=is_mock_test,  # 模擬テストフラグを渡す
                    )
                except (json.JSONDecodeError, KeyError) as e:
                    print(
                        f"AI問題の生成に失敗しました: {e}。DB問題にフォールバックします。"
                    )
                    # AI生成失敗時は、そのままDB問題の取得処理に進む

    # --- 以下、DBから問題を取得する従来のロジック ---
    try:
        query = Question.query.filter_by(chapter=int(chapter_id))
    except ValueError:
        return redirect(url_for("main.index"))

    if difficulty_code:
        diff_map = {"beginner": "初級", "intermediate": "中級", "advanced": "上級"}
        target_diff = diff_map.get(difficulty_code)
        if target_diff:
            query = query.filter(Question.difficulty == target_diff)

    # DB問題の場合、IDは数値なので、数値の場合のみフィルタリング
    if current_id and str(current_id).isdigit():
        query = query.filter(Question.id != int(current_id))

    question = query.order_by(db.func.random()).first()

    if not question:
        return redirect(url_for("main.index"))

    # ★修正: DB問題を共通形式の辞書に変換
    display_data = normalize_question(question)

    return render_template(
        "exercise.html",
        q=display_data,
        chapter_id=chapter_id,
        current_level=None,  # 章別のときはNoneでOK
        current_difficulty=difficulty_code,  # テンプレートで維持するために渡す
        is_mock=is_mock_test,  # 模擬テストフラグを渡す
    )


@app.route("/level_exercise/<int:level>")
@login_required
def level_exercise(level):
    current_id = request.args.get("current_id")  # AIのIDも考慮して文字列で受け取る

    # --- ★ハイブリッド出題ロジック (50%の確率でAI問題) ---
    is_from_ai = str(current_id).startswith("ai_")
    use_ai = random.choices([True, False], weights=[0.5, 0.5], k=1)[0]

    if not is_from_ai and use_ai:
        # ★追加: トークンチェック
        if current_user.api_token_count <= 0:
            # トークンがなくてもDB問題にフォールバックするので、ここではエラーにしない
            pass
        else:
            all_chapters = get_chapters_data()
            # そのレベルに対応する章をリストアップ
            level_chapters = [
                c for c in all_chapters if c.get("level") == level and c["id"].isdigit()
            ]

            if level_chapters:
                chapter_info = random.choice(level_chapters)
                chapter_id_for_ai = chapter_info["id"]
                topic = f"{chapter_info['title']} ({chapter_info['desc']})"
                prompt = create_ai_prompt(topic)

                try:
                    response_text = generate_content(prompt)
                    cleaned_text = (
                        response_text.replace("```json", "").replace("```", "").strip()
                    )
                    # ★追加: 成功したらトークンを消費
                    current_user.api_token_count -= 1
                    db.session.add(current_user)
                    db.session.commit()

                    quiz_data = json.loads(cleaned_text)

                    display_data = {
                        "id": f"ai_{random.randint(1000, 9999)}",
                        "question": quiz_data["question"],
                        "options": quiz_data["options"],
                        "answer": quiz_data["answer"].lower(),
                        "explanation": quiz_data["explanation"],
                        "is_ai": True,
                        "chapter_name": f"{chapter_info['title']} (AI応用)",
                        "chapter": chapter_id_for_ai,
                        "difficulty": "AI",
                        "individual_explanations": [
                            quiz_data.get("explanation_a"),
                            quiz_data.get("explanation_b"),
                            quiz_data.get("explanation_c"),
                            quiz_data.get("explanation_d"),
                        ],
                    }
                    return render_template(
                        "exercise.html",
                        q=display_data,
                        chapter_id=f"level_{level}",
                        current_level=level,
                    )
                except (json.JSONDecodeError, KeyError) as e:
                    print(
                        f"AI問題の生成に失敗しました: {e}。DB問題にフォールバックします。"
                    )

    # --- 以下、DBから問題を取得するロジック (exerciseルートと統一) ---
    level_map = {1: "初級", 2: "中級", 3: "上級"}
    target_difficulty = level_map.get(level, "初級")

    query = Question.query.filter(Question.difficulty.contains(target_difficulty))

    if current_id and str(current_id).isdigit():
        query = query.filter(Question.id != int(current_id))

    question = query.order_by(db.func.random()).first()

    if not question:
        return redirect(url_for("main.index"))

    # ★修正: DB問題を共通形式の辞書に変換
    display_data = normalize_question(question)

    return render_template(
        "exercise.html",
        q=display_data,
        chapter_id=f"level_{level}",
        current_level=level,
    )


# 模擬テスト用のルート（例）
@app.route("/mock_exam")
@login_required
def mock_exam():
    current_id = request.args.get("current_id", type=int)

    # 1. DBから全問題を一気に持ってくる
    all_questions = Question.query.all()

    # 2. もし問題が1件もなければトップへ
    if not all_questions:
        return redirect(url_for("main.index"))

    # 3. 【重要】「今の問題以外」から選ぶ（連チャン防止）
    selectable_questions = [q for q in all_questions if q.id != current_id]

    # 候補が空っぽ（全1件しかない場合など）なら全リストから選ぶ
    if not selectable_questions:
        selectable_questions = all_questions

    # 4. その中からランダムに1問だけ選ぶ
    # （40問形式の「雰囲気」を出すため、URLは固定で中身だけ変える設計）
    question = random.choice(selectable_questions)
    # ★修正: DB問題を共通形式の辞書に変換
    display_data = normalize_question(question)

    return render_template(
        "exercise.html",
        q=display_data,
        chapter_id="mock",  # 次の問題ボタン用
        is_mock=True,  # 🏆 タイトル表示用
    )


@app.route("/submit_mock_test", methods=["POST"])
@login_required
def submit_mock_test():
    """最終模擬テストの結果を受け取り、採点して結果を表示する"""
    question_ids = session.get("mock_test_question_ids")
    if not question_ids:
        flash(
            "テストセッションの有効期限が切れました。もう一度テストを開始してください。",
            "warning",
        )
        return redirect(url_for("main.index"))

    user_answers_from_form = request.form

    # DBからセッションに保存したIDの問題をまとめて取得
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    # IDをキーにした辞書に変換して、高速にアクセスできるようにする
    question_map = {q.id: q for q in questions}

    results_for_template = []
    correct_count = 0

    # セッションに保存したIDの順序を維持してループ処理
    for q_id in question_ids:
        question = question_map.get(q_id)
        if not question:
            continue

        # フォームから送られてきたユーザーの解答を取得
        user_answer_choice = user_answers_from_form.get(
            f"question_{q_id}"
        )  # 例: 'a', 'b', 'c', 'd'
        is_correct = user_answer_choice == question.answer.lower()

        if is_correct:
            correct_count += 1

        # 学習ログをDBに保存
        log = StudyLog(
            question_id=str(q_id),
            user_answer=user_answer_choice,
            is_correct=is_correct,
            user_id=current_user.id,
            chapter_id=str(question.chapter),  # 'mock'ではなく、元の章IDを保存
        )
        db.session.add(log)

        # 結果表示テンプレートに渡すためのデータを整形
        options_map = {
            "a": question.choice_a,
            "b": question.choice_b,
            "c": question.choice_c,
            "d": question.choice_d,
        }
        user_answer_text = options_map.get(user_answer_choice, "未解答")

        results_for_template.append(
            {
                "question": question,
                "user_answer_choice": user_answer_choice,
                "user_answer_text": user_answer_text,
                "is_correct": is_correct,
            }
        )

    # DBへの変更を確定
    db.session.commit()
    # 使用済みのセッション情報を削除
    session.pop("mock_test_question_ids", None)

    total_questions = len(question_ids)
    score = (correct_count / total_questions) * 100 if total_questions > 0 else 0

    return render_template(
        "mock_test_result.html",
        results=results_for_template,
        total_questions=total_questions,
        correct_count=correct_count,
        score=score,
    )


@app.route("/get_ai_explanation", methods=["POST"])
@login_required
def get_ai_explanation():
    """
    問題データを受け取り、AIによる深掘り解説を生成して返すAPI。
    """
    try:
        data = request.get_json()
        # ★追加: トークンチェック
        if current_user.api_token_count <= 0:
            return (
                jsonify({"error": "本日のAI機能の利用上限に達しました。"}),
                429,
            )  # Too Many Requests

        if not data:
            return jsonify({"error": "リクエストが無効です。"}), 400

        question = data.get("question", "")
        options = data.get("options", [])
        answer = data.get("answer", "")
        explanation = data.get("explanation", "")

        options_text = "\n".join(
            [f"{chr(97+i)}. {opt}" for i, opt in enumerate(options)]
        )

        prompt = f"""
あなたは経験豊富なPython講師です。
以下のPython基礎問題と、その公式解説があります。

この問題について、学習者がさらに深い理解を得られるような「深掘り解説」を生成してください。

【重要】
- 全体として、**300〜400字程度の簡潔な解説**にまとめてください。
- マークダウン形式（特にコードブロック ```python ... ```）を積極的に使用し、読みやすく整形してください。
- **特に「対話モードでの挙動」や「コードの実行結果」に関する説明では、必ず具体的なコード例（REPLの入出力イメージなど）を提示してください。**
- なぜ正解が正解なのか、その根拠をより詳しく説明してください。
- なぜ他の選択肢が間違いなのか、具体的な理由や初心者が陥りやすい誤解を指摘してください。
- 問題のトピックに関連する追加知識、発展的な内容、または実務での応用例などを盛り込んでください。
- **解説に出てくる専門用語（例: イミュータブル, スコープ, コマンド,etc.）には、必ず簡単な注釈（用語説明）を付けてください。**
- 問題のトピックに関連する追加知識、発展的な内容、または実務での応用例などを盛り込んでください。
- 全体として、丁寧で分かりやすい言葉遣いを心がけてください。

---
### 対象の問題

**問題文:**
{question}

**選択肢:**
{options_text}

**正解:**
{answer.upper()}

**公式解説:**
{explanation}
---

それでは、上記の指示に従って「深掘り解説」を生成してください。
"""
        # ★修正: モデル名を最新のものに更新し、安定性を向上 (2026年時点の推奨モデルへ)
        model = google_genai.GenerativeModel('models/gemini-1.5-flash')
        response = model.generate_content(prompt)

        if not response.parts:
            return jsonify({"error": "AIが回答を生成できませんでした。"}), 500

        # ★追加: 成功したらトークンを消費
        current_user.api_token_count -= 1
        db.session.add(current_user)
        db.session.commit()

        return jsonify({"explanation": response.text})
    except exceptions.ServerError as e:
        print(f"AI API Server Error: {e}")
        return (
            jsonify(
                {
                    "error": "AIサーバーが現在大変混み合っています。しばらく時間をおいてから、再度お試しください。"
                }
            ),
            503,
        )
    except Exception as e:
        print(f"AI解説の生成中に予期せぬエラーが発生しました: {e}")
        return (
            jsonify(
                {
                    "error": "AI解説の生成中に予期せぬエラーが発生しました。しばらくしてからもう一度お試しください。"
                }
            ),
            500,
        )


if __name__ == "__main__":
    # use_reloader=False を追加して、自動再起動をオフにする
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)

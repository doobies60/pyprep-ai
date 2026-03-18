from flask import Blueprint, render_template, session, url_for, redirect
from flask_login import current_user, login_required
from models import db, Question, User, StudyLog
from utils import get_chapters_data

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    chapters = get_chapters_data()
    progress_data = {}  # 先に初期化

    # --- ★進捗状況の計算ロジックを追加 ---
    if current_user.is_authenticated:
        # 1. ログインユーザーの学習ログを全て取得
        logs = StudyLog.query.filter_by(user_id=current_user.id).all()

        # 2. 章ごとの正解数・問題数を集計する辞書
        for log in logs:
            # 'level_1' のようなレベル別演習のログは章別集計から除外
            if log.chapter_id and not log.chapter_id.startswith("level"):
                # 集計辞書を初期化
                if log.chapter_id not in progress_data:
                    progress_data[log.chapter_id] = {"correct": 0, "total": 0}
                # カウントアップ
                progress_data[log.chapter_id]["total"] += 1
                if log.is_correct:
                    progress_data[log.chapter_id]["correct"] += 1

    # 3. 集計結果を chapters データにマージする
    for chapter in chapters:
        stats = progress_data.get(chapter["id"])
        chapter["is_completed"] = False  # まずFalseで初期化
        chapter["progress_percent"] = 0  # まず0で初期化
        if stats and stats["total"] > 0:
            chapter["progress_percent"] = int((stats["correct"] / stats["total"]) * 100)
            if chapter["progress_percent"] >= 80 and stats["total"] >= 5:
                chapter["is_completed"] = True

    # 各章に利用可能な難易度をDBから取得して追加する
    # これにより、テンプレート側で難易度別のリンクを動的に生成できる
    diff_map_jp_to_en = {"初級": "beginner", "中級": "intermediate", "上級": "advanced"}
    for chapter in chapters:
        # 'mock' のような数値でないIDはスキップ
        if chapter["id"].isdigit():
            # その章に存在する難易度をDBから重複なく取得
            difficulties_in_db = (
                db.session.query(Question.difficulty)
                .filter_by(chapter=int(chapter["id"]))
                .distinct()
                .all()
            )
            # 結果はタプルのリスト [(初級,), (中級,)] なので、文字列のリストに変換
            available_difficulties_jp = [d[0] for d in difficulties_in_db if d[0]]

            # テンプレートで使いやすいように、日本語名と英語コードの辞書のリストを作成
            chapter["available_difficulties"] = [
                {"name_jp": d_jp, "code": diff_map_jp_to_en.get(d_jp)}
                for d_jp in available_difficulties_jp
                if diff_map_jp_to_en.get(d_jp)
            ]

    username = session.get("username")
    return render_template("index.html", chapters=chapters, username=username)


@main_bp.route("/profile")
@login_required
def profile():
    """ユーザーの成績や進捗を表示するプロフィールページ"""
    # 1. ユーザーの基本情報を取得
    user = current_user

    # 2. 学習ログを取得 (★ご要望に基づき、未解答の問題は統計から除外)
    logs = (
        StudyLog.query.filter(
            StudyLog.user_id == user.id, StudyLog.user_answer.isnot(None)
        )
        .order_by(StudyLog.timestamp.desc())
        .all()
    )

    if not logs:
        # 学習履歴がない場合の表示
        return render_template("profile.html", user=user, stats=None)

    # 3. 成績サマリーを計算
    total_attempts = len(logs)
    correct_count = sum(1 for log in logs if log.is_correct)
    accuracy = (correct_count / total_attempts) * 100 if total_attempts > 0 else 0

    # 4. 章ごとの進捗を計算 (indexルートのロジックを参考に集計)
    progress_data = {}
    for log in logs:
        # 'level_x' や 'mock' のような特殊なIDは集計から除外する場合
        if log.chapter_id and log.chapter_id.isdigit():
            if log.chapter_id not in progress_data:
                progress_data[log.chapter_id] = {"correct": 0, "total": 0}
            progress_data[log.chapter_id]["total"] += 1
            if log.is_correct:
                progress_data[log.chapter_id]["correct"] += 1

    # 5. テンプレートで使いやすいように整形
    chapters_data = get_chapters_data()
    chapter_map = {c["id"]: c for c in chapters_data}

    chapter_stats = []
    for chapter_id, data in progress_data.items():
        percent = (data["correct"] / data["total"]) * 100
        chapter_info = chapter_map.get(chapter_id)
        if chapter_info:
            chapter_stats.append(
                {
                    "id": chapter_id,
                    "title": chapter_info["title"],
                    "total": data["total"],
                    "correct": data["correct"],
                    "percent": percent,
                }
            )

    # 正解率が100%未満のものを苦手な章とする
    weak_chapters = sorted(
        [s for s in chapter_stats if s["percent"] < 100], key=lambda x: x["percent"]
    )

    stats = {
        "total_attempts": total_attempts,
        "correct_count": correct_count,
        "accuracy": accuracy,
        "chapter_stats": sorted(chapter_stats, key=lambda x: int(x["id"])),  # 章番号でソート
        "weak_chapters": weak_chapters[:3],  # 苦手な章を上位3つ表示
    }

    return render_template("profile.html", user=user, stats=stats)
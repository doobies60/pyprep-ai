from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User, StudyLog
from collections import defaultdict

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/stats")
@login_required
def stats():
    """全ユーザーの統計情報を表示する管理者専用ページ"""
    # 管理者ユーザー（例: 'admin'）以外はアクセスを拒否
    if current_user.username != "admin":
        flash("管理者専用ページです。", "warning")
        return redirect(url_for("main.index"))

    # 全ユーザーと全学習ログを取得
    all_users = User.query.all()
    all_logs = StudyLog.query.filter(StudyLog.user_answer.isnot(None)).all()

    if not all_logs:
        return render_template("admin_stats.html", stats=None, title="管理者ダッシュボード")

    # --- 全体の統計 ---
    total_attempts = len(all_logs)
    total_correct = sum(1 for log in all_logs if log.is_correct)
    overall_accuracy = (
        (total_correct / total_attempts) * 100 if total_attempts > 0 else 0
    )

    # --- ユーザーごとの統計 ---
    user_stats = []
    user_map = {user.id: user.username for user in all_users}

    # ユーザーIDでログをグループ化
    logs_by_user = defaultdict(list)
    for log in all_logs:
        logs_by_user[log.user_id].append(log)

    for user_id, logs in logs_by_user.items():
        user_total = len(logs)
        user_correct = sum(1 for log in logs if log.is_correct)
        user_accuracy = (user_correct / user_total) * 100 if user_total > 0 else 0
        user_stats.append(
            {
                "username": user_map.get(user_id, f"不明なユーザー (ID:{user_id})"),
                "total": user_total,
                "correct": user_correct,
                "accuracy": user_accuracy,
            }
        )

    # 正解率が高い順にソート
    user_stats = sorted(user_stats, key=lambda x: x["accuracy"], reverse=True)

    stats = {
        "total_users": len(all_users),
        "total_attempts": total_attempts,
        "total_correct": total_correct,
        "overall_accuracy": overall_accuracy,
        "user_stats": user_stats,
    }

    return render_template("admin_stats.html", stats=stats, title="管理者ダッシュボード")
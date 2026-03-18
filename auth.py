from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from forms import LoginForm, RegistrationForm

# Blueprintの定義
auth_bp = Blueprint("auth", __name__)


# --- 1. ログイン機能 ---
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # 1. ログイン用のフォームを呼び出す
    form = LoginForm()

    # 2. 送信ボタンが押され、入力ルール（空欄でないか等）をクリアしたら
    if form.validate_on_submit():
        # フォームからデータを取り出す
        username = form.username.data
        password = form.password.data
        remember = form.remember_me.data

        # データベースからユーザーを探す
        user = User.query.filter_by(username=username).first()

        # ユーザーが存在し、かつパスワードが正しいかチェック
        if user and user.check_password(password):
            login_user(user, remember=remember)  # ログイン実行
            print(f"ログイン成功：{username}")
            
            # ★修正: ログイン後に、元々アクセスしようとしていたページにリダイレクトする
            next_page = request.args.get('next')
            # セキュリティのため、next_pageがサイト内のパスかチェック
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            # 失敗した場合はエラーメッセージを表示
            print("ログイン失敗：ユーザー名かパスワードが違います")
            return render_template(
                "login.html",
                form=form,
                error="ユーザー名またはパスワードが正しくありません",
            )

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    print("ログアウトしました")
    return redirect(url_for("main.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        print(f"新規ユーザー登録成功: {new_user.username}")
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)

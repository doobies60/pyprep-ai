from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Question(db.Model):
    """既存の python_exam_v2.db の構造に完全に合わせたクラス"""

    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    chapter = db.Column(db.Integer)
    difficulty = db.Column(db.Text)  # 初級・中級などの文字列
    question = db.Column(db.Text)  # 問題文
    choice_a = db.Column(db.Text)
    choice_b = db.Column(db.Text)
    choice_c = db.Column(db.Text)
    choice_d = db.Column(db.Text)
    answer = db.Column(db.String(1))  # 'a', 'b' など

    # 各選択肢の個別解説
    explanation_a = db.Column(db.Text)
    explanation_b = db.Column(db.Text)
    explanation_c = db.Column(db.Text)
    explanation_d = db.Column(db.Text)

    # 全体共通の解説
    common_explanation = db.Column(db.Text)

    # --- テンプレート互換用のプロパティを追加 ---
    @property
    def options(self):
        """選択肢をリスト形式で返す"""
        return [self.choice_a, self.choice_b, self.choice_c, self.choice_d]

    @property
    def explanation(self):
        """共通解説へのエイリアス"""
        return self.common_explanation

    @property
    def is_ai(self):
        """DB問題なので常にFalse"""
        return False

    @property
    def individual_explanations(self):
        """個別解説をリスト形式で返す"""
        return [
            self.explanation_a,
            self.explanation_b,
            self.explanation_c,
            self.explanation_d,
        ]


class User(db.Model, UserMixin):
    """ユーザー情報"""

    __bind_key__ = "users_db"
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    goal = db.Column(db.Text)
    api_token_count = db.Column(db.Integer, nullable=False, default=100)
    last_token_reset = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class StudyLog(db.Model):
    """成績を保存するテーブル"""

    __bind_key__ = "users_db"
    __tablename__ = "study_logs"
    id = db.Column(db.Integer, primary_key=True)

    # 外部キー: どの問題か
    question_id = db.Column(
        db.String(50)
    )  # AI問題のID(ai_1234)も保存できるようにString型を推奨

    # ★追加: どのユーザーか
    user_id = db.Column(
        db.Integer
    )  # シンプルにするためForeignKeyは張らずに数値のみ保存
    # ★追加: どの章/レベルの問題か (例: '3', 'mock', 'level_1')
    # exerciseルートから渡される chapter_id を保存する
    chapter_id = db.Column(db.String(50))

    user_answer = db.Column(db.String(1))
    is_correct = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, default=db.func.now())

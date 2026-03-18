from flask_wtf import FlaskForm
from models import User
from flask_login import current_user
from wtforms import StringField,PasswordField, SubmitField,BooleanField, IntegerField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, Length,EqualTo
from wtforms.validators import ValidationError

class RegistrationForm(FlaskForm):
    # フィールド（入力項目）の定義
    username = StringField('ユーザー名', validators=[DataRequired()])
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    confirm_password = PasswordField('パスワード確認', validators=[DataRequired(), EqualTo('password')])
    
    # ボタン
    submit = SubmitField('新規登録')
    
    # ユーザー名の重複チェック
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('そのユーザー名は既に使用されています。')

    # メールの重複チェック
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('そのメールアドレスは既に使用されています。')
        
class LoginForm(FlaskForm):
    # ログインに必要なのは「名前」と「パスワード」だけ
    username = StringField('ユーザー名', validators=[DataRequired(message="ユーザー名を入力してください")])
    password = PasswordField('パスワード', validators=[DataRequired(message="パスワードを入力してください")])
    
    # 「ログイン状態を保持する」チェックボックス（任意ですが便利です）
    remember_me = BooleanField('ログイン状態を保存する')
    
    submit = SubmitField('ログイン')
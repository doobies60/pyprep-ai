import streamlit as st
import sqlite3
import random
import pandas as pd
import os

# --- 設定 ---
DB_PATH = 'python_exam_v2.db'

st.set_page_config(page_title="Python基礎試験 攻略アプリ", layout="wide")

# データベースから全問題を読み込む関数
@st.cache_data # 毎回DBを読み込まないようにキャッシュ化
def load_all_questions():
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# データの初期化
all_questions = load_all_questions()

# --- メイン処理 ---
if not all_questions:
    st.error(f"❌ DBファイル `{DB_PATH}` が見つからないか、データが空です。")
    st.info("update_db.py を実行してデータを登録してください。")
    st.stop()

# --- サイドバーナビゲーション ---
st.sidebar.title("🎮 メニュー")
mode = st.sidebar.radio("モード選択", ["ダッシュボード", "模擬試験モード", "データベース閲覧"])

# --- 1. ダッシュボード ---
if mode == "ダッシュボード":
    st.title("📊 学習ダッシュボード")
    df = pd.DataFrame(all_questions)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("総問題数", f"{len(df)} 問")
    col2.metric("カバーしている章", f"{df['chapter'].nunique()} 章")
    col3.metric("ステータス", "120問 準備完了！")

    st.write("### 📖 章ごとの問題数分布")
    # 章ごとのカウントを計算して棒グラフを表示
    chapter_counts = df['chapter'].value_counts().sort_index()
    st.bar_chart(chapter_counts)
    
    st.write("### 📈 難易度別の割合")
    diff_counts = df['difficulty'].value_counts()
    st.area_chart(diff_counts)

# --- 2. 模擬試験モード ---
elif mode == "模擬試験モード":
    st.title("📝 模擬試験（40問）")
    
    if 'exam_questions' not in st.session_state:
        st.write("120問の中から、本番と同じ40問をランダムに出題します。")
        if st.button("試験を開始する"):
            st.session_state.exam_questions = random.sample(all_questions, 40)
            st.session_state.user_answers = {}
            st.rerun()
    else:
        # 試験フォーム
        with st.form("exam_form"):
            for i, q in enumerate(st.session_state.exam_questions):
                st.markdown(f"#### 第 {i+1} 問 (第{q['chapter']}章)")
                st.write(q['question'])
                
                # 選択肢の表示
                opts = ['A', 'B', 'C', 'D']
                labels = [f"A: {q['choice_a']}", f"B: {q['choice_b']}", f"C: {q['choice_c']}", f"D: {q['choice_d']}"]
                
                user_choice = st.radio(
                    f"回答を選んでください (ID:{q['id']})",
                    opts,
                    format_func=lambda x: next(l for l in labels if l.startswith(x)),
                    key=f"q_{q['id']}"
                )
                st.session_state.user_answers[q['id']] = user_choice
                st.divider()
            
            submitted = st.form_submit_button("採点する")
            
        if submitted:
            st.header("🏁 結果発表")
            score = 0
            detail_results = []
            
            for q in st.session_state.exam_questions:
                ans = st.session_state.user_answers[q['id']]
                correct = q['answer']
                is_correct = (ans == correct)
                if is_correct: score += 1
                
                detail_results.append({
                    "No": len(detail_results)+1,
                    "結果": "✅" if is_correct else "❌",
                    "あなたの回答": ans,
                    "正解": correct,
                    "問題内容": q['question'][:30] + "..."
                })
            
            # スコア表示
            percent = (score / 40) * 100
            if percent >= 70:
                st.balloons()
                st.success(f"合格圏内です！ スコア: {score}/40 ({percent}%)")
            else:
                st.warning(f"あともう少し！ スコア: {score}/40 ({percent}%)")
            
            st.table(pd.DataFrame(detail_results))
            
            if st.button("もう一度受ける"):
                del st.session_state.exam_questions
                st.rerun()

# --- 3. データベース閲覧 ---
else:
    st.title("📚 全問題データベース")
    st.write("登録されているすべての問題を一覧・検索できます。")
    df = pd.DataFrame(all_questions)
    st.dataframe(df)
    import streamlit as st
import datetime
import google.generativeai as genai
import pandas as pd
import random
from PIL import Image
from datetime import timedelta, timezone

# --- 日本時間(JST)を取得 ---
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.datetime.now(JST)
today = now.date()

# --- ページ設定 ---
st.set_page_config(page_title="limit my life (Demo)", layout="centered")

# --- 1. システム設定（サイドバー） ---
st.sidebar.title("System Settings (Demo)")
st.sidebar.info("※このデモ版ではGoogleスプレッドシートへの保存は行われません。")
limit_age = st.sidebar.number_input("End Age (寿命の目安)", value=80, min_value=1)

# APIキーを読者が入力できるようにします
api_key = st.sidebar.text_input("ご自身の Gemini API Key を入力してください", type="password", help="Google AI Studioで無料で発行できます")

# --- デザイン設定 ---
st.sidebar.markdown("---")
st.sidebar.subheader("🎨 Design Custom")
bg_color = st.sidebar.color_picker("背景色", "#E0F7FA") 
text_color = st.sidebar.color_picker("文字色", "#000000")

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    .stTextArea textarea, .stTextInput input {{ background-color: #ffffff !important; color: #000000 !important; }}
    .stMarkdown, p, h1, h2, h3, h4, span, label {{ color: {text_color} !important; }}
    </style>
    """,
    unsafe_allow_html=True
)

if api_key:
    try:
        genai.configure(api_key=api_key)
        st.sidebar.success("API Connected")
    except Exception as e:
        st.sidebar.error(f"API Error: {e}")

st.sidebar.markdown("---")

# --- 2. 軸と「やってしまったこと」の設定 ---
jiku_30 = ["健康", "挑戦", "勇気", "誠実", "自律", "貢献", "美意識", "直感", "知的好奇心", "冒険", "調和", "感謝", "遊び心", "覚悟", "柔軟性", "情熱", "謙虚", "忍耐", "共感", "創造性", "スピード", "余白", "ユーモア", "規律", "洗練", "俯瞰", "集中", "信頼", "純粋", "大胆"]
selected_axes = st.sidebar.multiselect("今月の3軸", jiku_30, default=["健康", "挑戦", "感謝"], max_selections=3)

st.sidebar.subheader("🚫 本日の「やってしまったこと」")
not_to_do_list = ["無駄なSNS", "夜更かし", "過度な飲酒", "サボり", "二度寝", "感情的な反応", "色欲", "言い訳", "嘘をつく", "批判"]
done_bad_habits = []
for habit in not_to_do_list:
    if st.sidebar.checkbox(habit, key=habit):
        done_bad_habits.append(habit)

st.sidebar.markdown("---")
companion_type = st.sidebar.radio("あなたの伴走者", ("子供（純粋）", "老人（経験）", "賢者（真理）"))

# --- 3. メイン表示 ---
st.title(f"limit my life : {limit_age}")
tab1, tab2, tab3 = st.tabs(["今日の内省", "振り返りカレンダー", "全データ"])

with tab1:
    st.markdown(f"### {today.year}年 {today.month}月 {today.day}日")
    
    progress_dots = int(((now.hour + now.minute / 60) / 24) * 12)
    dots_display = " ".join(["●" if i < progress_dots else "○" for i in range(12)])
    st.markdown(f"## {dots_display}")

    spacer = "&nbsp;" * 16
    st.markdown(f"{spacer}🌅{spacer}☀️{spacer}🌆{spacer}🌙", unsafe_allow_html=True)
    st.divider()
    
    # デモ版では目標は空欄または固定
    monthly_goal = st.text_input("今月の目標", value="AIを使いこなし、人生の軸を深化させる", placeholder="この一ヶ月で到達したい姿を書いてください")
    
    reflection_text = st.text_area("今の正直な気持ちを、自分の軸に照らして言葉にしてみよう", height=150)
    uploaded_file = st.file_uploader("今日の1枚を登録する（任意）", type=["jpg", "jpeg", "png"])
    img = None
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)

    if st.button("伴走者と対話する（デモ体験）"):
        if not api_key:
            st.error("サイドバーにご自身のGemini APIキーを入力してください。")
        elif not reflection_text:
            st.warning("内省内容を入力してください。")
        else:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                is_devil_mode = len(done_bad_habits) >= 2
                
                persona_prompts = {
                    "子供（純粋）": "好奇心旺盛で純粋な子供です。色や形に反応し、遊び心を忘れない言葉をかけて。",
                    "老人（経験）": "慈愛深い老人です。時の流れや無常を感じ取り、自己受容を促す穏やかな言葉をかけて。",
                    "賢者（真理）": "本質を突く賢者です。秩序を読み解き、内省につながる静かな問いを投げかけて。"
                }
                
                base_prompt = f"あなたは{persona_prompts[companion_type]}\n今の視点: {selected_axes}\n今日やってしまったこと: {done_bad_habits}\n日記: 「{reflection_text}」"
                
                if is_devil_mode:
                    full_prompt = base_prompt + "\n重要：ユーザーは悪い習慣を2つ以上行いました。前半は伴走者として厳しく叱責し、後半は『悪魔』が登場して甘く誘惑する二段構えで答えて。"
                elif img:
                    full_prompt = base_prompt + "\n写真の情景を交えつつ、1〜2文で勇気づけ気味に答えて。"
                else:
                    full_prompt = base_prompt + "\n1〜2文で心に届く前向きな対話をして。"

                content = [full_prompt, img] if img else [full_prompt]
                response = model.generate_content(content)
                
                st.markdown(f"### 【{companion_type}からの言葉】")
                if is_devil_mode:
                    st.error(response.text)
                else:
                    st.info(response.text)

                # --- 保存のシミュレーション ---
                st.balloons()
                st.success("【デモ体験完了】本番版では、ここで内容がスプレッドシートに保存されます！")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

with tab2:
    st.subheader("内省カレンダー（表示見本）")
    # デモ用のダミーカレンダー
    import calendar
    yy, mm = today.year, today.month
    st.write(f"### {yy}年 {mm}月")
    month_days = calendar.monthcalendar(yy, mm)
    
    html_cal = "<style>.cal-table { width: 100%; border-collapse: collapse; table-layout: fixed; } .cal-table th, .cal-table td { text-align: center; padding: 5px 0; border: 1px solid #ddd; font-size: 14px; } .check { color: #2ecc71; font-weight: bold; } .today { background-color: #e0f7fa; }</style><table class='cal-table'><tr><th>月</th><th>火</th><th>水</th><th>木</th><th>金</th><th style='color:blue;'>土</th><th style='color:red;'>日</th></tr>"
    for week in month_days:
        html_cal += "<tr>"
        for i, day in enumerate(week):
            if day == 0:
                html_cal += "<td></td>"
            else:
                date_obj = datetime.date(yy, mm, day)
                is_today = "today" if date_obj == today else ""
                # 今日の日付だけに✅をつける見本
                checked = "<span class='check'>✅</span>" if date_obj == today else ""
                html_cal += f"<td class='{is_today}'>{day}{checked}</td>"
        html_cal += "</tr>"
    st.markdown(html_cal + "</table>", unsafe_allow_html=True)
    st.caption("※デモ版のため、今日の日付にのみ見本の✅を表示しています。")

with tab3:
    st.subheader("全データ（表示見本）")
    # ダミーの表を表示
    demo_df = pd.DataFrame([{
        "date": str(today),
        "axes": ", ".join(selected_axes),
        "goal": "デモを成功させる",
        "reflection": "AIとの共同開発を楽しんだ。",
        "advice": "その一歩が、新しい未来を創るのじゃ。",
        "image_analysis": "なし"
    }])
    st.dataframe(demo_df, use_container_width=True)
    st.caption("※本番版では、ここに過去の全データが蓄積されます。")

















































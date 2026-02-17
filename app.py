from streamlit_gsheets import GSheetsConnection
import streamlit as st
import datetime
import google.generativeai as genai
import pandas as pd
import os
import random
from PIL import Image

# タイムゾーン指定のために追加
from datetime import timedelta, timezone

# --- 日本時間(JST)を計算で取得 ---
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.datetime.now(JST)
today = now.date()

# --- ページ設定 ---
st.set_page_config(page_title="limit my life", layout="centered")

# --- 保存用ファイルの準備 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. システム設定（サイドバー） ---
st.sidebar.title("System Settings")
limit_age = st.sidebar.number_input("End Age (寿命の目安)", value=80, min_value=1)
api_key = st.sidebar.text_input("Gemini API Key", type="password")

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
not_to_do_list = ["無駄なSNS", "夜更かし", "過度な飲酒", "サボり", "後回し", "感情的な反応", "比較", "言い訳", "嘘をつく", "批判"]
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

    # すべて左端が綺麗に揃っている必要があります
    spacer = "&nbsp;" * 16
    st.markdown(f"{spacer}🌅{spacer}☀️{spacer}🌆{spacer}🌙", unsafe_allow_html=True)
    st.divider()
    monthly_goal = st.text_input("今月の目標", placeholder="この一ヶ月で到達したい姿を書いてください")
    
    if "prompt" not in st.session_state:
        st.session_state.prompt = "今の正直な気持ちを、自分の軸に照らして言葉にしてみよう"
    
    reflection_text = st.text_area(st.session_state.prompt, height=150)
    uploaded_file = st.file_uploader("今日の1枚を登録する（任意）", type=["jpg", "jpeg", "png"])
    img = None
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)

    if st.button("伴走者と対話して刻む"):
        if not api_key:
            st.error("サイドバーにAPIキーを入力してください。")
        elif not reflection_text:
            st.warning("内省内容を入力してください。")
        else:
            try:
                model = genai.GenerativeModel('gemini-3-flash-preview')
                is_devil_mode = len(done_bad_habits) >= 2
                
                persona_prompts = {
                    "子供（純粋）": "好奇心旺盛で純粋な子供です。色や形に反応し、遊び心を忘れない言葉をかけて。",
                    "老人（経験）": "慈愛深い老人です。時の流れや無常を感じ取り、自己受容を促す穏やかな言葉をかけて。",
                    "賢者（真理）": "本質を突く賢者です。秩序を読み解き、内省につながる静かな問いを投げかけて。"
                }
                
                base_prompt = f"""
                あなたは{persona_prompts[companion_type]}
                今の視点: {selected_axes}
                今日やってしまったこと: {done_bad_habits}
                日記: 「{reflection_text}」
                """
                
                if is_devil_mode:
                    # 悪魔モード：写真の有無に関わらず、誘惑と叱責
                    full_prompt = base_prompt + "\n重要：ユーザーは悪い習慣を2つ以上行いました。前半は伴走者として厳しく叱責し、後半は『悪魔』が登場して甘く誘惑する二段構えで答えて。写真がある場合はその情景も交えて。"
                elif img:
                    # 写真がある通常の対話：画像解析を優先
                    full_prompt = base_prompt + "\n写真の「色・光・空気感」のどれか1つを拾い、日記の内容と結びつけて1〜2文で勇気づけ気味に答えて。"
                else:
                    # 写真がない通常の対話：テキストの深化に集中
                    full_prompt = base_prompt + "\n日記の内容から心の動きを読み取り、今の視点を踏まえて、1〜2文で心に届く前向きな対話をして。"

                # 送信データの構築（ここが判別の肝）
                content = [full_prompt, img] if img else [full_prompt]
                response = model.generate_content(content)
                
                st.markdown(f"### 【{companion_type}からの言葉】")
                if is_devil_mode:
                    st.error(response.text)
                else:
                    st.info(response.text)

                # --- 修正の肝：ここから try ブロックを開始する ---
                try:
                # 1. 保存するデータを辞書形式で用意
                    new_data_dict = {
                        "date": str(today), 
                        "axes": ", ".join(selected_axes), 
                        "goal": monthly_goal, 
                        "reflection": reflection_text, 
                        "advice": response.text,
                        "bad_habits": ", ".join(done_bad_habits)
                    }
                    
                    # 2. 【改善】全体を読み込まず、1行だけ直接追記する
                    # これにより通信量が激減し、3分かかっていた処理が数秒になります
                    conn.create(worksheet="Sheet1", data=pd.DataFrame([new_data_dict]))
                    
                    st.success("スプレッドシートに日記を刻みました！")
               except Exception as e:
                # この行の左端は try と縦のラインを合わせる
                st.error(f"エラーが発生しました: {e}")
with tab2:
    st.subheader("内省カレンダー")
    try:
        # スプレッドシートから最新データを読み込む
        df_log = conn.read(worksheet="Sheet1")
        
        if not df_log.empty:
            # 日付列を日付型に変換
            df_log['date'] = pd.to_datetime(df_log['date']).dt.date
            import calendar
            cal_date = today
            yy, mm = cal_date.year, cal_date.month
            st.write(f"### {yy}年 {mm}月")
            
            month_days = calendar.monthcalendar(yy, mm)
            written_days = set(df_log['date'].values)

            # 横並びカレンダーの表示
            html_cal = "<style>.cal-table { width: 100%; border-collapse: collapse; table-layout: fixed; } .cal-table th, .cal-table td { text-align: center; padding: 5px 0; border: 1px solid #ddd; font-size: 14px; } .check { color: #2ecc71; font-weight: bold; } .today { background-color: #e0f7fa; }</style><table class='cal-table'><tr><th>月</th><th>火</th><th>水</th><th>木</th><th>金</th><th style='color:blue;'>土</th><th style='color:red;'>日</th></tr>"
            for week in month_days:
                html_cal += "<tr>"
                for i, day in enumerate(week):
                    if day == 0:
                        html_cal += "<td></td>"
                    else:
                        date_obj = datetime.date(yy, mm, day)
                        is_today = "today" if date_obj == today else ""
                        checked = "<span class='check'>✅</span>" if date_obj in written_days else ""
                        html_cal += f"<td class='{is_today}'>{day}{checked}</td>"
                html_cal += "</tr>"
            st.markdown(html_cal + "</table>", unsafe_allow_html=True)
        else:
            st.info("データがまだありません。最初の日記を刻んでみましょう！")
    except Exception as e:
        st.error(f"データの読み込みに失敗しました。Secretsの設定を確認してください。")

with tab3:
    st.subheader("全データ表示")
    try:
        df_all = conn.read(worksheet="Sheet1")
        st.dataframe(df_all, use_container_width=True)
    except:
        st.info("データが読み込めません。")


























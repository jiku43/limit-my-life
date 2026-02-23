import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime

# --- 初期設定 ---
st.set_page_config(page_title="limit-my-life (Demo)", layout="centered")

# APIキーの設定（Secretsから読み込む設定にしています）
if "api_key" in st.secrets:
    genai.configure(api_key=st.secrets["api_key"])
else:
    st.error("APIキーが設定されていません。サイドバーから入力してください。")

# --- サイドバーの設定 ---
st.sidebar.title("設定（デモ版）")
st.sidebar.info("※このデモ版ではデータの保存は行われません。")

# キャラクター選択
char_type = st.sidebar.radio("対話相手を選択", ["賢者（真理）", "老人（経験）", "ポリエ（独創）"])

# --- メイン画面 ---
st.title("limit-my-life 伴走デモ")
st.write("今の正直な気持ちを、自分の軸に照らして言葉にしてみよう。")

# 入力欄
reflection_text = st.text_area("今日の振り返り", height=150)
uploaded_file = st.file_uploader("今日の1枚を登録（任意）", type=["jpg", "jpeg", "png"])

if st.button("伴走者と対話する（保存なし）"):
    if not reflection_text:
        st.warning("振り返りを入力してください。")
    else:
        with st.spinner("AIがあなたの言葉を咀嚼しています..."):
            try:
                # モデルの設定
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # プロンプト構築（ジクさんの「軸」をベースにした指示）
                prompt = f"あなたは{char_type}として、以下の振り返りに対してアドバイスをください。\n\n内容: {reflection_text}"
                
                # 画像がある場合の処理
                if uploaded_file:
                    import PIL.Image
                    img = PIL.Image.open(uploaded_file)
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(prompt)
                
                # 結果表示
                st.subheader(f"【{char_type} からの言葉】")
                st.write(response.text)
                
                # 保存機能の代わりのメッセージ
                st.divider()
                st.info("💡 本番版では、ここでスプレッドシートに ✅ が刻まれ、カレンダーに反映されます。")
                
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# -*- coding: utf-8 -*-
"""
🎙️ 語音轉文字 Word 工具 — Streamlit 版
=============================================
支援國語（普通話）與英文
上傳音檔（MP3/WAV/M4A/FLAC…）→ 語音轉文字 → 產出並下載 Word 檔

本檔同時適用於：
  1. 本機執行：  streamlit run app.py
  2. GitHub + Streamlit Community Cloud 雲端部署（見 README.md）
=============================================
"""

import io
import os
import time
import streamlit as st
from datetime import datetime
from docx import Document

import imageio_ffmpeg
import whisper

# Whisper 依賴 ffmpeg。若部署環境（如 Streamlit Cloud）未內建系統 ffmpeg，
# 這裡改用 imageio-ffmpeg 自帶的 ffmpeg 執行檔加入 PATH，確保可正常轉檔。
os.environ["PATH"] = (
    os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe()) + os.pathsep + os.environ.get("PATH", "")
)

# -----------------------------------------------------------------
# 頁面設定
# -----------------------------------------------------------------
st.set_page_config(
    page_title="語音轉文字 Word",
    page_icon="🎙️",
    layout="centered",
)

st.title("🎙️ 語音轉文字 Word 工具")
st.caption("支援國語（普通話）與英文 ・ 上傳音檔 → 轉成文字 → 下載 Word")

# -----------------------------------------------------------------
# 側邊欄：設定
# -----------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 設定")

    lang_map = {
        "自動偵測": None,
        "國語 (普通話)": "zh",
        "英文": "en",
    }
    lang_choice = st.selectbox("辨識語言", list(lang_map.keys()), index=0)
    language = lang_map[lang_choice]

    model_size = st.selectbox(
        "模型大小（越大越準、越慢）",
        ["tiny", "base", "small", "medium"],
        index=2,  # 預設 small
        help="tiny 最快最省資源；medium 最準但較慢、記憶體需求較高。",
    )

    st.markdown("---")
    st.caption("模型首次載入需下載數百 MB，之後會快取加速。")

# -----------------------------------------------------------------
# 載入模型（快取：同一個模型只下載/載入一次）
# -----------------------------------------------------------------
@st.cache_resource(show_spinner="載入語音模型中（首次較久，請稍候）...")
def load_model(size: str):
    return whisper.load_model(size)

# -----------------------------------------------------------------
# 上傳音檔
# -----------------------------------------------------------------
audio_file = st.file_uploader(
    "📂 請上傳音檔",
    type=["mp3", "wav", "m4a", "flac", "ogg", "aac"],
    help="支援 MP3 / WAV / M4A / FLAC / OGG / AAC。",
)

if audio_file is not None:
    # 先將上傳的檔案暫存到本機，供 Whisper 讀取
    suffix = audio_file.name.rsplit(".", 1)[-1].lower()
    tmp_path = f"/tmp/upload_{int(time.time())}.{suffix}"
    with open(tmp_path, "wb") as f:
        f.write(audio_file.getbuffer())

    size_kb = audio_file.size / 1024
    st.audio(audio_file)  # 預覽播放
    st.success(f"已上傳：**{audio_file.name}**（{size_kb:.1f} KB）")

    if st.button("▶️ 開始辨識", type="primary"):
        with st.spinner("載入模型中（首次較久）..."):
            model = load_model(model_size)

        with st.spinner("正在辨識文字，請耐心等待（音檔越長越久）..."):
            result = model.transcribe(tmp_path, language=language)
            text = result["text"].strip()

        st.markdown("---")
        st.subheader("📄 辨識結果")
        if not text:
            st.warning("未辨識到文字，請確認音檔內容，或改用更清晰、無背景噪音的音檔。")
        else:
            st.text_area("辨識文字", text, height=280)

            # 建立 Word 檔
            doc = Document()
            doc.add_heading("語音轉文字結果", level=1)
            doc.add_paragraph(f"來源檔案：{audio_file.name}")
            doc.add_paragraph(
                f"辨識時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            doc.add_paragraph()
            doc.add_paragraph(text)

            # 轉成 BytesIO，供下載按鈕使用
            buf = io.BytesIO()
            doc.save(buf)
            buf.seek(0)

            out_name = audio_file.name.rsplit(".", 1)[0] + "_轉文字.docx"
            st.download_button(
                label="⬇️ 下載 Word 檔",
                data=buf,
                file_name=out_name,
                mime=(
                    "application/vnd.openxmlformats-officedocument"
                    ".wordprocessingml.document"
                ),
                type="primary",
            )
#(註：內容由 AI 生成)

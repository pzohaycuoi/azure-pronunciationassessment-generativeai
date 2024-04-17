import streamlit as st
from st_audiorec import st_audiorec
from func import (
    pronunciation_assessment_with_content_assessment,
    text_to_speech,
    transcribe_real_time_audio
)

st.set_page_config(page_title="Azure SST", page_icon="🗣️", initial_sidebar_state="auto", layout='centered')
default_lang = "English"
lang_codes = {'Arabic': 'ar-EG', 'Bahasa Indonesian': 'id-ID', 'Bengali': 'bn-IN',
              'Chinese Mandarin': 'zh-CN', 'Dutch': 'nl-NL', 'English (default)': 'en-US', 'French': 'fr-FR',
              'German': 'de-DE', 'Hindi': 'hi-IN', 'Italian': 'it-IT', 'Japanese': 'ja-JP', 'Korean': 'ko-KR',
              'Russian': 'ru-RU', 'Spanish': 'es-ES', 'Telugu': 'te-IN'}

with st.sidebar:
    option = st.selectbox('Select Option', ('Speech-to-Text', 'Text-to-Speech', "Speech-Assessment"))
    lang = st.selectbox('Choose the language', list(lang_codes.keys()), index=5)
    lang_code = lang_codes[lang]
    if (option == "Speech-to-Text"):
        req_type = 'stt'
    elif (option == "Text-to-Speech"):
        req_type = 'tts'
    else:
        req_type = 'pra'

if req_type == "stt" or req_type == "pra":
    icon = '🗣️'
else:
    icon = '📝'

st.title(f"{option} with Azure AI"+icon)


if req_type == "stt":
    st.info("Speak in "+lang)
    if st.button("Start Transcription"):
        transcribe_real_time_audio(lang_code)
elif req_type == "tts":
    st.info("Type text in "+lang)
    text = st.text_area("Enter text for Text-to-Speech")
    if st.button("Generate Speech"):
        if text.strip() == "":
            st.error('Dont leave it empty😪! Enter text 😁')
        else:
            text_to_speech(text, lang_code)
else:
    st.info("Speak in "+lang)
    topic = st.text_area("Enter topic for Pronunciation Assessment", "how IT impact to our world")
    wav_audio_data = st_audiorec()
    audio_file = "./audio.wav"
    if wav_audio_data:
        with open(audio_file, "wb") as f:
            f.write(wav_audio_data)
    if st.button("Start Assessment"):
        with st.spinner("Performing Pronunciation Assessment..."):
            pronunciation_assessment_with_content_assessment(topic, lang_code, audio_file)

import os

import streamlit as st
import requests
from dotenv import load_dotenv
from st_audiorec import st_audiorec


load_dotenv()
BACKEND_URL = os.environ["BACKEND_URL"]


def pron_assesst(audio_file_path: str, topic: str):
    body = {
        "audio_file": audio_file_path,
        "topic": topic
    }
    print(f"body request: {body}")
    response = requests.post(f"{BACKEND_URL}/pron_assesst", json=body)
    return response


topic_input = st.text_input("Enter topic: ", "how IT impact to our world")
wav_audio_data = st_audiorec()
audio_wav_file = "./audio.wav"
if wav_audio_data:
    with open(audio_wav_file, "wb") as f:
        f.write(wav_audio_data)

submit_btn = st.button("Submit")
if submit_btn:
    with st.spinner("Wait for it..."):
        print(f"audio_wav_file: {audio_wav_file}")
        print(f"topic_input: {topic_input}")
        result = pron_assesst(audio_wav_file, topic_input)

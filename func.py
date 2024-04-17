import os
import time
from dotenv import load_dotenv
import streamlit as st
import azure.cognitiveservices.speech as speechsdk


load_dotenv()
speech_key = os.getenv('AZURE_SPEECH_SUBSCRIPTION_KEY')
service_region = os.getenv('AZURE_SPEECH_REGION')
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)


def pronunciation_assessment_with_content_assessment(topic: str, lang_code: str, audio_file: str):
    """Performs content assessment asynchronously with input from an audio file.
        See more information at https://aka.ms/csspeech/pa"""

    # Create an instance of a speech config with specified subscription key and service region.
    audio_config = speechsdk.audio.AudioConfig(filename=audio_file)

    # Create pronunciation assessment config, set grading system, granularity and if enable miscue based on your requirement.
    pronunciation_config = speechsdk.PronunciationAssessmentConfig(
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=False)
    pronunciation_config.enable_prosody_assessment()
    pronunciation_config.enable_content_assessment_with_topic(topic)

    # Create a speech recognizer using a file as audio input.
    language = lang_code
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, language=language, audio_config=audio_config)
    # Apply pronunciation assessment config to speech recognizer
    pronunciation_config.apply_to(speech_recognizer)

    done = False
    pron_results = []
    recognized_text = ""

    def stop_cb(evt):
        """callback that signals to stop continuous recognition upon receiving an event `evt`"""
        print("CLOSING on {}".format(evt))
        nonlocal done
        done = True

    def recognized(evt):
        nonlocal pron_results, recognized_text
        if (evt.result.reason == speechsdk.ResultReason.RecognizedSpeech or
                evt.result.reason == speechsdk.ResultReason.NoMatch):
            pron_results.append(speechsdk.PronunciationAssessmentResult(evt.result))
            if evt.result.text.strip().rstrip(".") != "":
                print(f"Recognized: {evt.result.text}")
                recognized_text += " " + evt.result.text.strip()

    # Connect callbacks to the events fired by the speech recognizer
    speech_recognizer.recognized.connect(recognized)
    speech_recognizer.session_started.connect(lambda evt: print("SESSION STARTED: {}".format(evt)))
    speech_recognizer.session_stopped.connect(lambda evt: print("SESSION STOPPED {}".format(evt)))
    speech_recognizer.canceled.connect(lambda evt: print("CANCELED {}".format(evt)))
    # Stop continuous recognition on either session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Start continuous pronunciation assessment
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(.5)
    speech_recognizer.stop_continuous_recognition()

    # Content assessment result is in the last pronunciation assessment block
    assert pron_results[-1].content_assessment_result is not None
    content_result = pron_results[-1].content_assessment_result
    print(f"Content Assessment for: {recognized_text.strip()}")
    st.subheader("Content Assessment")
    st.write(f"{recognized_text.strip()}")
    print("Content Assessment results:\n"
          f"\tGrammar score: {content_result.grammar_score:.1f}\n"
          f"\tVocabulary score: {content_result.vocabulary_score:.1f}\n"
          f"\tTopic score: {content_result.topic_score:.1f}")
    st.subheader("Content Assessment results")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Grammar score", content_result.grammar_score)
    with col2:
        st.metric("Vocabulary score", content_result.vocabulary_score)
    with col3:
        st.metric("Topic score", content_result.topic_score)
    return {
        "content_assessment_result": content_result,
        "content_assessmment": recognized_text.strip(),
        "pronunciation_assessment_results": pron_results
    }


def text_to_speech(text: str, lang_code: str):
    try:
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_config.speech_synthesis_language = lang_code
        audio_output_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config, audio_output_config=audio_output_config)
        with st.spinner("Speaking 🗣️..."):
            result = speech_synthesizer.speak_text_async(text).get()
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                st.success("Synthesized Speech !")
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                st.error("Speech synthesis canceled due to ⚠{}".format(cancellation_details.reason))
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    if cancellation_details.error_details:
                        st.error("Error details: {}".format(cancellation_details.error_details))
    except Exception as e:
        st.error(f"An error occurred: {e}")


def transcribe_real_time_audio(lang_code: str):
    st.info("Speak into your microphone 🗣️...", icon="💡")
    try:
        speech_config.speech_recognition_language = lang_code
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        with st.spinner("Listening🧏🏻..."):
            result = speech_recognizer.recognize_once_async().get()
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                st.subheader("Transcription")
                st.success("{}".format(result.text))
                speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
                result = speech_synthesizer.speak_text_async(result.text).get()
            elif result.reason == speechsdk.ResultReason.NoMatch:
                st.error("No speech could be recognized")
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                st.error("Speech Recognition canceled: {}".format(cancellation_details.reason))
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    st.error("Error details: {}".format(cancellation_details.error_details))
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
import azure.cognitiveservices.speech as speechsdk
import uvicorn


def pronunciation_assessment_with_content_assessment(audio_file, topic: str = "how IT impact to our world"):
    """Performs content assessment asynchronously with input from an audio file.
        See more information at https://aka.ms/csspeech/pa"""

    # Create an instance of a speech config with specified subscription key and service region.
    # Replace with your own subscription key and service region (e.g., "westus").
    # Note: The sample is for en-US language.
    speech_config = speechsdk.SpeechConfig(
        subscription=os.environ["AZURE_SPEECH_SUBSCRIPTION_KEY"], region=os.environ["AZURE_SPEECH_REGION"])
    # Generally, the waveform should longer than 20s and the content should be more than 3 sentences.
    audio_config = speechsdk.audio.AudioConfig(filename=audio_file)

    # Create pronunciation assessment config, set grading system, granularity and if enable miscue based on your requirement.
    # topic = input("Enter topic: ")
    # if not topic:
    #     topic = "how IT impact to our world"
    #     print(f"No topic input so using default topic is: {topic}")

    pronunciation_config = speechsdk.PronunciationAssessmentConfig(
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=False)
    pronunciation_config.enable_prosody_assessment()
    pronunciation_config.enable_content_assessment_with_topic(topic)

    # Create a speech recognizer using a file as audio input.
    language = 'en-US'
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
                print(f"Recognizing: {evt.result.text}")
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
    print("Content Assessment results:\n"
          f"\tGrammar score: {content_result.grammar_score:.1f}\n"
          f"\tVocabulary score: {content_result.vocabulary_score:.1f}\n"
          f"\tTopic score: {content_result.topic_score:.1f}")
    return {
        "content_assessment_result": content_result,
        "content_assessmment": recognized_text.strip(),
        "pronunciation_assessment_results": pron_results
    }


app = FastAPI()
load_dotenv()


class PronunciationAssessmentRequest(BaseModel):
    audio_file: str
    topic: str


@app.post("/pron_assesst")
def pron_assesst(req: PronunciationAssessmentRequest):
    return pronunciation_assessment_with_content_assessment(req.audio_file,
                                                            req.topic)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8501)

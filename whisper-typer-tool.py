import codecs
import whisper
import time
import threading
import pyaudio
import uuid
import wave
import os
import queue
from datetime import datetime
from enum import Enum
from pathlib import Path
from playaudio import playaudio
from pynput import keyboard

ROOT_DIR = Path(os.path.abspath(os.path.curdir))
print(f"Root directory: {ROOT_DIR}")


class ModelChoice(Enum):
    """ exhaustive list of available models for Whisper API"""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


# load model
# model selection -> refer to the ModelChoice(Enum) class above
model_choice = ModelChoice.BASE

print("loading model...")
model = whisper.load_model(model_choice.value)
playaudio(ROOT_DIR.joinpath("model_loaded.wav"))
print(f"{model_choice.value} model loaded")

record = threading.Event()
stop_recording = False
is_recording = threading.Event()
terminate_event = threading.Event()
pykeyboard = keyboard.Controller()


def transcribe_speech(f_queue: queue.Queue):
    file_name = f_queue.get()

    try:
        result = model.transcribe(f"{file_name}.wav")
        print(result["text"] + "\n")
    except RuntimeError as err:
        print(f"Error in transcribe: {err}\n skipping and cleaning up temporary files")
        os.remove(f"{file_name}.wav")
        return

    now = str(datetime.now()).split(".")[0]
    with codecs.open('transcribe.log', 'a', encoding='utf-8') as f:
        f.write(now + " : " + result["text"] + "\n")
    for element in result["text"]:
        try:
            pykeyboard.type(element)
            time.sleep(0.0025)
        except:
            print("empty or unknown symbol")
    os.remove(f"{file_name}.wav")


# keyboard events
pressed = set()

COMBINATIONS = [
    {
        "keys": [
            # {keyboard.Key.ctrl ,keyboard.Key.shift, keyboard.KeyCode(char="r")},
            # {keyboard.Key.ctrl ,keyboard.Key.shift, keyboard.KeyCode(char="R")},
            {keyboard.Key.f2},
        ],
        "command": "start record",
    },
    {
        "keys": [
            {keyboard.Key.f12},
        ],
        "command": "terminate program",
    }
]


# record audio
def record_speech(f_queue: queue.Queue):
    global is_recording
    global stop_recording

    is_recording.set()
    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 2
    fs = 44100  # Record at 44100 samples per second
    p = pyaudio.PyAudio()  # Create an interface to PortAudio
    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    frames = []  # Initialize array to store frames

    print("Start recording...\n")
    playaudio(ROOT_DIR.joinpath("on.wav"))

    while not stop_recording:
        data = stream.read(chunk)
        frames.append(data)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    # Terminate the PortAudio interface
    p.terminate()
    playaudio(ROOT_DIR.joinpath("off.wav"))
    print('Finish recording')

    # Save the recorded data as a WAV file
    file_name = uuid.uuid4().hex
    wf = wave.open(f"{file_name}.wav", 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))
    wf.close()

    stop_recording = False
    is_recording.clear()
    f_queue.put(file_name)


# hot key events
def on_press(key):
    pressed.add(key)


def on_release(key):
    global pressed
    global record
    global is_recording
    global stop_recording

    for c in COMBINATIONS:
        for keys in c["keys"]:
            if keys.issubset(pressed):
                if c["command"] == "terminate program":
                    print("terminating")
                    stop_recording = True
                    terminate_event.set()
                elif c["command"] == "start record" and not record.is_set():
                    if is_recording.is_set():
                        stop_recording = True
                    else:
                        record.set()

                pressed = set()


def main_thread():
    file_queue = queue.Queue()
    print("ready - start transcribing with F2 ...\n")

    t1 = None
    t2 = None

    while True:
        # call record if record event set
        if file_queue.empty():
            record.wait(0.5)

        if record.is_set():
            t1 = threading.Thread(target=record_speech, args=(file_queue,))
            t1.start()
            record.clear()

        # call transcribe if there are files ready to be transcribed
        if not file_queue.empty():
            t2 = threading.Thread(target=transcribe_speech, args=(file_queue,))
            t2.start()

        if terminate_event.is_set():
            print("Finishing up tasks ...")
            if not file_queue.empty():
                continue
            if t1:
                t1.join()
            if t2:
                t2.join()
            print("Terminating")
            break


if __name__ == "__main__":
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        main_thread()
        listener.stop()
        listener.join()
    print("Termination complete")

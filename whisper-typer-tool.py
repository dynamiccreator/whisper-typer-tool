import contextlib
import logging
import os
import queue
import struct
from tempfile import NamedTemporaryFile
from threading import Thread
import wave

from pynput import keyboard
from playsound import playsound
from pvrecorder import PvRecorder
import whisper


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("whisper-typer")


def main():
    # See https://github.com/openai/whisper#available-models-and-languages
    model_name = "medium"
    # Use "cpu" if cuda is not present on your machine
    device = "cuda"
    # Play sounds on recording start/stop
    play_sounds = True

    logger.info(f"Load {model_name} model")
    model = whisper.load_model(model_name, device=device)
    logger.info(f"Loaded {model_name} model")

    recordings = queue.Queue()  # Paths to recordings (.wav files)
    control_events = queue.Queue(maxsize=1)  # Start/stop recording events

    transcriber = Thread(target=recording_transcriber, args=(model, recordings))
    transcriber.start()

    recorder = Thread(
        target=speech_recorder, args=(recordings, control_events, play_sounds))
    recorder.start()

    rl = RecordControlListener(control_events)
    with keyboard.Listener(on_press=rl.on_press, on_release=rl.on_release) as listener:
        listener.join()
    # TODO: implement graceful shutdown
    recorder.join()
    transcriber.join()


def recording_transcriber(model: whisper.Whisper, recordings: queue.Queue):
    pykeyboard = keyboard.Controller()
    while True:
        with next_recording(recordings) as recording:
            result = model.transcribe(recording)
            logger.info(f"Transcribed {result['text']}")

            with contextlib.suppress(Exception):
                pykeyboard.type(f"{result['text']}")

            # Alternatively, you print each element of the result
            # if you want to experiment wIth fUnny outpUts lOOKing lIke thIs.
            # for element in result["text"]:
            #    with contextlib.suppress(Exception):
            #        pykeyboard.type(f"{element}")


@contextlib.contextmanager
def next_recording(recordings: queue.Queue):
    recording = recordings.get()
    yield recording
    os.remove(recording)


def speech_recorder(
        recordings: queue.Queue, control_events: queue.Queue, play_sounds: bool):
    while True:
        control_events.get(block=True)
        recording_path = record_speech(control_events, play_sounds)
        recordings.put(recording_path)


def record_speech(control_events: queue.Queue, play_sounds: bool):
    recorder = PvRecorder(frame_length=128)

    logger.info("Start recording")
    if play_sounds:
        playsound("on.wav")

    recorder.start()
    frames = []
    while control_events.empty():
        frame = recorder.read()
        frames.extend(frame)
    control_events.get()
    recorder.stop()

    if play_sounds:
        playsound("off.wav")
    logger.info("Finish recording")

    return store_recording(frames)


def store_recording(frames: list):
    with NamedTemporaryFile(mode="wb", suffix=".wav", delete=False) as rec:
        wav = wave.open(rec, "wb")
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.setnframes(512)
        wav.writeframes(struct.pack("h" * len(frames), *frames))
        wav.close()
        return rec.name


class RecordControlListener:
    # This uses F12 for simplicity, but it will also work if multiple keys are listed
    RECORD_TOGGLE_COMBINATION = {keyboard.Key.f8}

    def __init__(self, control_events: queue.Queue):
        self._recording_control_events = control_events
        self._pressed_keys = set()

    def on_press(self, key):
        if key in self.RECORD_TOGGLE_COMBINATION:
            self._pressed_keys.add(key)
        else:
            self._pressed_keys.clear()

    def on_release(self, key):
        if (self._pressed_keys == self.RECORD_TOGGLE_COMBINATION
                and key in self._pressed_keys):
            self._pressed_keys.remove(key)
            if not self._pressed_keys:
                with contextlib.suppress(queue.Full):
                    self._recording_control_events.put_nowait("Toggle recording")


if __name__ == "__main__":
    main()

# whisper-typer
This is a script using [openai/whisper](https://github.com/openai/whisper) to type with your voice.

# Usage
Start the script and press a hotkey (**F8** by default) to toggle recording. The hotkey is global (available from any window).

When you press the hotkey to stop recording, the script will transcribe the recording and type text starting at the current cursor position in any input field of any window.

# Setup Instructions
1. [Install poetry](https://python-poetry.org/docs/#installation)
2. Install dependencies using `poetry install`
3. Start the script using `poetry run ./whisper-typer`

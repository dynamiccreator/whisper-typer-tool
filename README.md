# whisper-typer-tool
This is a python script using [openai/whisper](https://github.com/openai/whisper) to type with your voice.
After you start the script you just press **F2** to start/stop recording. After the record is finsihed, it will type what you said starting at the current cursor position in any editor,input field etc.

# Setup Instructions

**Step 1 (Linux - Ubuntu,Debian):**

    sudo apt-get install python3 python3-pip git ffmpeg

**Step 1 (Windows):**

- Download ffmpeg from https://ffmpeg.org/ , unpack it and paste "ffmpeg.exe" in this folder
- Download and Install git from https://git-scm.com/download/win
- Download and Install python3 from https://www.python.org/downloads/windows/

**Step 1 (MAC OS - not tested):**

Download and Install ffmpeg, git and python3

**Step 2:**

    pip install -r requirements.txt

**Step 3:**

    python3 whisper-typer-tool.py

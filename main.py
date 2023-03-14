import os


if __name__ == "__main__":
    print(os.path.abspath(os.path.curdir))
    response = os.system("python whisper-typer-tool.py")



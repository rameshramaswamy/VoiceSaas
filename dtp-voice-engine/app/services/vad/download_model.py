import urllib.request
import os

MODEL_URL = "https://github.com/snakers4/silero-vad/raw/master/files/silero_vad.onnx"
DEST_PATH = os.path.join(os.path.dirname(__file__), "silero_vad.onnx")

def download():
    if not os.path.exists(DEST_PATH):
        print("Downloading VAD model...")
        urllib.request.urlretrieve(MODEL_URL, DEST_PATH)
        print("Done.")
    else:
        print("Model already exists.")

if __name__ == "__main__":
    download()
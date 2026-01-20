# Team Radio Transcription Service

This module provides offline speech-to-text capabilities for F1 team radio messages using [OpenAI's Whisper](https://github.com/openai/whisper) model.

## 🚀 Features

* **Offline Transcription:** Uses local Whisper models (privacy-focused, no API keys required).
* **Lazy Loading:** The heavy ML model is only loaded into memory when the first transcription is requested.
* **Async Support:** Handles audio downloads and processing asynchronously to avoid blocking the main event loop.
* **Automatic Cleanup:** Manages temporary audio files automatically.

## 🛠 Prerequisites

### 1. Python Dependencies
The service requires the following packages (ensure they are in your `requirements.txt`):
* `openai-whisper`
* `httpx`

### 2. System Dependencies (Important!)
Whisper relies on `ffmpeg` to process audio files. It must be installed on the system running the service.

* **Ubuntu/Debian:**
    ```bash
    sudo apt update && sudo apt install ffmpeg
    ```
* **MacOS (Homebrew):**
    ```bash
    brew install ffmpeg
    ```
* **Windows:**
    Download from [ffmpeg.org](https://ffmpeg.org/) and add to your system PATH.

## 💻 Usage

### Basic Implementation

```python
from openf1.services.transcription.whisper_service import WhisperTranscriptionService

# Initialize the service (model is not loaded yet)
# Available models: "tiny", "base", "small", "medium", "large"
service = WhisperTranscriptionService(model_name="base")

async def process_radio():
    url = "[https://path-to-f1-radio.mp3](https://path-to-f1-radio.mp3)"
    
    # Model loads here (first run) and transcribes
    result = await service.transcribe_from_url(url)
    
    if result["status"] == "completed":
        print(f"Language: {result['language']}")
        print(f"Text: {result['transcript']}")
    else:
        print(f"Error: {result['error']}")
```
## ⚙️ Model Selection

You can choose the model size based on your hardware capabilities and accuracy needs:

| Model  | Parameters | VRAM Required | Relative Speed |
|--------|------------|---------------|----------------|
| tiny   | 39 M       | ~1 GB         | ~32x           |
| base   | 74 M       | ~1 GB         | ~16x           |
| small  | 244 M      | ~2 GB         | ~6x            |
| medium | 769 M      | ~5 GB         | ~2x            |
| large  | 1550 M     | ~10 GB        | 1x             |

*Default is `base`, which offers a good balance for English-heavy F1 terminology.*

## 🧪 Testing

To run the unit tests for this service (using mocks to avoid loading the full model):

```bash
pytest tests/test_whisper_service.py
``` 

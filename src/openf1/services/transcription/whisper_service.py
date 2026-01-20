"""AI-powered transcription service for team radios using OpenAI Whisper"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class WhisperTranscriptionService:
    """Service for transcribing F1 team radio audio using Whisper AI"""

    def __init__(self, model_name: str = "base"):
        """
        Initialize transcription service

        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large)
                       - tiny: Fastest, good for real-time
                       - base: Balanced (recommended for production)
                       - small/medium: Better accuracy, slower
        """
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        """Lazy loading of Whisper model to save memory"""
        if self._model is None:
            try:
                import whisper

                logger.info(f"Loading Whisper model: {self.model_name}")
                self._model = whisper.load_model(self.model_name)
                logger.info("Whisper model loaded successfully")
            except ImportError:
                logger.error(
                    "openai-whisper not installed. Install with: pip install openai-whisper"
                )
                raise
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise
        return self._model

    async def transcribe_from_url(
        self, audio_url: str, language: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio from URL

        Args:
            audio_url: URL of the audio file (MP3)
            language: Optional language code (en, it, es, etc). If None, auto-detect

        Returns:
            Dict with:
                - transcript: The transcribed text
                - language: Detected language
                - status: "completed" or "failed"
                - error: Error message if failed
        """
        try:
            # Download audio
            logger.debug(f"Downloading audio from: {audio_url}")
            audio_data = await self._download_audio(audio_url)

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name

            try:
                # Transcribe
                logger.debug(f"Transcribing audio file: {tmp_path}")
                result = self.model.transcribe(
                    tmp_path, language=language, task="transcribe"
                )

                transcript = result["text"].strip()
                detected_language = result.get("language", language or "unknown")

                logger.info(
                    f"Transcription completed: {len(transcript)} chars, language: {detected_language}"
                )

                return {
                    "transcript": transcript,
                    "language": detected_language,
                    "status": "completed",
                }

            finally:
                # Clean up temporary file
                Path(tmp_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Transcription failed for {audio_url}: {e}", exc_info=True)
            return {
                "transcript": None,
                "language": None,
                "status": "failed",
                "error": str(e),
            }

    async def _download_audio(self, url: str, timeout: int = 30) -> bytes:
        """
        Download audio file from URL

        Args:
            url: Audio file URL
            timeout: Request timeout in seconds

        Returns:
            Audio file content as bytes

        Raises:
            httpx.HTTPError: If download fails
        """
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    def unload_model(self):
        """Unload model from memory to free resources"""
        if self._model is not None:
            logger.info("Unloading Whisper model from memory")
            del self._model
            self._model = None

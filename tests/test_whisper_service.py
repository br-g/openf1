import sys
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

current_dir = os.path.dirname(__file__)
src_path = os.path.abspath(os.path.join(current_dir, "../src"))
sys.path.insert(0, src_path)

try:
    from openf1.services.transcription.whisper_service import (
        WhisperTranscriptionService,
    )
except ImportError as e:
    raise ImportError(
        f"Erro ao importar WhisperTranscriptionService. Path: {src_path}. Erro: {e}"
    )


@pytest.fixture
def service():
    return WhisperTranscriptionService(model_name="base")


@pytest.fixture
def mock_whisper_module():
    mock_whisper = MagicMock()
    mock_model = MagicMock()

    mock_whisper.load_model.return_value = mock_model

    mock_model.transcribe.return_value = {
        "text": " Box, box. Confirm box. ",
        "language": "en",
    }

    with patch.dict("sys.modules", {"whisper": mock_whisper}):
        yield mock_whisper, mock_model


def test_initialization(service):
    assert service.model_name == "base"
    assert service._model is None


def test_model_loading(service, mock_whisper_module):
    mock_whisper, _ = mock_whisper_module

    model = service.model

    assert model is not None
    mock_whisper.load_model.assert_called_once_with("base")

    _ = service.model
    mock_whisper.load_model.assert_called_once()


@pytest.mark.asyncio
async def test_transcribe_from_url_success(service, mock_whisper_module):
    _, mock_model = mock_whisper_module
    fake_url = "http://example.com/audio.mp3"
    fake_audio_content = b"fake audio content"

    with patch("httpx.AsyncClient") as MockClientClass:
        mock_internal_client = MagicMock()
        mock_internal_client.get = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fake_audio_content
        mock_response.raise_for_status = MagicMock()

        mock_internal_client.get.return_value = mock_response

        mock_instance = MockClientClass.return_value
        mock_instance.__aenter__.return_value = mock_internal_client

        result = await service.transcribe_from_url(fake_url)

    assert result["status"] == "completed"
    assert result["transcript"] == "Box, box. Confirm box."
    assert result["language"] == "en"

    mock_model.transcribe.assert_called()


@pytest.mark.asyncio
async def test_transcribe_model_error(service, mock_whisper_module):
    _, mock_model = mock_whisper_module
    fake_url = "http://example.com/audio.mp3"

    mock_model.transcribe.side_effect = Exception("Model error")

    with patch("httpx.AsyncClient") as MockClientClass:
        mock_internal_client = MagicMock()
        mock_internal_client.get = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake audio data"
        mock_response.raise_for_status = MagicMock()

        mock_internal_client.get.return_value = mock_response

        mock_instance = MockClientClass.return_value
        mock_instance.__aenter__.return_value = mock_internal_client

        result = await service.transcribe_from_url(fake_url)

    assert result["status"] == "failed"
    assert "Model error" in result["error"]

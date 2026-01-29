from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Optional

try:
    from vosk import KaldiRecognizer, Model
except Exception:  # pragma: no cover - optional dependency
    Model = None  # type: ignore
    KaldiRecognizer = None  # type: ignore

_model: Optional["Model"] = None


def _get_model_path() -> Optional[Path]:
    raw_path = os.getenv("VOSK_MODEL_PATH", "").strip()
    if not raw_path:
        return None
    path = Path(raw_path).expanduser()
    return path if path.exists() else None


def stt_is_available() -> bool:
    return (
        Model is not None
        and KaldiRecognizer is not None
        and _get_model_path() is not None
        and shutil.which("ffmpeg") is not None
    )


def stt_status_message() -> tuple[bool, str]:
    parts: list[str] = []
    ok = True

    if Model is None or KaldiRecognizer is None:
        ok = False
        parts.append("Vosk не установлен. Установите: pip install vosk==0.3.44")

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        ok = False
        parts.append("ffmpeg не найден. Установите: brew install ffmpeg")

    model_path = _get_model_path()
    if model_path is None:
        ok = False
        raw_path = os.getenv("VOSK_MODEL_PATH", "").strip()
        if raw_path:
            parts.append(f"VOSK_MODEL_PATH указывает на несуществующую папку: {raw_path}")
        else:
            parts.append("VOSK_MODEL_PATH не задан. Пример: /path/to/vosk-model-small-ru-0.22")

    if ok:
        return True, "Голосовые включены ✅ Отправьте голосовое, я отвечу."

    return False, "Проверка голосовых:\n" + "\n".join(f"- {item}" for item in parts)


def _get_model() -> "Model":
    global _model
    if Model is None:
        raise RuntimeError("Vosk is not installed")
    model_path = _get_model_path()
    if model_path is None:
        raise RuntimeError("VOSK_MODEL_PATH is not set or invalid")
    if _model is None:
        _model = Model(str(model_path))
    return _model


def _convert_to_wav(input_path: Path, output_path: Path) -> bool:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-f",
        "wav",
        str(output_path),
    ]
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        logging.exception("FFmpeg conversion failed")
        return False


async def transcribe_audio(path: Path, *, language: Optional[str] = "ru") -> Optional[str]:
    if not stt_is_available():
        return None
    wav_path = path.with_suffix(".wav")
    if not _convert_to_wav(path, wav_path):
        return None
    try:
        model = _get_model()
        with wave.open(str(wav_path), "rb") as wf:
            rec = KaldiRecognizer(model, wf.getframerate())
            rec.SetWords(False)
            while True:
                data = wf.readframes(4000)
                if not data:
                    break
                rec.AcceptWaveform(data)
            result = rec.FinalResult()
        payload = json.loads(result or "{}")
        text = payload.get("text", "")
        return text.strip() if text else None
    except Exception:
        logging.exception("Vosk transcription failed")
        return None
    finally:
        try:
            wav_path.unlink()
        except OSError:
            pass

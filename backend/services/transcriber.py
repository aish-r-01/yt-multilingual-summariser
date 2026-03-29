import os

from groq import AsyncGroq


async def transcribe_audio(audio_path: str):
    """
    Send the mp3 at *audio_path* to Groq Whisper and return the
    verbose_json transcription object.

    Language is intentionally omitted so Whisper auto-detects it.
    The response object exposes:
      .text          – full transcript string
      .language      – top-level ISO-639-1 code
      .segments      – list of segment objects (start, end, text,
                       avg_logprob, language, …)
    """
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    with open(audio_path, "rb") as f:
        response = await client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=f,
            response_format="verbose_json",
        )

    return response

"""Bounded Gemini REST adapter; keys stay in server-side request headers."""

import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np


class GeminiServiceError(RuntimeError):
    def __init__(self, status):
        self.status = status
        super().__init__(f"Gemini request rejected (HTTP {status}).")


class GeminiProvider:
    def __init__(self, settings, repository):
        self.settings, self.repository = settings, repository

    def request(self, model, operation, payload):
        if not self.settings.gemini_api_key:
            raise RuntimeError("Gemini API key is missing.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:{operation}"
        for attempt in range(2):
            self.repository.reserve_model_call()
            request = Request(
                url,
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.settings.gemini_api_key,
                },
            )
            try:
                with urlopen(request, timeout=self.settings.model_timeout_seconds) as response:
                    return json.load(response)
            except HTTPError as exc:
                if exc.code in {429, 503} and not attempt:
                    exc.close()
                    time.sleep(5)
                    continue
                status = exc.code
                exc.close()
                raise GeminiServiceError(status) from None
            except URLError:
                raise RuntimeError("Gemini connection failed.") from None

    def embed(self, text):
        response = self.request(
            self.settings.embedding_model_id,
            "embedContent",
            {
                "model": f"models/{self.settings.embedding_model_id}",
                "content": {"parts": [{"text": text}]},
                "taskType": "SEMANTIC_SIMILARITY",
                "outputDimensionality": self.settings.embedding_dimensions,
            },
        )
        vector = np.asarray(response["embedding"]["values"], dtype=np.float32)
        if vector.shape != (self.settings.embedding_dimensions,) or not np.isfinite(vector).all():
            raise ValueError("Gemini embedding configuration mismatch")
        norm = np.linalg.norm(vector)
        if norm == 0:
            raise ValueError("Empty Gemini embedding")
        return vector / norm

    def converse(self, system, prompt):
        thinking = (
            {
                "thinkingConfig": {
                    "thinkingLevel": "minimal"
                    if self.settings.gemini_model_id == "gemini-3.5-flash-lite"
                    else "low"
                }
            }
            if self.settings.gemini_model_id in {"gemini-3.8-flash", "gemini-3.5-flash-lite"}
            else {}
        )
        response = self.request(
            self.settings.gemini_model_id,
            "generateContent",
            {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 8192,
                    "responseMimeType": "application/json",
                    **thinking,
                },
            },
        )
        candidates = response.get("candidates", [])
        if not candidates or candidates[0].get("finishReason") != "STOP":
            raise ValueError("Gemini did not return a complete response")
        text = "\n".join(
            p.get("text", "") for p in candidates[0].get("content", {}).get("parts", [])
        )
        usage = response.get("usageMetadata", {})
        return text, {
            "inputTokens": usage.get("promptTokenCount", 0),
            "outputTokens": usage.get("candidatesTokenCount", 0),
            "totalTokens": usage.get("totalTokenCount", 0),
        }

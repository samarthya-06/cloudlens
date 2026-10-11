import io
import json
from urllib.error import HTTPError

import numpy as np
import pytest

from app.config import Settings
from app.gemini import GeminiProvider


class Budget:
    calls = 0

    def reserve_model_call(self):
        self.calls += 1


def test_embedding_uses_server_header_and_normalizes(monkeypatch):
    def transport(request, timeout):
        assert "private-test-key" not in request.full_url
        assert request.get_header("X-goog-api-key") == "private-test-key"
        payload = json.loads(request.data)
        assert payload["outputDimensionality"] == 768
        assert payload["taskType"] == "SEMANTIC_SIMILARITY"
        return io.BytesIO(json.dumps({"embedding": {"values": [2.0] * 768}}).encode())

    monkeypatch.setattr("app.gemini.urlopen", transport)
    settings = Settings(gemini_api_key="private-test-key", embedding_dimensions=768)
    budget = Budget()
    vector = GeminiProvider(settings, budget).embed("synthetic error")
    assert vector.shape == (768,)
    assert np.isclose(np.linalg.norm(vector), 1)
    assert budget.calls == 1


def test_service_retry_is_bounded_and_counted(monkeypatch):
    def transport(request, timeout):
        raise HTTPError(request.full_url, 503, "Unavailable", {}, io.BytesIO(b"{}"))

    monkeypatch.setattr("app.gemini.urlopen", transport)
    monkeypatch.setattr("app.gemini.time.sleep", lambda _: None)
    budget = Budget()
    with pytest.raises(RuntimeError, match="HTTP 503"):
        GeminiProvider(Settings(gemini_api_key="private-test-key"), budget).embed("synthetic")
    assert budget.calls == 2

import types
from types import SimpleNamespace
import pytest

# minimal import of the module under test
from app.services import ai_service

class FakeHistory:
    def __init__(self, idx):
        # create distinguishable values
        self.cycle_phase = f"phase{idx}"
        self.mood = f"mood{idx}"
        self.energy = f"energy{idx}"
        self.sleep = float(6 + (idx % 5))
        self.id = idx

class QueryStub:
    def __init__(self, items):
        # items should be ordered latest-first if caller expects that
        self._items = items
        self._n = None
    def filter(self, *args, **kwargs):
        return self
    def order_by(self, *args, **kwargs):
        return self
    def limit(self, n):
        self._n = n
        return self
    def all(self):
        if self._n is None:
            return self._items
        # simulate DB returning latest entries first (already arranged)
        return self._items[: self._n]

class FakeDB:
    def __init__(self, items):
        # items should be in latest-first order to match code expectations
        self._items = items
    def query(self, model):
        return QueryStub(self._items)

def test_generate_insight_uses_limit_and_returns_model_text(monkeypatch):
    # create 12 history items (more than the 10 limit in generate_insight)
    items = [FakeHistory(i) for i in range(12)]
    # ensure latest-first (index 0 is most recent for our stub)
    items_sorted = items  # already in desired order for this stub

    db = FakeDB(items_sorted)

    captured_prompts = []

    def fake_create(messages, model=None, max_tokens=None, **kwargs):
        # messages may be passed as first positional arg or kw arg depending on client
        # ai_service calls: client.chat.completions.create(model=..., messages=[...])
        # so here we accept messages kw or positional
        # capture messages content for assertions
        if isinstance(messages, dict) or isinstance(messages, list):
            msg = messages
        else:
            # check kwargs
            msg = kwargs.get('messages') or messages
        # ensure we extract the content string
        if isinstance(msg, list) and msg:
            captured_prompts.append(msg[0].get('content', ''))
        else:
            captured_prompts.append(str(msg))
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="FAKE_INSIGHT"))])

    # monkeypatch the client's create method
    # the exact attribute path in ai_service is client.chat.completions.create
    monkeypatch.setattr(ai_service.client.chat.completions, "create", fake_create)

    data = SimpleNamespace(cycle_phase="menstrual", mood="sad", energy="low", sleep=7.0, user_id="42")
    out = ai_service.generate_insight(data, db, user_id="42")
    assert out == "FAKE_INSIGHT"
    assert captured_prompts, "Prompt was not captured"
    prompt_text = captured_prompts[0]
    # count occurrences of history lines e.g., "Cycle Phase:"
    history_count = prompt_text.count("Cycle Phase:")
    # generate_insight limits to 10 entries
    assert history_count <= 10

def test_generate_insight_uses_data_userid_when_no_userid_arg(monkeypatch):
    # create a few history items
    items = [FakeHistory(i) for i in range(3)]
    db = FakeDB(items)

    captured_prompts = []
    def fake_create(messages, model=None, max_tokens=None, **kwargs):
        if isinstance(messages, list) and messages:
            captured_prompts.append(messages[0].get('content', ''))
        else:
            captured_prompts.append(str(messages))
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="OK"))])

    monkeypatch.setattr(ai_service.client.chat.completions, "create", fake_create)

    # data includes user_id attribute; pass user_id arg as None to exercise that path
    data = SimpleNamespace(cycle_phase="follicular", mood="ok", energy="medium", sleep=8.0, user_id="99")
    out = ai_service.generate_insight(data, db, user_id=None)
    assert out == "OK"
    assert captured_prompts, "Prompt was not captured"
    assert "Cycle Phase:" in captured_prompts[0]
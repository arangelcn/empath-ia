"""Tests that message_count is incremented exactly once per exchange."""
import asyncio

from src.repositories.conversation_repository import ConversationRepository


class FakeUpdateResult:
    modified_count = 1
    matched_count = 1


class FakeCollection:
    def __init__(self, conversation=None):
        self._conversation = conversation or {}
        self.update_calls = []
        self.find_calls = []

    async def find_one(self, query):
        self.find_calls.append(query)
        return self._conversation

    async def update_one(self, query, update):
        self.update_calls.append((query, update))
        return FakeUpdateResult()

    def find(self, query, **kwargs):
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


def make_repo_with_conversation(session_id="joao_session-2"):
    conversation = {
        "chat_id": f"chat_{session_id}",
        "session_id": session_id,
        "legacy_session_id": session_id,
        "username": "joao",
        "therapeutic_session_id": "session-2",
    }
    fake_col = FakeCollection(conversation=conversation)

    async def resolve_ref(ref, *, username=None, therapeutic_session_id=None, create=False):
        return {
            "chat_id": conversation["chat_id"],
            "legacy_session_id": session_id,
            "username": "joao",
            "therapeutic_session_id": "session-2",
            "conversation": conversation,
        }

    def extract_username(sid):
        parts = sid.rsplit("_", 1)
        return parts[0] if len(parts) == 2 else None

    repo = ConversationRepository(resolve_ref=resolve_ref, extract_username=extract_username)

    import src.repositories.conversation_repository as repo_module
    orig = repo_module.get_collection

    def fake_get_collection(name):
        return fake_col

    repo_module.get_collection = fake_get_collection
    return repo, repo_module, orig, fake_col


def test_update_message_count_increments_exactly_once():
    repo, repo_module, orig, fake_col = make_repo_with_conversation()

    try:
        asyncio.run(repo.update_message_count("joao_session-2"))
    finally:
        repo_module.get_collection = orig

    inc_calls = [
        call for call in fake_col.update_calls
        if call[1].get("$inc", {}).get("message_count") == 1
    ]
    assert len(inc_calls) == 1, f"Expected 1 increment call, got {len(inc_calls)}"


def test_save_message_stores_correct_fields():
    repo, repo_module, orig, fake_col = make_repo_with_conversation()

    inserted = []
    original_insert = fake_col.update_calls

    class FakeInsertCollection(FakeCollection):
        async def insert_one(self, doc):
            inserted.append(doc)

            class Result:
                inserted_id = "fake_id"
            return Result()

    import src.repositories.conversation_repository as repo_module2
    orig2 = repo_module2.get_collection

    fake_insert_col = FakeInsertCollection(conversation={
        "chat_id": "chat_joao_session-2",
        "session_id": "joao_session-2",
        "legacy_session_id": "joao_session-2",
        "username": "joao",
        "therapeutic_session_id": "session-2",
    })

    def fake_get_collection_v2(name):
        return fake_insert_col

    repo_module2.get_collection = fake_get_collection_v2

    try:
        asyncio.run(repo.save_message("joao_session-2", "user", "Estou ansioso", None))
    finally:
        repo_module2.get_collection = orig2

    assert len(inserted) == 1
    msg = inserted[0]
    assert msg["type"] == "user"
    assert msg["content"] == "Estou ansioso"
    assert msg["username"] == "joao"
    assert msg["session_id"] == "joao_session-2"

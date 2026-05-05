import asyncio
from datetime import datetime

from src.services.user_therapeutic_session_service import (
    REGISTRATION_SESSION_ID,
    UserTherapeuticSessionService,
)


class FakeInsertResult:
    inserted_id = "inserted-id"


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, key, direction):
        reverse = direction < 0
        self.docs = sorted(
            self.docs,
            key=lambda doc: doc.get(key) or datetime.min,
            reverse=reverse,
        )
        return self

    async def to_list(self, length):
        return self.docs[:length]

    def __aiter__(self):
        self._iter = iter(self.docs)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeUserSessionsCollection:
    def __init__(self):
        self.docs = []

    def _matches(self, doc, query):
        for key, value in query.items():
            if isinstance(value, dict) and "$in" in value:
                if doc.get(key) not in value["$in"]:
                    return False
            elif doc.get(key) != value:
                return False
        return True

    async def find_one(self, query, *args, **kwargs):
        docs = [doc for doc in self.docs if self._matches(doc, query)]
        sort = kwargs.get("sort")
        if sort:
            key, direction = sort[0]
            docs.sort(key=lambda doc: doc.get(key) or datetime.min, reverse=direction < 0)
        return docs[0] if docs else None

    async def insert_one(self, doc):
        doc = {**doc, "_id": f"id-{len(self.docs) + 1}"}
        self.docs.append(doc)
        return FakeInsertResult()

    def find(self, query, *args, **kwargs):
        docs = [doc for doc in self.docs if self._matches(doc, query)]
        sort = kwargs.get("sort")
        if sort:
            key, direction = sort[0]
            docs.sort(key=lambda doc: doc.get(key) or datetime.min, reverse=direction < 0)
        return FakeCursor(docs)

    async def count_documents(self, query):
        return len([doc for doc in self.docs if self._matches(doc, query)])


def make_service(collection):
    service = UserTherapeuticSessionService()
    service._user_sessions_collection = collection
    return service


def test_get_user_sessions_creates_registration_session_when_missing():
    collection = FakeUserSessionsCollection()
    service = make_service(collection)

    sessions = asyncio.run(service.get_user_sessions("ana"))

    assert len(sessions) == 1
    assert sessions[0]["session_id"] == REGISTRATION_SESSION_ID
    assert sessions[0]["status"] == "unlocked"
    assert sessions[0]["is_registration_session"] is True
    assert collection.docs[0]["username"] == "ana"


def test_get_user_sessions_keeps_status_filter_after_registration_seed():
    collection = FakeUserSessionsCollection()
    service = make_service(collection)

    sessions = asyncio.run(service.get_user_sessions("ana", status="completed"))

    assert sessions == []
    assert collection.docs[0]["session_id"] == REGISTRATION_SESSION_ID
    assert collection.docs[0]["status"] == "unlocked"


def test_can_create_next_session_blocks_until_registration_is_completed():
    collection = FakeUserSessionsCollection()
    service = make_service(collection)

    can_create = asyncio.run(service.can_create_next_session("ana"))

    assert can_create is False
    assert collection.docs[0]["session_id"] == REGISTRATION_SESSION_ID

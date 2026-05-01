from src.services.streaming_utils import SentenceChunker, sse_event


def test_sentence_chunker_flushes_complete_sentence():
    chunker = SentenceChunker(max_chars=200, max_wait_ms=10_000)

    assert chunker.push("Eu entendo. E ") == ["Eu entendo."]
    assert chunker.flush() == "E"


def test_sentence_chunker_flushes_long_buffer():
    chunker = SentenceChunker(max_chars=12, max_wait_ms=10_000)

    assert chunker.push("uma frase longa") == ["uma frase longa"]
    assert chunker.flush() is None


def test_sentence_chunker_does_not_time_flush_single_word():
    chunker = SentenceChunker(max_chars=200, max_wait_ms=100, min_timed_flush_chars=20, min_timed_flush_words=4)
    chunker._last_flush -= 1

    assert chunker.push("você") == []
    assert chunker.flush() == "você"


def test_sentence_chunker_time_flushes_speakable_phrase():
    chunker = SentenceChunker(max_chars=200, max_wait_ms=100, min_timed_flush_chars=20, min_timed_flush_words=4)
    chunker._last_flush -= 1

    assert chunker.push("isso parece importante para você agora") == ["isso parece importante para você agora"]
    assert chunker.flush() is None


def test_sse_event_serializes_utf8_json():
    frame = sse_event("text_delta", {"delta": "Olá", "trace_id": "trace_1"})

    assert frame.startswith("event: text_delta\n")
    assert '"delta": "Olá"' in frame
    assert frame.endswith("\n\n")

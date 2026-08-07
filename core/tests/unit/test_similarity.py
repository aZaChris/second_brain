from src.similarity import Match, cosine_similarity, find_similar, is_low_signal


def test_cosine_similarity_identical_vectors_is_one():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_cosine_similarity_orthogonal_vectors_is_zero():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_is_low_signal_for_short_text():
    assert is_low_signal("ok") is True
    assert is_low_signal("questa è una nota abbastanza lunga") is False


def test_find_similar_returns_matches_above_threshold():
    embedding = [1.0, 0.0]
    saved = [
        {"event_id": "evt_similar", "embedding": [0.99, 0.01]},
        {"event_id": "evt_unrelated", "embedding": [0.0, 1.0]},
    ]
    matches = find_similar(embedding, saved, threshold=0.75)
    assert matches == [Match(event_id="evt_similar", similarity=matches[0].similarity)]


def test_find_similar_with_no_saved_events_returns_empty():
    assert find_similar([1.0, 0.0], [], threshold=0.75) == []

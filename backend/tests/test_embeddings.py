from app.services.embeddings import clear_skill_phrase_cache, cosine_similarity, embed_texts, get_skill_phrase_embedding


def test_cosine_similarity_identical_vectors_is_one():
    vec = [1.0, 2.0, 3.0]
    assert cosine_similarity(vec, vec) == 1.0


def test_cosine_similarity_orthogonal_vectors_is_zero():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_cosine_similarity_handles_zero_vector_without_dividing_by_zero():
    assert cosine_similarity([0.0, 0.0, 0.0], [1.0, 2.0, 3.0]) == 0.0
    assert cosine_similarity([1.0, 2.0, 3.0], [0.0, 0.0, 0.0]) == 0.0
    assert cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0


def test_embed_texts_returns_none_when_key_is_blank(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "openai_api_key", "")
    assert embed_texts(["kubernetes container orchestration"]) is None


def test_embed_texts_returns_empty_list_for_empty_input(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "openai_api_key", "sk-test-key")
    assert embed_texts([]) == []


def test_skill_phrase_embedding_is_cached(monkeypatch):
    import app.services.embeddings as embeddings_module

    clear_skill_phrase_cache()
    calls = []

    def fake_embed_texts(texts):
        calls.append(texts)
        return [[1.0, 0.0, 0.0] for _ in texts]

    monkeypatch.setattr(embeddings_module, "embed_texts", fake_embed_texts)

    first = get_skill_phrase_embedding("kubernetes", "kubernetes container orchestration")
    second = get_skill_phrase_embedding("kubernetes", "kubernetes container orchestration")

    assert first == [1.0, 0.0, 0.0]
    assert second == [1.0, 0.0, 0.0]
    assert len(calls) == 1
    clear_skill_phrase_cache()

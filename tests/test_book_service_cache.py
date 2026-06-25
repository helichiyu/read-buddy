"""Book search cache behavior tests."""


async def test_search_cache_uses_full_normalized_query(monkeypatch):
    """Queries with the same first word should not share cached results."""
    import book_service

    book_service._search_cache.clear()
    google_calls = []

    async def fake_douban(query):
        return None

    async def fake_google(query):
        google_calls.append(query)
        return {"title": query, "author": "", "description": "", "cover_url": "", "isbn": "", "categories": ""}

    monkeypatch.setattr(book_service, "_search_douban", fake_douban)
    monkeypatch.setattr(book_service, "_search_google", fake_google)

    first = await book_service.search("Harry Potter")
    second = await book_service.search("Harry Bosch")
    third = await book_service.search("  harry   potter  ")

    assert first["title"] == "Harry Potter"
    assert second["title"] == "Harry Bosch"
    assert third["title"] == "Harry Potter"
    assert google_calls == ["Harry Potter", "Harry Bosch"]

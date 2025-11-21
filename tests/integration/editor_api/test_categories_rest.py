import pytest


@pytest.mark.asyncio
async def test_create_category_and_fetch_by_id(editor_client, editor_headers):
    payload = {
        "name": "Docs",
        "description": "Developer docs",
        "slug": "docs"
    }
    # Create
    resp = await editor_client.post("/editor/categories", json=payload, headers=editor_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Docs"
    assert data["slug"] == "docs"
    category_id = data["id"]

    # Fetch by ID
    resp2 = await editor_client.get(f"/editor/categories/{category_id}", headers=editor_headers)
    assert resp2.status_code == 200
    fetched = resp2.json()
    assert fetched["id"] == category_id
    assert fetched["name"] == "Docs"


@pytest.mark.asyncio
async def test_create_duplicate_slug_conflict(editor_client, editor_headers):
    payload = {
        "name": "Tutorials",
        "description": "Step by step guides",
        "slug": "tutorials"
    }
    # First create succeeds
    resp1 = await editor_client.post("/editor/categories", json=payload, headers=editor_headers)
    assert resp1.status_code == 200

    # Second create should conflict
    resp2 = await editor_client.post("/editor/categories", json=payload, headers=editor_headers)
    assert resp2.status_code == 409
    assert resp2.json()["detail"] == "Slug already exists"


@pytest.mark.asyncio
async def test_list_and_fetch_by_slug(editor_client, editor_headers):
    # Create test data first
    docs_payload = {"name": "Docs", "description": "Documentation", "slug": "docs"}
    tutorials_payload = {"name": "Tutorials", "description": "Tutorials", "slug": "tutorials"}

    resp_docs = await editor_client.post("/editor/categories", json=docs_payload, headers=editor_headers)
    assert resp_docs.status_code == 200

    resp_tutorials = await editor_client.post("/editor/categories", json=tutorials_payload, headers=editor_headers)
    assert resp_tutorials.status_code == 200

    # Should list the inserted ones
    resp = await editor_client.get("/editor/categories", headers=editor_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    assert any(c["slug"] == "docs" for c in items)
    assert any(c["slug"] == "tutorials" for c in items)

    # Fetch by slug
    resp2 = await editor_client.get("/editor/categories/slug/docs", headers=editor_headers)
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["slug"] == "docs"

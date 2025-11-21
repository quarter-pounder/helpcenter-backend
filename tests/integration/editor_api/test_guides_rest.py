import pytest


@pytest.mark.asyncio
async def test_create_guide_and_fetch_by_id(editor_client, editor_headers):
    import uuid
    unique_slug = f"getting-started-guide-{uuid.uuid4().hex[:8]}"
    payload = {
        "title": "Getting Started Guide",
        "slug": unique_slug,
        "body": {
            "blocks": [
                {"type": "heading", "level": 1, "text": "Welcome"},
                {"type": "paragraph", "text": "This is a test guide."}
            ]
        },
        "estimated_read_time": 5,
        "category_ids": [],
        "media_ids": []
    }
    # Create
    resp = await editor_client.post("/editor/guides", json=payload, headers=editor_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Getting Started Guide"
    assert data["slug"] == unique_slug
    assert data["estimated_read_time"] == 5
    assert data["body"]["blocks"][0]["type"] == "heading"
    assert "media_ids" in data
    assert isinstance(data["media_ids"], list)
    guide_id = data["id"]

    # Fetch by ID
    resp2 = await editor_client.get(f"/editor/guides/{guide_id}", headers=editor_headers)
    assert resp2.status_code == 200
    fetched = resp2.json()
    assert fetched["id"] == guide_id
    assert fetched["title"] == "Getting Started Guide"
    assert "media_ids" in fetched


@pytest.mark.asyncio
async def test_create_duplicate_slug_conflict(editor_client, editor_headers):
    import uuid
    unique_slug = f"test-guide-{uuid.uuid4().hex[:8]}"
    payload = {
        "title": "Test Guide",
        "slug": unique_slug,
        "body": {"blocks": [{"type": "paragraph", "text": "Test content"}]},
        "estimated_read_time": 3,
        "category_ids": []
    }
    # First create succeeds
    resp1 = await editor_client.post("/editor/guides", json=payload, headers=editor_headers)
    assert resp1.status_code == 200

    # Second create should conflict
    resp2 = await editor_client.post("/editor/guides", json=payload, headers=editor_headers)
    assert resp2.status_code == 409
    assert resp2.json()["detail"] == "Slug already exists"


@pytest.mark.asyncio
async def test_list_and_fetch_by_slug(editor_client, editor_headers):
    import uuid
    # Create a guide with unique slug
    unique_slug = f"list-test-guide-{uuid.uuid4().hex[:8]}"
    create_payload = {
        "title": "List Test Guide",
        "slug": unique_slug,
        "body": {"blocks": [{"type": "paragraph", "text": "Test content"}]},
        "estimated_read_time": 3,
        "category_ids": []
    }
    resp = await editor_client.post("/editor/guides", json=create_payload, headers=editor_headers)
    assert resp.status_code == 200

    # Should list the created guide
    resp = await editor_client.get("/editor/guides", headers=editor_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    assert any(g["slug"] == unique_slug for g in items)

    # Fetch by slug
    resp2 = await editor_client.get(f"/editor/guides/slug/{unique_slug}", headers=editor_headers)
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["slug"] == unique_slug


@pytest.mark.asyncio
async def test_update_guide(editor_client, editor_headers):
    import uuid
    # First create a guide
    unique_slug = f"update-test-guide-{uuid.uuid4().hex[:8]}"
    create_payload = {
        "title": "Original Title",
        "slug": unique_slug,
        "body": {"blocks": [{"type": "paragraph", "text": "Original content"}]},
        "estimated_read_time": 2,
        "category_ids": []
    }
    resp = await editor_client.post("/editor/guides", json=create_payload, headers=editor_headers)
    assert resp.status_code == 200
    guide_id = resp.json()["id"]

    # Update the guide
    update_payload = {
        "title": "Updated Title",
        "body": {"blocks": [{"type": "paragraph", "text": "Updated content"}]},
        "estimated_read_time": 4
    }
    resp2 = await editor_client.put(f"/editor/guides/{guide_id}", json=update_payload, headers=editor_headers)
    assert resp2.status_code == 200
    updated = resp2.json()
    assert updated["title"] == "Updated Title"
    assert updated["estimated_read_time"] == 4
    assert updated["body"]["blocks"][0]["text"] == "Updated content"


@pytest.mark.asyncio
async def test_delete_guide(editor_client, editor_headers):
    import uuid
    # Create a guide to delete with unique slug
    unique_slug = f"delete-test-guide-{uuid.uuid4().hex[:8]}"
    payload = {
        "title": "Guide to Delete",
        "slug": unique_slug,
        "body": {"blocks": [{"type": "paragraph", "text": "This will be deleted"}]},
        "estimated_read_time": 1,
        "category_ids": []
    }
    resp = await editor_client.post("/editor/guides", json=payload, headers=editor_headers)
    assert resp.status_code == 200
    guide_id = resp.json()["id"]

    # Delete the guide
    resp2 = await editor_client.delete(f"/editor/guides/{guide_id}", headers=editor_headers)
    assert resp2.status_code == 200

    # Verify it's deleted
    resp3 = await editor_client.get(f"/editor/guides/{guide_id}", headers=editor_headers)
    assert resp3.status_code == 404


@pytest.mark.asyncio
async def test_create_guide_with_media_ids(editor_client, editor_headers):
    """Test creating a guide with pre-existing media IDs"""
    import uuid
    import io

    # Create a guide for media upload
    unique_slug_temp = f"temp-guide-{uuid.uuid4().hex[:8]}"
    temp_guide_payload = {
        "title": "Temp Guide for Media",
        "slug": unique_slug_temp,
        "body": {"blocks": [{"type": "paragraph", "text": "Temp"}]},
        "estimated_read_time": 1,
        "category_ids": []
    }
    temp_resp = await editor_client.post("/editor/guides", json=temp_guide_payload, headers=editor_headers)
    assert temp_resp.status_code == 200
    temp_guide_id = temp_resp.json()["id"]

    # Upload media to temp guide
    file = io.BytesIO(b"fake image")
    files = {"file": ("test.jpg", file, "image/jpeg")}
    data = {"alt": "Test media"}
    media_resp = await editor_client.post(f"/editor/guides/{temp_guide_id}/media/upload", files=files, data=data, headers=editor_headers)
    assert media_resp.status_code == 200
    media_id = media_resp.json()["id"]

    # Create a new guide with this media_id
    unique_slug = f"guide-with-media-{uuid.uuid4().hex[:8]}"
    payload = {
        "title": "Guide with Media",
        "slug": unique_slug,
        "body": {"blocks": [{"type": "paragraph", "text": "Test"}]},
        "estimated_read_time": 2,
        "category_ids": [],
        "media_ids": [media_id]
    }
    resp = await editor_client.post("/editor/guides", json=payload, headers=editor_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "media_ids" in data
    assert media_id in data["media_ids"]

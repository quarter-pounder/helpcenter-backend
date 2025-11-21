import pytest
import io


@pytest.mark.asyncio
async def test_upload_media_to_guide(editor_client, editor_headers):
    """Test uploading media directly to a guide"""
    import uuid
    # First create a guide
    unique_slug = f"media-test-guide-{uuid.uuid4().hex[:8]}"
    guide_payload = {
        "title": "Media Test Guide",
        "slug": unique_slug,
        "body": {"blocks": [{"type": "paragraph", "text": "Test content"}]},
        "estimated_read_time": 3,
        "category_ids": []
    }
    guide_resp = await editor_client.post("/editor/guides", json=guide_payload, headers=editor_headers)
    assert guide_resp.status_code == 200
    guide_id = guide_resp.json()["id"]

    # Upload media to guide
    file_content = b"fake image content"
    file = io.BytesIO(file_content)

    files = {"file": ("test_image.jpg", file, "image/jpeg")}
    data = {"alt": "Test image for guide"}

    resp = await editor_client.post(f"/editor/guides/{guide_id}/media/upload", files=files, data=data, headers=editor_headers)
    assert resp.status_code == 200
    response_data = resp.json()
    assert "id" in response_data
    assert "url" in response_data
    assert "alt" in response_data
    assert response_data["alt"] == "Test image for guide"
    return guide_id, response_data["id"]


@pytest.mark.asyncio
async def test_get_guide_media(editor_client, editor_headers):
    """Test retrieving all media for a specific guide"""
    import uuid
    # Create a guide
    unique_slug = f"guide-media-test-{uuid.uuid4().hex[:8]}"
    guide_payload = {
        "title": "Guide Media Test",
        "slug": unique_slug,
        "body": {"blocks": [{"type": "paragraph", "text": "Test content"}]},
        "estimated_read_time": 2,
        "category_ids": []
    }
    guide_resp = await editor_client.post("/editor/guides", json=guide_payload, headers=editor_headers)
    assert guide_resp.status_code == 200
    guide_id = guide_resp.json()["id"]

    # Upload media to this guide
    file_content = b"fake image content for guide media test"
    file = io.BytesIO(file_content)

    files = {"file": ("guide_media_test.jpg", file, "image/jpeg")}
    data = {"alt": "Guide media test image"}

    media_resp = await editor_client.post(f"/editor/guides/{guide_id}/media/upload", files=files, data=data, headers=editor_headers)
    assert media_resp.status_code == 200
    media_id = media_resp.json()["id"]

    # Get media for guide
    resp = await editor_client.get(f"/editor/guides/{guide_id}/media", headers=editor_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(m["id"] == media_id for m in data)


@pytest.mark.asyncio
async def test_delete_guide_media(editor_client, editor_headers):
    """Test deleting media from a guide (also deletes from database)"""
    guide_id, media_id = await test_upload_media_to_guide(editor_client, editor_headers)

    # Delete media from guide
    resp = await editor_client.delete(f"/editor/guides/{guide_id}/media/{media_id}", headers=editor_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data

    # Verify media is removed from guide
    resp2 = await editor_client.get(f"/editor/guides/{guide_id}/media", headers=editor_headers)
    assert resp2.status_code == 200
    media_list = resp2.json()
    assert not any(m["id"] == media_id for m in media_list)


@pytest.mark.asyncio
async def test_upload_invalid_file_type(editor_client, editor_headers):
    """Test that non-image/video files are rejected"""
    import uuid
    # Create a guide first
    unique_slug = f"invalid-file-test-{uuid.uuid4().hex[:8]}"
    guide_payload = {
        "title": "Invalid File Test Guide",
        "slug": unique_slug,
        "body": {"blocks": [{"type": "paragraph", "text": "Test content"}]},
        "estimated_read_time": 1,
        "category_ids": []
    }
    guide_resp = await editor_client.post("/editor/guides", json=guide_payload, headers=editor_headers)
    assert guide_resp.status_code == 200
    guide_id = guide_resp.json()["id"]

    # Try to upload a non-image file
    file_content = b"not an image"
    file = io.BytesIO(file_content)

    files = {"file": ("test.txt", file, "text/plain")}
    data = {"alt": "Invalid file"}

    resp = await editor_client.post(f"/editor/guides/{guide_id}/media/upload", files=files, data=data, headers=editor_headers)
    assert resp.status_code == 400
    assert "Only image and video files are allowed" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_multiple_media_to_guide(editor_client, editor_headers):
    """Test uploading multiple media items to a single guide"""
    import uuid
    # Create a guide
    unique_slug = f"multi-media-test-{uuid.uuid4().hex[:8]}"
    guide_payload = {
        "title": "Multi Media Test Guide",
        "slug": unique_slug,
        "body": {"blocks": [{"type": "paragraph", "text": "Test content"}]},
        "estimated_read_time": 5,
        "category_ids": []
    }
    guide_resp = await editor_client.post("/editor/guides", json=guide_payload, headers=editor_headers)
    assert guide_resp.status_code == 200
    guide_id = guide_resp.json()["id"]

    # Upload first media
    file1 = io.BytesIO(b"fake image 1")
    files1 = {"file": ("image1.jpg", file1, "image/jpeg")}
    data1 = {"alt": "First image"}
    resp1 = await editor_client.post(f"/editor/guides/{guide_id}/media/upload", files=files1, data=data1, headers=editor_headers)
    assert resp1.status_code == 200

    # Upload second media
    file2 = io.BytesIO(b"fake image 2")
    files2 = {"file": ("image2.jpg", file2, "image/jpeg")}
    data2 = {"alt": "Second image"}
    resp2 = await editor_client.post(f"/editor/guides/{guide_id}/media/upload", files=files2, data=data2, headers=editor_headers)
    assert resp2.status_code == 200

    # Get all media for guide
    resp = await editor_client.get(f"/editor/guides/{guide_id}/media", headers=editor_headers)
    assert resp.status_code == 200
    media_list = resp.json()
    assert isinstance(media_list, list)
    assert len(media_list) >= 2

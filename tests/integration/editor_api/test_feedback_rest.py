import pytest


@pytest.mark.asyncio
async def test_list_feedback(editor_client, editor_headers):
    resp = await editor_client.get("/editor/feedback", headers=editor_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_feedback_not_found(editor_client, editor_headers):
    import uuid
    fake_id = str(uuid.uuid4())
    resp = await editor_client.get(f"/editor/feedback/{fake_id}", headers=editor_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_feedback_not_found(editor_client, editor_headers):
    import uuid
    fake_id = str(uuid.uuid4())
    resp = await editor_client.delete(f"/editor/feedback/{fake_id}", headers=editor_headers)
    assert resp.status_code == 404


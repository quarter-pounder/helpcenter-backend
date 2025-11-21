import pytest


@pytest.mark.asyncio
async def test_graphql_media_via_guides(client):
    """Test that media is accessible through guide queries"""
    query = """
    query {
      guides {
        id
        title
        slug
        media {
          id
          url
          alt
          createdAt
          updatedAt
        }
      }
    }
    """
    response = await client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "guides" in data["data"]
    assert isinstance(data["data"]["guides"], list)

    # Check structure of guides with media
    for guide in data["data"]["guides"]:
        assert "id" in guide
        assert "title" in guide
        assert "slug" in guide
        assert "media" in guide
        assert isinstance(guide["media"], list)

        # Check media structure if present
        for media in guide["media"]:
            assert "id" in media
            assert "url" in media
            assert "alt" in media
            assert "createdAt" in media
            assert "updatedAt" in media


@pytest.mark.asyncio
async def test_graphql_media_urls_via_guide(client):
    """Test that media URLs are valid when accessed through guides"""
    query = """
    query ($slug: String!) {
      guide(slug: $slug) {
        id
        title
        media {
          id
          url
          alt
        }
      }
    }
    """
    variables = {"slug": "getting-started-guide"}
    response = await client.post("/graphql", json={"query": query, "variables": variables})
    assert response.status_code == 200
    data = response.json()

    if data["data"]["guide"] and data["data"]["guide"]["media"]:
        for media in data["data"]["guide"]["media"]:
            url = media["url"]
            assert url.startswith("http")
            # Should be either placeholder URL or GCS URL
            assert "placeholder.com" in url or "storage.googleapis.com" in url


@pytest.mark.asyncio
async def test_graphql_standalone_media_query_not_available(client):
    """Test that standalone media query has been removed"""
    query = """
    query {
      media {
        id
        url
      }
    }
    """
    response = await client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()

    # Should have an error indicating media query doesn't exist
    assert "errors" in data

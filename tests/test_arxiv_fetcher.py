import pytest 
from AIDaily.services.arxiv_fetcher import ArxivFetcher
from fastapi.exceptions import HTTPException



FAKE_FEED = """
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/1234.5678v1</id>
    <title>  Test Paper Title  </title>
    <link href="http://arxiv.org/abs/1234.5678v1"/>
    <link title="pdf" href="http://arxiv.org/pdf/1234.5678v1" type="application/pdf"/>
    <author><name>John Doe</name></author>
    <published>2025-08-18T12:00:00Z</published>
    <summary>  This is a test abstract.   </summary>
  </entry>
</feed>
"""

@pytest.mark.asyncio
async def test_fetch_one_paper_success(mocker):
    fetcher = ArxivFetcher()

    mock_response = mocker.Mock()
    mock_response.text = FAKE_FEED
    mock_response.raise_for_status = mocker.Mock()

    mock_get = mocker.AsyncMock(return_value=mock_response)
    mocker.patch("httpx.AsyncClient.get", mock_get)

    paper = await fetcher.fetch_one_paper()

    assert paper.title == "Test Paper Title"
    assert paper.id == "1234.5678v1"
    assert paper.authors == ["John Doe"]
    assert paper.pdf_url.startswith("https://arxiv.org/pdf/")
    assert "test abstract" in paper.summary.lower()

    mock_get.assert_called_once()
    
@pytest.mark.asyncio
async def test_fecth_one_paper_fail(mocker):
    fetcher = ArxivFetcher()
    empty_feed = "<feed xmlns='http://www.w3.org/2005/Atom'></feed>"
    mock_response = mocker.Mock()
    mock_response.text = empty_feed
    mock_response.raise_for_status = mocker.Mock()
    mock_get = mocker.AsyncMock(return_value=mock_response)
    mocker.patch("httpx.AsyncClient.get", mock_get)
    with pytest.raises(HTTPException) as e:
        await fetcher.fetch_one_paper()
    assert e.value.status_code == 404
    

@pytest.mark.asyncio
async def test_fetch_one_paper_http_error(mocker):
    fetcher = ArxivFetcher()
    mock_get = mocker.AsyncMock(side_effect=Exception("Network Error"))
    mocker.patch("httpx.AsyncClient.get", mock_get)
    with pytest.raises(HTTPException) as e:
        await fetcher.fetch_one_paper()
    assert e.value.status_code == 500
    
        

    
    
    

    
    





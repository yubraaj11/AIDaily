import pytest
from AIDaily.services.process_pdf import ProcessPDF
from fastapi.exceptions import HTTPException
import httpx


@pytest.mark.asyncio
async def test_download_pdf_success(mocker):
    fake_pdf_bytes = b"%PDF-1.4 Fake PDF content"
    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mocker.Mock(status_code=200, content=fake_pdf_bytes))

    pdf_bytes = await ProcessPDF.download_pdf("http://fake-url.com/fake.pdf")
    assert pdf_bytes == fake_pdf_bytes
    mock_get.assert_called_once()
    
@pytest.mark.asyncio
async def test_extract_text_from_pdf_page(mocker):
    fake_pdf_bytes = b"%PDF-1.4 Fake PDF content"
    processor = ProcessPDF()

    mock_page = mocker.Mock()
    mock_page.extract_text.return_value = "Hello World"
    mock_pdf_reader = mocker.Mock()
    mock_pdf_reader.pages = [mock_page]
    mocker.patch("AIDaily.services.process_pdf.PdfReader", return_value=mock_pdf_reader)

    text = processor.extract_text_from_pdf(fake_pdf_bytes)
    assert "Hello World" in text
    
@pytest.mark.asyncio
async def test_extract_text_from_pdf(mocker):
    fake_pdf_bytes = b"%PDF-1.4 Fake PDF content"
    processor = ProcessPDF()

    mock_page = mocker.Mock()
    mock_page.extract_text.return_value = "Hello World"
    mock_pdf_reader = mocker.Mock()
    mock_pdf_reader.pages = [mock_page]
    mocker.patch("AIDaily.services.process_pdf.PdfReader", return_value=mock_pdf_reader)

    text = processor.extract_text_from_pdf(fake_pdf_bytes)
    assert "Hello World" in text
    
@pytest.mark.asyncio
async def test_summarize_pdf_text(mocker):
    fake_summary = "1. Introduction: Fake summary"

    processor = ProcessPDF()
    mock_model = mocker.Mock()
    mock_model.generate_content.return_value = mocker.Mock(text=fake_summary)
    mocker.patch("google.generativeai.GenerativeModel", return_value=mock_model)

    text = "Some research paper content"
    api_key = "fake-api-key"
    result = ProcessPDF.summarize_pdf_text(text, api_key)

    assert fake_summary in result
    mock_model.generate_content.assert_called_once()
    
@pytest.mark.asyncio
async def test_download_pdf_status_error(mocker):
    class MockResponse:
        def raise_for_status(self):
            raise httpx.HTTPStatusError(
                "Bad status",
                request=httpx.Request("GET", "http://fake-url.com"),
                response=httpx.Response(500),
            )

    async def mock_get(*args, **kwargs):
        return MockResponse()

    mocker.patch("httpx.AsyncClient.get", mock_get)

    with pytest.raises(HTTPException) as exc:
        await ProcessPDF.download_pdf("http://fake-url.com")

    assert exc.value.status_code == 500
    
	
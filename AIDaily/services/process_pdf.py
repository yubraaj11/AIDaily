"""
AI Daily App - ./services/process_pdf.py
Author: Yubraj Sigdel
© 2025 Yubraj Sigdel. All rights reserved.

This file contains the ProcessPDF class, which is responsible for handling
PDF files. It provides functionality to:
    1. Download PDFs from URLs asynchronously.
    2. Extract text from PDFs (including encrypted PDFs).
    3. Summarize extracted text using the Gemini API in a structured format.

Usage:
    from AIDaily.services import ProcessPDF
    pdf_processor = ProcessPDF()
    pdf_content = await pdf_processor.download_pdf(pdf_url)
    text = pdf_processor.extract_text_from_pdf(pdf_content)
    summary = ProcessPDF.summarize_pdf_text(text, api_key)
"""

import logging
import os
import re
import tempfile
from typing import Optional

import google.generativeai as genai
import httpx
import PyPDF2
from fastapi import HTTPException

from AIDaily.configs import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class ProcessPDF:
	"""Class to handle downloading, extracting, and summarizing PDFs."""

	def __init__(self):
		pass

	@staticmethod
	async def download_pdf(pdf_url: str) -> bytes:
		"""Download a PDF file from a URL asynchronously."""
		try:
			logger.info(f'Downloading PDF from: {pdf_url}')

			async with httpx.AsyncClient(timeout=60) as client:
				response = await client.get(pdf_url)
				response.raise_for_status()
				logger.info(f'PDF downloaded successfully, size: {len(response.content)} bytes')
				return response.content

		except httpx.RequestError as e:
			logger.error(f'Request error downloading PDF: {e}')
			raise HTTPException(500, detail=f'Failed to download PDF: {str(e)}') from e
		except httpx.HTTPStatusError as e:
			logger.error(f'HTTP error downloading PDF: {e}')
			raise HTTPException(500, detail=f'Failed to download PDF: {str(e)}') from e
		except Exception as e:
			logger.error(f'Unexpected error downloading PDF: {e}')
			raise HTTPException(500, detail=f'Failed to download PDF: {str(e)}') from e

	@staticmethod
	def _extract_text_from_pdf_page(page: PyPDF2._page.PageObject, page_num: int) -> str:
		"""Extract and clean text from a single PDF page."""
		try:
			text = page.extract_text() or ''
			text = re.sub(r'\s+', ' ', text).strip()
			if not text:
				logger.warning(f'No meaningful text extracted from page {page_num}')
			return text + '\n' if text else ''
		except Exception as e:
			logger.warning(f'Error extracting text from page {page_num}: {e}')
			return ''

	def extract_text_from_pdf(self, pdf_content: bytes) -> str:
		"""Extract text from PDF bytes."""
		if not pdf_content:
			logger.warning('Empty PDF content provided')
			return ''

		temp_file_path: Optional[str] = None
		try:
			with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
				temp_file.write(pdf_content)
				temp_file_path = temp_file.name

			logger.info(f'Temporary PDF created at: {temp_file_path}')

			text = ''
			with open(temp_file_path, 'rb') as pdf_file:
				pdf_reader = PyPDF2.PdfReader(pdf_file)
				logger.info(f'PDF has {len(pdf_reader.pages)} pages')

				# Decrypt if necessary
				if pdf_reader.is_encrypted:
					if pdf_reader.decrypt(''):
						logger.info('PDF decrypted successfully with empty password')
					else:
						logger.error('Failed to decrypt PDF')
						return ''

				# Extract text page by page
				for i, page in enumerate(pdf_reader.pages):
					text += self._extract_text_from_pdf_page(page, i + 1)

			return text.strip()

		except Exception as e:
			logger.error(f'Error extracting text from PDF: {e}', exc_info=True)
			raise HTTPException(500, detail=f'Error extracting text: {str(e)}') from e
		finally:
			# Ensure temporary file is removed
			if temp_file_path and os.path.exists(temp_file_path):
				try:
					os.unlink(temp_file_path)
					logger.info(f'Deleted temporary file: {temp_file_path}')
				except Exception as cleanup_e:
					logger.warning(f'Failed to delete temporary file: {cleanup_e}')

	@staticmethod
	def summarize_pdf_text(text: str, api_key: str) -> str:
		"""Summarize PDF text using Gemini API in structured format."""
		try:
			if not api_key or not api_key.strip():
				raise ValueError('Invalid API key')

			genai.configure(api_key=api_key)
			model = genai.GenerativeModel('gemini-2.5-pro')

			# Limit text to avoid token issues
			limit = 8000
			if len(text) > limit:
				logger.info(f'Truncating text from {len(text)} to {limit} characters')
				text = text[:limit]

			prompt = f"""
Please summarize the following research paper in a structured format with these 5 sections:

1. Introduction/Core Idea
2. Methodology
3. Mathematical Equations
4. Limitations
5. Conclusion

Research Paper Text:
{text}
"""
			response = model.generate_content(prompt)
			if not response.text:
				raise Exception('Empty response from Gemini API')
			logger.info(f'Summary generated, length: {len(response.text)}')
			return response.text

		except ValueError as e:
			logger.error(f'API key error: {e}')
			raise HTTPException(400, detail=f'Invalid API key: {str(e)}') from e
		except Exception as e:
			logger.error(f'Error summarizing PDF text: {e}', exc_info=True)
			msg = str(e).lower()
			if 'api key' in msg or 'authentication' in msg:
				raise HTTPException(400, detail=f'Invalid API key: {str(e)}') from e
			elif 'quota' in msg or 'limit' in msg:
				raise HTTPException(429, detail=f'API quota exceeded: {str(e)}') from e
			elif 'safety' in msg:
				raise HTTPException(400, detail=f'Content blocked by safety filters: {str(e)}') from e
			else:
				raise HTTPException(500, detail=f'Summarization failed: {str(e)}') from e

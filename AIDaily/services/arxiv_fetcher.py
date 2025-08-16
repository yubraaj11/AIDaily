"""
AI Daily App - arxiv_fetcher
Author: Yubraj Sigdel
© 2025 Yubraj Sigdel. All rights reserved.

This file contains the ArxivFetcher class, which is responsible for fetching
research papers from the arXiv API. It selects a category, fetches recent papers,
and returns a securely chosen paper with metadata such as title, authors, PDF URL, and summary.

Usage:
    from arxiv_fetcher import ArxivFetcher
    fetcher = ArxivFetcher()
    paper = await fetcher.fetch_one_paper()
"""

import logging
import re
import secrets
from typing import Optional

import feedparser
import httpx
from fastapi.exceptions import HTTPException

from AIDaily.configs import setup_logging
from AIDaily.constants import ARXIV_API
from AIDaily.schemas import Paper
from utils import next_category

setup_logging()
logger = logging.getLogger(__name__)


class ArxivFetcher:
	"""
	Class to fetch research papers from the arXiv API.

	Example usage:
	    fetcher = ArxivFetcher()
	    paper = await fetcher.fetch_one_paper()
	"""

	def __init__(self, max_results: int = 5, timeout: int = 30):
		"""
		Initialize the ArxivFetcher.

		Args:
		    max_results: Number of recent papers to fetch for selection.
		    timeout: HTTP request timeout in seconds.
		"""
		self.max_results = max_results
		self.timeout = timeout

	async def fetch_one_paper(self) -> Paper:
		"""
		Fetch a single random paper from a chosen arXiv category.

		Returns:
		    Paper: A Paper schema object containing paper metadata.

		Raises:
		    HTTPException: If no papers are found or request fails.
		"""
		category = next_category()
		logger.info(f'Fetching papers from category: {category}')

		params = {
			'search_query': category,
			'start': 0,
			'max_results': self.max_results,
			'sortBy': 'submittedDate',
			'sortOrder': 'descending',
		}

		try:
			async with httpx.AsyncClient(timeout=self.timeout) as client:
				response = await client.get(ARXIV_API, params=params)
				response.raise_for_status()
			feed = feedparser.parse(response.text)
		except Exception as e:
			logger.error(f'Error fetching papers from arXiv: {e}')
			raise HTTPException(500, detail=f'Failed to fetch papers: {str(e)}') from e

		if not feed.entries:
			logger.warning(f'No papers found for category: {category}')
			raise HTTPException(404, detail='No papers found')

		# Choose a random paper securely
		entry = secrets.choice(feed.entries)
		pid = entry.id.split('/')[-1]

		# Find PDF URL
		pdf_url: Optional[str] = None
		for link in getattr(entry, 'links', []):
			if getattr(link, 'type', '') == 'application/pdf':
				pdf_url = link.href
				break

		if pdf_url.startswith('http'):
			pdf_url = f'https:{pdf_url.split(":")[-1]}'
		paper = Paper(
			id=pid,
			title=re.sub(r'\s+', ' ', getattr(entry, 'title', '').strip()),
			url=getattr(entry, 'link', ''),
			authors=[a.name for a in getattr(entry, 'authors', [])] if hasattr(entry, 'authors') else [],
			published=getattr(entry, 'published', ''),
			summary=re.sub(r'\s+', ' ', getattr(entry, 'summary', '').strip()) or None,
			doi=getattr(entry, 'arxiv_doi', None),
			pdf_url=pdf_url,
		)
		logger.info(f'Fetched paper: {paper.title} (ID: {paper.id})')
		return paper

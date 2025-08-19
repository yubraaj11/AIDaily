"""
AI Daily App - ./routes/v1_routes.py
Author: Yubraj Sigdel
© 2025 Yubraj Sigdel. All rights reserved.

This file contains version 1 routers for fetching, indexing and managing papers.
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException

from AIDaily.configs import setup_logging
from AIDaily.constants import PAPER_DIR
from AIDaily.schemas import Paper, PaperSummary, SummarizationRequest
from AIDaily.services import ArxivFetcher, ProcessPDF
from utils import load_index, norm, save_index

setup_logging()
logger = logging.getLogger(__name__)

v1_router = APIRouter(prefix='/ai-daily/v1', tags=['AI Daily-v1'])


@v1_router.get('/health')
async def health():
	idx = load_index()
	return {'ok': True, 'cached': len(idx)}


@v1_router.post('/fetch_store')
async def fetch_and_store():
	paper = await ArxivFetcher().fetch_one_paper()
	idx = load_index()
	if paper.id in idx:
		return {'status': 'exists', 'paper': paper}

	today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
	fname = f'{today_str}-{norm(paper.id)}.json'
	(PAPER_DIR / fname).write_text(paper.model_dump_json(indent=2))

	idx[paper.id] = paper.title
	save_index(idx)
	return {'status': 'stored', 'file': fname, 'paper': paper}


@v1_router.get('/today')
async def today_papers():
	today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
	files = [f for f in PAPER_DIR.glob(f'{today_str}-*.json')]
	papers = []
	for f in files:
		papers.append(json.loads(f.read_text()))
	return {'date': today_str, 'count': len(papers), 'papers': papers}


@v1_router.post('/summarize')
async def summarize_paper(request: SummarizationRequest):
	# Validate API key
	logger.info(f'Summarization requested for paper ID: {request.paper_id}')
	if not request.api_key or not request.api_key.strip():
		logger.warning('Summarization failed: API key is required')
		raise HTTPException(400, detail='API key is required for summarization')

	# Load the paper from storage
	logger.info(f'Loading paper from storage: {request.paper_id}')
	paper_files = list(PAPER_DIR.glob(f'*-{request.paper_id}.json'))
	if not paper_files:
		logger.warning(f'Summarization failed: Paper not found for ID {request.paper_id}')
		raise HTTPException(404, detail='Paper not found')

	paper_data = json.loads(paper_files[0].read_text())
	paper = Paper(**paper_data)
	logger.info(f'Paper loaded: {paper.title}')

	# Check if already summarized
	if 'summarized_text' in paper_data and paper_data['summarized_text']:
		logger.info(f'Paper already summarized: {request.paper_id}')
		return {'paper': paper_data}

	# Summarize the paper
	if not paper.pdf_url:
		logger.warning(f'Summarization failed: Paper has no PDF URL to process for ID {request.paper_id}')
		raise HTTPException(400, detail='Paper has no PDF URL to process')

	try:
		# Download the PDF
		logger.info(f'Downloading PDF from {paper.pdf_url}')
		pdf_content = await ProcessPDF().download_pdf(paper.pdf_url)
		logger.info(f'PDF downloaded, size: {len(pdf_content)} bytes')

		# Extract text from PDF
		logger.info('Extracting text from PDF')
		pdf_text = ProcessPDF().extract_text_from_pdf(pdf_content)
		logger.info(f'Text extracted, length: {len(pdf_text)} characters')

		if not pdf_text:
			logger.warning(f'Summarization failed: Could not extract text from PDF for ID {request.paper_id}')
			raise HTTPException(400, detail='Could not extract text from PDF')

		# Summarize the PDF text
		logger.info('Summarizing PDF text with Gemini API')
		summarized_text = ProcessPDF().summarize_pdf_text(pdf_text, request.api_key)
		logger.info(f'Summarization completed, length: {len(summarized_text)} characters')

		# Update the paper with the summary
		logger.info(f'Updating paper with summary: {request.paper_id}')
		paper_summary = PaperSummary(
			id=paper.id,
			title=paper.title,
			url=paper.url,
			authors=paper.authors,
			published=paper.published,
			summary=paper.summary,
			doi=paper.doi,
			pdf_url=paper.pdf_url,
			summarized_text=summarized_text,
		)

		# Save the updated paper
		updated_paper_data = paper_summary.model_dump()
		paper_files[0].write_text(json.dumps(updated_paper_data, indent=2))
		logger.info(f'Paper updated and saved: {request.paper_id}')

		return {'paper': updated_paper_data}
	except HTTPException:
		# Re-raise HTTP exceptions
		raise
	except Exception as e:
		# Log and raise a generic 500 error for unexpected exceptions
		logger.error(f'Unexpected error during summarization: {e}', exc_info=True)
		raise HTTPException(500, detail=f'Summarization failed: {str(e)}') from e


@v1_router.get('/paper/{paper_id}')
async def get_paper(paper_id: str):
	paper_files = list(PAPER_DIR.glob(f'*-{paper_id}.json'))
	if not paper_files:
		raise HTTPException(404, detail='Paper not found')

	paper_data = json.loads(paper_files[0].read_text())
	return {'paper': paper_data}


@v1_router.get('/history')
async def get_history(date_range: str = Query('all', pattern='^(7|30|all)$')):
	"""
	List papers grouped by date.
	date_range: '7' for last 7 days, '30' for last 30 days, 'all' for all time
	"""
	all_files = list(PAPER_DIR.glob('*.json'))
	papers_by_date = {}

	now = datetime.now()
	date_cutoff = None
	if date_range != 'all':
		date_cutoff = now - timedelta(days=int(date_range))

	for file in all_files:
		try:
			# Extract date from filename: assume format YYYY-MM-DD-<id>.json
			date_str = file.name.split('-')[0] + '-' + file.name.split('-')[1] + '-' + file.name.split('-')[2]
			file_date = datetime.strptime(date_str, '%Y-%m-%d')

			# Skip files outside the date range
			if date_cutoff and file_date < date_cutoff:
				continue

			if date_str not in papers_by_date:
				papers_by_date[date_str] = []

			paper_data = json.loads(file.read_text())
			papers_by_date[date_str].append(
				{
					'id': paper_data['id'],
					'title': paper_data['title'],
					'authors': paper_data['authors'],
					'published': paper_data['published'],
					'pdf_url': paper_data['pdf_url'],
				}
			)

		except Exception as e:
			logger.warning(f'Failed to process file {file.name}: {str(e)}')
			continue

	# Sort by date descending
	sorted_history = dict(sorted(papers_by_date.items(), reverse=True))
	return {'history': sorted_history}

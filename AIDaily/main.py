"""
AI Daily App - ./main.py
Author: Yubraj Sigdel
© 2025 Yubraj Sigdel. All rights reserved.

The main entry point for the Webapp - AI Daily.
Usage:
    uvicorn AIDaily.main:app
"""

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from AIDaily.configs import setup_logging
from AIDaily.routes import v1_router
from AIDaily.services import ArxivFetcher

setup_logging()
logger = logging.getLogger(__name__)


def background_runner():
	asyncio.run(ArxivFetcher().fetch_one_paper())


app = FastAPI(title='AI Daily (ArXiv)', description='A new AI research paper every day.')

app.add_middleware(
	CORSMiddleware,
	allow_origins=['*'],
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)

app.mount('/static', StaticFiles(directory='AIDaily/static'), name='static')

templates = Jinja2Templates(directory='AIDaily/templates')


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
	return templates.TemplateResponse('index.html', {'request': request})


app.include_router(router=v1_router)

# ----------------------
# Scheduler
# ----------------------
scheduler = BackgroundScheduler()

# Schedule job to run daily at 8:00 AM server time
scheduler.add_job(background_runner, trigger='cron', hour=8, minute=0, id='daily_paper_job', replace_existing=True)

scheduler.start()
logger.info('Scheduler started, daily fetch job added.')

"""
AI Daily App - ./schemas/paper_schemas.py
Author: Yubraj Sigdel
© 2025 Yubraj Sigdel. All rights reserved.

This file contains schema classes for papers fetched, papers summary generated from gemini api and summarization request.

Usage:
    from AIDaily.schemas import Paper, PaperSummary, SummarizationRequest
"""

from typing import List, Optional

from pydantic import BaseModel


class Paper(BaseModel):
	id: str
	title: str
	url: str
	authors: List[str]
	published: str
	summary: Optional[str] = None
	doi: Optional[str] = None
	pdf_url: Optional[str] = None


class PaperSummary(BaseModel):
	id: str
	title: str
	url: str
	authors: List[str]
	published: str
	summary: str
	doi: Optional[str] = None
	pdf_url: Optional[str] = None
	summarized_text: Optional[str] = None


class SummarizationRequest(BaseModel):
	api_key: str
	paper_id: str

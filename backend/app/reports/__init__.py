"""Structured report renderers."""

from .pdf_report import build_pdf_report
from .markdown_report import build_markdown_report

__all__ = ["build_markdown_report", "build_pdf_report"]

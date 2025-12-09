"""Retriever modules for different conference types"""

from .base_retriever import BaseRetriever
from .static_html import StaticHTMLRetriever

__all__ = ['BaseRetriever', 'StaticHTMLRetriever']

"""Retriever modules for different conference types"""

from retrievers.base_retriever import BaseRetriever
from retrievers.static_html import StaticHTMLRetriever

__all__ = ['BaseRetriever', 'StaticHTMLRetriever']

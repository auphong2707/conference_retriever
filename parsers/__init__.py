"""Parser modules for conference-specific HTML"""

from .neurips_parser import NeurIPSParser
from .icml_parser import ICMLParser
from .usenix_parser import USENIXParser

__all__ = ['NeurIPSParser', 'ICMLParser', 'USENIXParser']

"""
File I/O - Load and save .rsim files (JSON format).
"""

import json
from pathlib import Path
from typing import Dict, Any
from core.document import Document
from core.page import Page


class FileIO:
    """
    Handles loading and saving of .rsim files.
    Format: JSON with .rsim extension
    """
    
    @staticmethod
    def save_document(document: Document, filepath: str) -> Dict[str, Any]:
        """
        Save document to .rsim file.
        
        Args:
            document: Document to save
            filepath: Path to save file
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # Convert document to dict
            data = document.to_dict()
            
            # Ensure .rsim extension
            filepath = Path(filepath)
            if filepath.suffix != '.rsim':
                filepath = filepath.with_suffix('.rsim')
            
            # Create parent directories if needed
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Write JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'message': f'Document saved to {filepath}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saving document: {e}'
            }
    
    @staticmethod
    def load_document(filepath: str) -> Dict[str, Any]:
        """
        Load document from .rsim file.
        
        Args:
            filepath: Path to .rsim file
            
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'document': Document or None
            }
        """
        try:
            filepath = Path(filepath)
            
            # Check file exists
            if not filepath.exists():
                return {
                    'success': False,
                    'message': f'File not found: {filepath}',
                    'document': None
                }
            
            # Read JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate basic structure
            if 'metadata' not in data or 'pages' not in data:
                return {
                    'success': False,
                    'message': 'Invalid .rsim file format',
                    'document': None
                }
            
            # Create document from data
            document = Document.from_dict(data)
            
            # Validate IDs
            is_valid, duplicates = document.validate_ids()
            if not is_valid:
                return {
                    'success': False,
                    'message': f'Document has duplicate IDs: {duplicates}',
                    'document': None
                }
            
            return {
                'success': True,
                'message': f'Document loaded from {filepath}',
                'document': document
            }
            
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'message': f'Invalid JSON in file: {e}',
                'document': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error loading document: {e}',
                'document': None
            }
    
    @staticmethod
    def create_empty_document() -> Document:
        """
        Create a new empty document with one default page.
        
        Returns:
            Document: New document
        """
        doc = Document()
        doc.metadata['version'] = '1.0'
        doc.create_page("Page 1")
        return doc

"""
ID Manager - UUID generation and validation for all simulator objects.
All IDs are 8-character truncated UUIDs.
"""

import uuid
from typing import Set, Optional, Tuple


class IDManager:
    """
    Manages ID generation and validation for the simulator.
    
    All IDs are 8-character truncated UUIDs.
    Hierarchical format: PageId.ComponentId.PinId.TabId
    """
    
    def __init__(self):
        """Initialize ID manager"""
        self._used_ids: Set[str] = set()
    
    def generate_id(self) -> str:
        """
        Generate a new unique 8-character ID.
        
        Returns:
            str: 8-character UUID (first 8 chars of UUID4)
        """
        while True:
            new_id = str(uuid.uuid4())[:8]
            if new_id not in self._used_ids:
                self._used_ids.add(new_id)
                return new_id
    
    def register_id(self, id_str: str) -> bool:
        """
        Register an existing ID (from file load).
        
        Args:
            id_str: ID to register
            
        Returns:
            bool: True if registered, False if duplicate
        """
        if id_str in self._used_ids:
            return False
        self._used_ids.add(id_str)
        return True
    
    def is_id_used(self, id_str: str) -> bool:
        """
        Check if an ID is already in use.
        
        Args:
            id_str: ID to check
            
        Returns:
            bool: True if ID is used
        """
        return id_str in self._used_ids
    
    def release_id(self, id_str: str):
        """
        Release an ID (e.g., when deleting object).
        
        Args:
            id_str: ID to release
        """
        self._used_ids.discard(id_str)
    
    def clear(self):
        """Clear all registered IDs"""
        self._used_ids.clear()
    
    def get_used_count(self) -> int:
        """
        Get count of used IDs.
        
        Returns:
            int: Number of registered IDs
        """
        return len(self._used_ids)
    
    @staticmethod
    def parse_hierarchical_id(hierarchical_id: str) -> Tuple[str, ...]:
        """
        Parse a hierarchical ID into components.
        
        Args:
            hierarchical_id: Dot-separated ID (e.g., "page.comp.pin.tab")
            
        Returns:
            tuple: ID components
            
        Examples:
            >>> IDManager.parse_hierarchical_id("12345678.abcdef12.99887766.55443322")
            ('12345678', 'abcdef12', '99887766', '55443322')
        """
        return tuple(hierarchical_id.split('.'))
    
    @staticmethod
    def build_hierarchical_id(*components: str) -> str:
        """
        Build a hierarchical ID from components.
        
        Args:
            *components: ID components
            
        Returns:
            str: Dot-separated ID
            
        Examples:
            >>> IDManager.build_hierarchical_id("12345678", "abcdef12")
            '12345678.abcdef12'
        """
        return '.'.join(components)
    
    @staticmethod
    def get_page_id(hierarchical_id: str) -> str:
        """
        Extract page ID from hierarchical ID.
        
        Args:
            hierarchical_id: Full hierarchical ID
            
        Returns:
            str: Page ID (first component)
            
        Examples:
            >>> IDManager.get_page_id("12345678.abcdef12.99887766")
            '12345678'
        """
        return hierarchical_id.split('.')[0]
    
    @staticmethod
    def replace_page_id(hierarchical_id: str, new_page_id: str) -> str:
        """
        Replace page ID in hierarchical ID (used for cut/paste to different page).
        
        Args:
            hierarchical_id: Original ID
            new_page_id: New page ID to use
            
        Returns:
            str: ID with replaced page ID
            
        Examples:
            >>> IDManager.replace_page_id("12345678.abcdef12.99887766", "aaaaaaaa")
            'aaaaaaaa.abcdef12.99887766'
        """
        parts = hierarchical_id.split('.')
        parts[0] = new_page_id
        return '.'.join(parts)
    
    def validate_document_ids(self, document) -> Tuple[bool, list]:
        """
        Validate all IDs in a document for uniqueness.
        
        Args:
            document: Document instance to validate
            
        Returns:
            tuple: (is_valid, list_of_duplicate_ids)
        """
        seen_ids = set()
        duplicates = []
        
        # Would iterate through document structure
        # For now, just a placeholder
        
        return len(duplicates) == 0, duplicates

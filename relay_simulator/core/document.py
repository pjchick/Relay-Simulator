"""
Document class - Represents a complete .rsim file with multiple pages.
"""

from typing import Dict, List, Optional
from core.page import Page
from core.id_manager import IDManager


class Document:
    """
    Document represents a complete .rsim simulation file.
    Contains multiple pages, metadata, and manages global ID registry.
    """
    
    def __init__(self):
        """Initialize document"""
        self.metadata = {
            'version': '1.0',
            'author': '',
            'created': '',
            'modified': '',
            'description': ''
        }
        self.pages: Dict[str, Page] = {}
        self.id_manager = IDManager()
    
    # === Page Management ===
    
    def add_page(self, page: Page) -> bool:
        """
        Add a page to document.
        
        Args:
            page: Page instance
            
        Returns:
            bool: True if added, False if page_id already exists
        """
        if page.page_id in self.pages:
            return False
        
        self.pages[page.page_id] = page
        self.id_manager.register_id(page.page_id)
        return True
    
    def create_page(self, name: str = "Untitled") -> Page:
        """
        Create and add a new page with generated ID.
        
        Args:
            name: Page name
            
        Returns:
            Page: Newly created page
        """
        page_id = self.id_manager.generate_id()
        page = Page(page_id, name)
        self.add_page(page)
        return page
    
    def remove_page(self, page_id: str) -> Optional[Page]:
        """
        Remove a page from document.
        
        Args:
            page_id: Page ID to remove
            
        Returns:
            Page: Removed page or None
        """
        page = self.pages.pop(page_id, None)
        if page:
            self.id_manager.release_id(page_id)
        return page
    
    def get_page(self, page_id: str) -> Optional[Page]:
        """
        Get page by ID.
        
        Args:
            page_id: Page ID
            
        Returns:
            Page: Page instance or None
        """
        return self.pages.get(page_id)
    
    def get_all_pages(self) -> List[Page]:
        """
        Get all pages in document.
        
        Returns:
            list: List of pages
        """
        return list(self.pages.values())
    
    def get_page_count(self) -> int:
        """
        Get number of pages.
        
        Returns:
            int: Page count
        """
        return len(self.pages)
    
    # === Component Queries ===
    
    def get_component(self, component_id: str) -> Optional['Component']:
        """
        Get component by ID (searches all pages).
        
        Args:
            component_id: Component ID (may include page ID prefix)
            
        Returns:
            Component: Component instance or None
        """
        # Try to extract page ID from component ID
        page_id = IDManager.get_page_id(component_id)
        
        if page_id in self.pages:
            return self.pages[page_id].get_component(component_id)
        
        # If not found, search all pages
        for page in self.pages.values():
            comp = page.get_component(component_id)
            if comp:
                return comp
        
        return None
    
    def get_all_components(self) -> List['Component']:
        """
        Get all components from all pages.
        
        Returns:
            list: List of all components
        """
        components = []
        for page in self.pages.values():
            components.extend(page.get_all_components())
        return components
    
    def get_components_with_link_name(self, link_name: str) -> List['Component']:
        """
        Get all components with a specific link name.
        Used for cross-page connections.
        
        Args:
            link_name: Link name to search for
            
        Returns:
            list: List of components with that link name
        """
        result = []
        for component in self.get_all_components():
            if component.link_name == link_name:
                result.append(component)
        return result
    
    # === Validation ===
    
    def validate_ids(self) -> tuple:
        """
        Validate all IDs in document for uniqueness.
        
        Returns:
            tuple: (is_valid, list_of_duplicate_ids)
        """
        seen_ids = set()
        duplicates = []
        
        # Check page IDs
        for page_id in self.pages.keys():
            if page_id in seen_ids:
                duplicates.append(page_id)
            seen_ids.add(page_id)
        
        # Check component IDs
        for page in self.pages.values():
            for comp in page.get_all_components():
                if comp.component_id in seen_ids:
                    duplicates.append(comp.component_id)
                seen_ids.add(comp.component_id)
                
                # Check pin IDs
                for pin in comp.pins.values():
                    if pin.pin_id in seen_ids:
                        duplicates.append(pin.pin_id)
                    seen_ids.add(pin.pin_id)
                    
                    # Check tab IDs
                    for tab in pin.tabs.values():
                        if tab.tab_id in seen_ids:
                            duplicates.append(tab.tab_id)
                        seen_ids.add(tab.tab_id)
        
        return len(duplicates) == 0, duplicates
    
    # === Serialization ===
    
    def to_dict(self) -> dict:
        """
        Serialize document to dict for saving.
        
        Returns:
            dict: Document data
        """
        return {
            'metadata': self.metadata,
            'pages': {
                page_id: page.to_dict() 
                for page_id, page in self.pages.items()
            }
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Document':
        """
        Deserialize document from dict.
        
        Args:
            data: Document data dict
            
        Returns:
            Document: Reconstructed document
        """
        doc = Document()
        doc.metadata = data.get('metadata', {})
        
        # Load pages
        for page_data in data.get('pages', {}).values():
            page = Page.from_dict(page_data)
            doc.add_page(page)
        
        return doc
    
    def __repr__(self):
        return f"Document(pages={len(self.pages)}, components={len(self.get_all_components())})"

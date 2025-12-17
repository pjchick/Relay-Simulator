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
        # Explicit page ordering (tab order). This is the source of truth for
        # get_all_pages() and serialization order.
        self.page_order: List[str] = []
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
        if page.page_id not in self.page_order:
            self.page_order.append(page.page_id)
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
            try:
                self.page_order.remove(page_id)
            except ValueError:
                pass
            self.id_manager.release_id(page_id)
        return page

    # Backwards-compatible alias used by the GUI.
    def delete_page(self, page_id: str) -> Optional[Page]:
        return self.remove_page(page_id)
    
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
        ordered: List[Page] = []

        # Primary: explicit order list.
        for page_id in self.page_order:
            page = self.pages.get(page_id)
            if page is not None:
                ordered.append(page)

        # Defensive: append any pages missing from page_order.
        for page_id, page in self.pages.items():
            if page_id not in self.page_order:
                ordered.append(page)

        return ordered

    def move_page(self, page_id: str, new_index: int) -> bool:
        """Move a page to a new index in the page_order list."""
        if page_id not in self.pages:
            return False

        if page_id not in self.page_order:
            self.page_order.append(page_id)

        try:
            old_index = self.page_order.index(page_id)
        except ValueError:
            old_index = None

        if old_index is None:
            return False

        new_index = int(new_index)
        if new_index < 0:
            new_index = 0
        if new_index >= len(self.page_order):
            new_index = len(self.page_order) - 1

        if old_index == new_index:
            return True

        self.page_order.pop(old_index)
        self.page_order.insert(new_index, page_id)
        return True

    def reorder_pages(self, ordered_page_ids: List[str]) -> bool:
        """Replace page_order with the provided ordered list (validated)."""
        if not isinstance(ordered_page_ids, list):
            return False

        # Keep only valid page IDs, in provided order.
        new_order: List[str] = []
        seen = set()
        for pid in ordered_page_ids:
            if not isinstance(pid, str):
                continue
            if pid in seen:
                continue
            if pid not in self.pages:
                continue
            new_order.append(pid)
            seen.add(pid)

        # Append any missing pages (defensive).
        for pid in self.pages.keys():
            if pid not in seen:
                new_order.append(pid)
                seen.add(pid)

        self.page_order = new_order
        return True
    
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
        Serialize document to dict for saving (matches .rsim schema).
        
        Returns:
            dict: Document data
        """
        from fileio.rsim_schema import SchemaVersion
        
        result = {
            'version': SchemaVersion.to_string(),
            'pages': [page.to_dict() for page in self.get_all_pages()]
        }
        
        # Optional metadata (only include if not empty)
        if self.metadata:
            result['metadata'] = self.metadata.copy()
        
        return result
    
    @staticmethod
    def from_dict(data: dict, component_factory=None) -> 'Document':
        """
        Deserialize document from dict (matches .rsim schema).
        
        Args:
            data: Document data dict
            component_factory: ComponentFactory instance for creating components
            
        Returns:
            Document: Reconstructed document with all pages, components, and wires
        """
        from fileio.rsim_schema import SchemaVersion
        
        # Validate version compatibility
        file_version = data.get('version', '1.0.0')
        if not SchemaVersion.is_compatible(file_version):
            raise ValueError(
                f"Incompatible file version {file_version}. "
                f"Expected version {SchemaVersion.to_string()}."
            )
        
        doc = Document()
        doc.metadata = data.get('metadata', {})
        
        # Load pages (array in schema) with component factory
        for page_data in data.get('pages', []):
            page = Page.from_dict(page_data, component_factory)
            doc.add_page(page)

        # Ensure page_order is consistent even if older code mutated pages.
        doc.reorder_pages(doc.page_order)
        
        return doc
    
    def __repr__(self):
        return f"Document(pages={len(self.pages)}, components={len(self.get_all_components())})"

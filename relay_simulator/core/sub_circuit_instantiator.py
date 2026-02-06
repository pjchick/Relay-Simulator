"""
Sub-Circuit Instantiator - Create instances from templates.

This module handles the complex orchestration of:
1. Loading .rsub template
2. Embedding definition in document
3. Creating instance with cloned pages
4. Building SubCircuit component with pins from FOOTPRINT
5. Calculating bounding box from FOOTPRINT
"""

from typing import Optional, Tuple, List, Dict
from pathlib import Path

from core.document import Document, SubCircuitDefinition, SubCircuitInstance
from core.page import Page
from core.id_regenerator import PageCloner, IDMapper
from fileio.sub_circuit_loader import SubCircuitLoader, SubCircuitTemplate
from components.sub_circuit import SubCircuit
from components.factory import ComponentFactory


class SubCircuitInstantiator:
    """
    Orchestrates sub-circuit instantiation.
    
    Workflow:
    1. Load template from .rsub file (or use existing definition)
    2. Embed definition in document (if not already embedded)
    3. Create instance with cloned pages
    4. Build SubCircuit component from FOOTPRINT
    5. Add to target page
    """
    
    def __init__(self, document: Document, component_factory: Optional[ComponentFactory] = None):
        """
        Initialize instantiator.
        
        Args:
            document: Target document
            component_factory: ComponentFactory for creating components
        """
        self.document = document
        self.component_factory = component_factory or ComponentFactory()
        self.loader = SubCircuitLoader(self.component_factory)
    
    def load_and_embed_template(self, rsub_filepath: str) -> SubCircuitDefinition:
        """
        Load .rsub template and embed as definition in document.
        
        Args:
            rsub_filepath: Path to .rsub file
            
        Returns:
            SubCircuitDefinition: Embedded definition
            
        Raises:
            FileNotFoundError: If file not found
            ValueError: If template invalid
        """
        # Load template
        template = self.loader.load_from_file(rsub_filepath)
        
        # Create definition from template
        sub_circuit_id = self.document.id_manager.generate_id()
        sc_def = SubCircuitDefinition(sub_circuit_id, template.name)
        sc_def.source_file = template.source_file
        
        # Convert template pages to Page objects
        for page_data in template.pages:
            page = Page.from_dict(page_data, self.component_factory)
            sc_def.template_pages.append(page)
        
        # Embed in document
        if not self.document.add_sub_circuit_definition(sc_def):
            raise ValueError(f"Sub-circuit definition with ID {sub_circuit_id} already exists")
        
        return sc_def
    
    def create_instance(
        self,
        sub_circuit_id: str,
        parent_page_id: str,
        position: Tuple[float, float]
    ) -> SubCircuit:
        """
        Create a new instance of a sub-circuit.
        
        Args:
            sub_circuit_id: ID of embedded sub-circuit definition
            parent_page_id: Page where SubCircuit component will be placed
            position: (x, y) position on parent page
            
        Returns:
            SubCircuit: Created component (not yet added to page)
            
        Raises:
            ValueError: If sub_circuit_id not found or parent page invalid
        """
        # Get definition
        sc_def = self.document.get_sub_circuit_definition(sub_circuit_id)
        if not sc_def:
            raise ValueError(f"Sub-circuit definition {sub_circuit_id} not found")
        
        # Validate parent page exists
        parent_page = self.document.get_page(parent_page_id)
        if not parent_page:
            raise ValueError(f"Parent page {parent_page_id} not found")
        
        # Generate instance ID
        instance_id = self.document.id_manager.generate_id()
        
        # Clone template pages with new IDs
        cloner = PageCloner(self.component_factory, self.document.id_manager)
        cloned_pages, id_mapper = cloner.clone_pages(sc_def.template_pages)
        
        # Mark cloned pages as instance pages
        for page in cloned_pages:
            page.is_sub_circuit_page = True
            page.parent_instance_id = instance_id
            page.parent_sub_circuit_id = sub_circuit_id
        
        # Build page ID map (template -> instance)
        page_id_map = {}
        for i, template_page in enumerate(sc_def.template_pages):
            page_id_map[template_page.page_id] = cloned_pages[i].page_id
        
        # Create instance record
        component_id = self.document.id_manager.generate_id()
        instance = SubCircuitInstance(instance_id, parent_page_id, component_id)
        instance.page_id_map = page_id_map
        
        # Add instance to definition
        sc_def.instances[instance_id] = instance
        
        # Add cloned pages to document
        for page in cloned_pages:
            self.document.add_page(page)
        
        # Build SubCircuit component from FOOTPRINT
        sub_circuit_comp = self._build_component_from_footprint(
            sc_def, instance, component_id, parent_page_id, position, id_mapper
        )
        
        return sub_circuit_comp
    
    def _build_component_from_footprint(
        self,
        sc_def: SubCircuitDefinition,
        instance: SubCircuitInstance,
        component_id: str,
        parent_page_id: str,
        position: Tuple[float, float],
        id_mapper: IDMapper
    ) -> SubCircuit:
        """
        Build SubCircuit component from FOOTPRINT page.
        
        Extracts Link components as interface, calculates bounding box.
        
        Args:
            sc_def: Sub-circuit definition
            instance: Instance record
            component_id: Component ID for new SubCircuit
            parent_page_id: Parent page ID
            position: Component position
            id_mapper: ID mapper from cloning
            
        Returns:
            SubCircuit: Built component
        """
        # Find FOOTPRINT page in template
        footprint_page = None
        for page in sc_def.template_pages:
            if page.name == "FOOTPRINT":
                footprint_page = page
                break
        
        if not footprint_page:
            raise ValueError(f"Sub-circuit {sc_def.name} has no FOOTPRINT page")
        
        # Create SubCircuit component
        sub_circuit = SubCircuit(component_id, parent_page_id)
        sub_circuit.position = position
        sub_circuit.sub_circuit_id = sc_def.sub_circuit_id
        sub_circuit.instance_id = instance.instance_id
        sub_circuit.sub_circuit_name = sc_def.name
        
        # Set document reference for bridge creation during simulation
        sub_circuit._document = self.document
        
        # Extract Links from FOOTPRINT
        links = []
        for comp in footprint_page.components.values():
            if comp.component_type == "Link" and comp.link_name:
                links.append(comp)
        
        # Calculate bounding box from FOOTPRINT components
        bbox = self._calculate_bounding_box(footprint_page)
        sub_circuit.width = bbox['width']
        sub_circuit.height = bbox['height']
        
        # Calculate center of FOOTPRINT bounding box
        bbox_center_x = (bbox['min_x'] + bbox['max_x']) / 2
        bbox_center_y = (bbox['min_y'] + bbox['max_y']) / 2
        
        # Build pins from Links
        for link in links:
            # Link position is on FOOTPRINT page
            link_pos = link.position
            
            # Calculate tab position relative to bounding box center
            # This makes tabs align correctly with the SubCircuit visual outline
            relative_pos = (
                link_pos[0] - bbox_center_x,
                link_pos[1] - bbox_center_y
            )
            
            sub_circuit.add_pin_from_link(
                link.link_name,
                relative_pos,
                link.rotation
            )
            
            # Store mapping to instance Link for bridge creation
            # Find corresponding cloned Link in instance FOOTPRINT
            instance_footprint_id = instance.page_id_map.get(footprint_page.page_id)
            if instance_footprint_id:
                # Map template link ID to instance link ID
                instance_link_id = id_mapper.get_mapped_id(link.component_id)
                if instance_link_id:
                    # Store mapping for later bridge resolution
                    pin_id = f"{component_id}.{link.link_name}"
                    sub_circuit.set_pin_link_mapping(pin_id, instance_link_id)
        
        return sub_circuit
    
    def _calculate_bounding_box(self, page: Page) -> Dict[str, float]:
        """
        Calculate bounding box of all components on a page.
        
        Args:
            page: Page to calculate bounds for
            
        Returns:
            dict: {'width', 'height', 'min_x', 'min_y', 'max_x', 'max_y'}
        """
        if not page.components:
            return {'width': 100, 'height': 100, 'min_x': 0, 'min_y': 0, 'max_x': 100, 'max_y': 100}
        
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for comp in page.components.values():
            x, y = comp.position
            
            # Estimate component size (rough approximation)
            # Different components have different sizes
            comp_width = 40  # Default
            comp_height = 40
            
            if comp.component_type == "Box":
                comp_width = comp.properties.get('width', 100)
                comp_height = comp.properties.get('height', 100)
            elif comp.component_type == "Link":
                comp_width = 30
                comp_height = 10
            elif comp.component_type == "DPDTRelay":
                comp_width = 60
                comp_height = 160
            
            # Update bounds
            min_x = min(min_x, x - comp_width / 2)
            min_y = min(min_y, y - comp_height / 2)
            max_x = max(max_x, x + comp_width / 2)
            max_y = max(max_y, y + comp_height / 2)
        
        return {
            'width': max_x - min_x,
            'height': max_y - min_y,
            'min_x': min_x,
            'min_y': min_y,
            'max_x': max_x,
            'max_y': max_y
        }

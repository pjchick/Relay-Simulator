"""SubCircuit Component.

A SubCircuit is a composite component that encapsulates multiple pages of circuitry
from a .rsub template file. Each instance creates its own isolated copy of the
sub-circuit's pages.

Design:
- Each instance has a unique instance_id and references a sub_circuit_id in the document
- Pins/tabs are dynamically generated from the FOOTPRINT page's Link components
- During simulation, creates bridges between external tabs and internal Link tabs
- All internal pages participate in normal VNET/component simulation

Architecture:
- SubCircuit component appears on main page canvas
- Document.sub_circuits contains embedded sub-circuit definitions
- Each definition has multiple instances, each with its own page copies
"""

from __future__ import annotations

from typing import Any, Dict, Optional, List

from components.base import Component
from core.pin import Pin
from core.tab import Tab
from core.state import PinState


class SubCircuit(Component):
    """SubCircuit component - encapsulates embedded circuit pages."""

    component_type = "SubCircuit"

    def __init__(self, component_id: str, page_id: str):
        super().__init__(component_id, page_id)

        # Reference to sub-circuit definition in Document.sub_circuits
        self.sub_circuit_id: Optional[str] = None
        
        # Unique identifier for this instance
        self.instance_id: Optional[str] = None
        
        # Name of the sub-circuit (from template)
        self.sub_circuit_name: str = ""
        
        # Visual representation size (from FOOTPRINT bounding box)
        self.width: int = 100
        self.height: int = 100
        
        # Bridges created during simulation (external_tab_id -> internal_tab_id)
        self._active_bridges: List[tuple] = []
        
        # Pin to instance Link mapping (pin_id -> instance_link_id)
        self._pin_to_link_map: Dict[str, str] = {}
        
        # Document reference (set by instantiator, needed for bridge creation)
        self._document = None

    def simulate_logic(self, vnet_manager, bridge_manager=None):
        """
        SubCircuit is passive - it only creates bridges.
        Internal components handle their own logic.
        """
        pass

    def sim_start(self, vnet_manager, bridge_manager=None):
        """
        Initialize sub-circuit for simulation.
        
        Creates bridges between external tabs (on this component) and
        internal tabs (on FOOTPRINT Links in the instance's pages).
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance for creating bridges
        """
        if not bridge_manager:
            return
        
        # Clear any previous bridges
        self._active_bridges.clear()
        
        # Initialize all pins to FLOAT
        for pin in self.pins.values():
            pin.set_state(PinState.FLOAT)
        
        # Mark tabs dirty
        for pin in self.pins.values():
            for tab in pin.tabs.values():
                try:
                    vnet_manager.mark_tab_dirty(tab.tab_id)
                except Exception:
                    pass
        
        # Create bridges if we have document access
        if not self._document:
            # Document not set - bridges cannot be created
            return
        
        # Create bridges for each pin to its corresponding instance Link
        for pin_id, instance_link_id in self._pin_to_link_map.items():
            # Find the instance Link component
            instance_link = self._document.get_component(instance_link_id)
            if not instance_link:
                continue
            
            # Get external tab (from this SubCircuit component)
            external_pin = self.pins.get(pin_id)
            if not external_pin or not external_pin.tabs:
                continue
            
            # SubCircuit pins should have exactly one tab
            external_tab_id = list(external_pin.tabs.keys())[0]
            
            # Get internal tab (from FOOTPRINT Link)
            if not instance_link.pins:
                continue
            
            # Link components have one pin with one tab
            internal_pin = list(instance_link.pins.values())[0]
            if not internal_pin.tabs:
                continue
            
            internal_tab_id = list(internal_pin.tabs.keys())[0]
            
            # Create bidirectional bridge
            # CRITICAL: BridgeManager.create_bridge requires VNET IDs, not tab IDs!
            # We need to look up which VNETs these tabs belong to            
            try:
                # Get VNETs for the tabs
                external_vnet = vnet_manager.get_vnet_for_tab(external_tab_id)
                internal_vnet = vnet_manager.get_vnet_for_tab(internal_tab_id)
                
                if not external_vnet or not internal_vnet:
                    print(f"ERROR: Could not find VNETs for tabs {external_tab_id} / {internal_tab_id}")
                    continue
                
                # Create bridge between the two VNETs
                bridge_id = bridge_manager.create_bridge(
                    external_vnet.vnet_id,
                    internal_vnet.vnet_id,
                    self.component_id  # Component creating the bridge
                )
                
                self._active_bridges.append((external_tab_id, internal_tab_id, bridge_id))
            except Exception:
                # Bridge creation failed - skip this pin
                pass
        
        # Now create bridges between FOOTPRINT Links and internal Links with matching link_names
        # This connects the FOOTPRINT page to the internal logic pages
        self._create_link_name_bridges(vnet_manager, bridge_manager)

    def _create_link_name_bridges(self, vnet_manager, bridge_manager):
        """
        Create bridges between FOOTPRINT Links and internal Links with matching link_names.
        
        This enables signal propagation from the FOOTPRINT page (connected to SubCircuit pins)
        to the internal logic pages.
        
        Args:
            vnet_manager: VnetManager instance
            bridge_manager: BridgeManager instance
        """
        if not self._document or not self.instance_id:
            return
        
        # Find the FOOTPRINT page for this instance
        footprint_page = None
        internal_pages = []
        
        for page in self._document.pages.values():
            if not page.is_sub_circuit_page:
                continue
            if not page.parent_instance_id == self.instance_id:
                continue
            
            if page.name == "FOOTPRINT":
                footprint_page = page
            else:
                internal_pages.append(page)
        
        if not footprint_page or not internal_pages:
            return
        
        # Collect all Link components from FOOTPRINT page with their link_names
        footprint_links = {}  # link_name -> Link component
        for component in footprint_page.get_all_components():
            if component.component_type == "Link" and hasattr(component, 'link_name') and component.link_name:
                footprint_links[component.link_name] = component
        
        # Collect all Link components from internal pages with their link_names
        internal_links = {}  # link_name -> Link component
        for page in internal_pages:
            for component in page.get_all_components():
                if component.component_type == "Link" and hasattr(component, 'link_name') and component.link_name:
                    internal_links[component.link_name] = component
        
        # Create bridges between matching link_names
        for link_name, footprint_link in footprint_links.items():
            internal_link = internal_links.get(link_name)
            if not internal_link:
                continue
            
            # Get tabs from both Links
            if not footprint_link.pins or not internal_link.pins:
                continue
            
            footprint_pin = list(footprint_link.pins.values())[0]
            internal_pin = list(internal_link.pins.values())[0]
            
            if not footprint_pin.tabs or not internal_pin.tabs:
                continue
            
            footprint_tab_id = list(footprint_pin.tabs.keys())[0]
            internal_tab_id = list(internal_pin.tabs.keys())[0]
            
            # Get VNETs for the tabs
            try:
                footprint_vnet = vnet_manager.get_vnet_for_tab(footprint_tab_id)
                internal_vnet = vnet_manager.get_vnet_for_tab(internal_tab_id)
                
                if not footprint_vnet or not internal_vnet:
                    continue
                
                # Create bridge between the two VNETs
                bridge_id = bridge_manager.create_bridge(
                    footprint_vnet.vnet_id,
                    internal_vnet.vnet_id,
                    self.component_id  # Component creating the bridge
                )
                
                self._active_bridges.append((footprint_tab_id, internal_tab_id, bridge_id))
            except Exception:
                # Bridge creation failed - skip this link
                pass

    def sim_stop(self):
        """Clean up simulation state. Bridges removed automatically by engine."""
        self._active_bridges.clear()

    def render(self, canvas_adapter, x_offset=0, y_offset=0):
        """Render handled by dedicated renderer in GUI layer."""
        pass

    def add_pin_from_link(self, link_name: str, link_position: tuple, link_rotation: int = 0):
        """
        Create a pin and tab based on a Link from the FOOTPRINT page.
        
        Called during instantiation to build the component's interface.
        
        Args:
            link_name: Name of the link (acts as pin identifier)
            link_position: (x, y) position relative to component center
            link_rotation: Rotation of the Link (0/90/180/270)
        """
        # Create unique pin ID
        pin_id = f"{self.component_id}.{link_name}"
        pin = Pin(pin_id, self)
        
        # Create tab at relative position
        # Position is already calculated relative to component center in instantiator
        tab_id = f"{pin_id}.tab1"
        tab = Tab(tab_id, pin, link_position)
        pin.add_tab(tab)
        
        self.add_pin(pin)
    
    def set_pin_link_mapping(self, pin_id: str, instance_link_id: str):
        """
        Store mapping from pin to instance Link component.
        
        Args:
            pin_id: Pin ID on this SubCircuit
            instance_link_id: Component ID of corresponding Link in instance FOOTPRINT
        """
        self._pin_to_link_map[pin_id] = instance_link_id

    def get_internal_link_tab_id(self, external_pin_id: str, document) -> Optional[str]:
        """
        Resolve external pin to internal FOOTPRINT Link tab.
        
        This will be used during sim_start to create bridges.
        Returns the tab_id of the corresponding Link on the instance's FOOTPRINT page.
        
        Args:
            external_pin_id: Pin ID on this SubCircuit component
            document: Document containing sub_circuits structure
            
        Returns:
            str: Internal Link tab_id or None if not found
        """
        # Implementation deferred to Phase 3 (requires Document.sub_circuits structure)
        return None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubCircuit":
        """
        Deserialize SubCircuit from file data.
        
        Args:
            data: Component data dictionary
            
        Returns:
            SubCircuit: Reconstructed component
        """
        sc = cls(data["component_id"], data.get("page_id", "page001"))

        # Position and rotation
        pos = data.get("position", {"x": 0, "y": 0})
        sc.position = (pos.get("x", 0), pos.get("y", 0))
        sc.rotation = int(data.get("rotation", 0) or 0)

        # SubCircuit-specific fields
        if "properties" in data and isinstance(data["properties"], dict):
            props = data["properties"]
            sc.sub_circuit_id = props.get("sub_circuit_id")
            sc.instance_id = props.get("instance_id")
            sc.sub_circuit_name = props.get("sub_circuit_name", "")
            sc.width = props.get("width", 100)
            sc.height = props.get("height", 100)
            
            # Store all properties
            sc.properties.update(props)

        # Load pins and tabs from data (critical for wire connections)
        if "pins" in data:
            # Clear any default pins
            sc.pins.clear()
            
            # Recreate pins from saved data
            from core.pin import Pin
            from core.tab import Tab
            
            for pin_data in data["pins"]:
                pin = Pin(pin_data["pin_id"], sc)
                
                # Restore tabs
                if "tabs" in pin_data:
                    for tab_data in pin_data["tabs"]:
                        # Position is {x, y} in schema
                        pos_data = tab_data.get("position", {"x": 0, "y": 0})
                        tab_pos = (pos_data.get("x", 0), pos_data.get("y", 0))
                        
                        # Create Tab with required relative_position argument
                        tab = Tab(tab_data["tab_id"], pin, tab_pos)
                        
                        pin.add_tab(tab)
                
                sc.pins[pin.pin_id] = pin
        
        return sc

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize SubCircuit to file data.
        
        Returns:
            dict: Component data matching schema
        """
        # Store SubCircuit-specific data in properties
        self.properties = self.properties or {}
        self.properties["sub_circuit_id"] = self.sub_circuit_id
        self.properties["instance_id"] = self.instance_id
        self.properties["sub_circuit_name"] = self.sub_circuit_name
        self.properties["width"] = self.width
        self.properties["height"] = self.height
        
        # Use base class serialization
        return super().to_dict()

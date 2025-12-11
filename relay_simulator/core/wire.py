"""
Wire Structure Classes for Relay Logic Simulator

This module defines the wire structure hierarchy:
- Waypoint: Position point along a wire path
- Junction: Connection point where wires split/merge
- Wire: Connection between tabs with waypoints and junctions
"""

from typing import Optional, List, Dict, Tuple


class Waypoint:
    """
    A position point along a wire path.
    
    Waypoints define the routing of a wire between its start and end points,
    allowing wires to be drawn with specific paths rather than straight lines.
    """
    
    def __init__(self, waypoint_id: str, position: Tuple[int, int]):
        """
        Initialize a Waypoint.
        
        Args:
            waypoint_id: Unique 8-character identifier for this waypoint
            position: (X, Y) coordinates on the page
        """
        self.waypoint_id = waypoint_id
        self.position = position
    
    def to_dict(self) -> dict:
        """
        Serialize waypoint to dictionary (matches .rsim schema).
        
        Returns:
            Dictionary representation of waypoint
        """
        return {
            'waypoint_id': self.waypoint_id,
            'position': {
                'x': self.position[0],
                'y': self.position[1]
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Waypoint':
        """
        Deserialize waypoint from dictionary (matches .rsim schema).
        
        Args:
            data: Dictionary containing waypoint data
            
        Returns:
            New Waypoint instance
        """
        position = data['position']
        return cls(
            waypoint_id=data['waypoint_id'],
            position=(position['x'], position['y'])
        )
    
    def __repr__(self):
        return f"Waypoint({self.waypoint_id} at {self.position})"


class Junction:
    """
    A connection point where wires split or merge.
    
    Junctions allow complex wire networks where a single wire can branch
    into multiple paths. Each junction can have multiple child wires.
    """
    
    def __init__(self, junction_id: str, position: Tuple[int, int]):
        """
        Initialize a Junction.
        
        Args:
            junction_id: Unique 8-character identifier for this junction
            position: (X, Y) coordinates on the page
        """
        self.junction_id = junction_id
        self.position = position
        self.child_wires: Dict[str, 'Wire'] = {}  # wire_id -> Wire
    
    def add_child_wire(self, wire: 'Wire') -> bool:
        """
        Add a child wire to this junction.
        
        Args:
            wire: Wire to add as child
            
        Returns:
            True if wire was added, False if wire_id already exists
        """
        if wire.wire_id in self.child_wires:
            return False
        
        self.child_wires[wire.wire_id] = wire
        wire.parent_junction = self
        return True
    
    def remove_child_wire(self, wire_id: str) -> Optional['Wire']:
        """
        Remove a child wire from this junction.
        
        Args:
            wire_id: ID of wire to remove
            
        Returns:
            Removed Wire object, or None if not found
        """
        wire = self.child_wires.pop(wire_id, None)
        if wire:
            wire.parent_junction = None
        return wire
    
    def get_child_wire(self, wire_id: str) -> Optional['Wire']:
        """
        Get a child wire by ID.
        
        Args:
            wire_id: ID of wire to retrieve
            
        Returns:
            Wire object or None if not found
        """
        return self.child_wires.get(wire_id)
    
    def get_all_child_wires(self) -> List['Wire']:
        """
        Get all child wires.
        
        Returns:
            List of all child Wire objects
        """
        return list(self.child_wires.values())
    
    def to_dict(self) -> dict:
        """
        Serialize junction to dictionary (matches .rsim schema).
        
        Returns:
            Dictionary representation of junction
        """
        return {
            'junction_id': self.junction_id,
            'position': {
                'x': self.position[0],
                'y': self.position[1]
            },
            'child_wires': [wire.to_dict() for wire in self.child_wires.values()]
        }
    
    @classmethod
    def from_dict(cls, data: dict, parent_wire: Optional['Wire'] = None) -> 'Junction':
        """
        Deserialize junction from dictionary (matches .rsim schema).
        
        Args:
            data: Dictionary containing junction data
            parent_wire: Optional parent wire for child wires
            
        Returns:
            New Junction instance
        """
        position = data['position']
        junction = cls(
            junction_id=data['junction_id'],
            position=(position['x'], position['y'])
        )
        
        # Deserialize child wires (array in schema)
        for wire_data in data.get('child_wires', []):
            child_wire = Wire.from_dict(wire_data, parent_junction=junction)
            junction.child_wires[child_wire.wire_id] = child_wire
        
        return junction
    
    def __repr__(self):
        return f"Junction({self.junction_id} at {self.position}, {len(self.child_wires)} children)"


class Wire:
    """
    A connection between tabs with optional waypoints and junctions.
    
    Wires connect component tabs to form electrical networks. They can:
    - Connect two tabs directly (start_tab_id and end_tab_id)
    - End at a junction (end_tab_id is None)
    - Contain waypoints for custom routing
    - Contain junctions for branching paths
    - Be nested within a junction as a child wire
    """
    
    def __init__(self, wire_id: str, start_tab_id: str, end_tab_id: Optional[str] = None):
        """
        Initialize a Wire.
        
        Args:
            wire_id: Unique 8-character identifier for this wire
            start_tab_id: ID of the starting tab
            end_tab_id: ID of the ending tab (None if wire ends at junction)
        """
        self.wire_id = wire_id
        self.start_tab_id = start_tab_id
        self.end_tab_id = end_tab_id
        
        self.waypoints: Dict[str, Waypoint] = {}  # waypoint_id -> Waypoint
        self.junctions: Dict[str, Junction] = {}  # junction_id -> Junction
        
        # Parent junction if this wire is a child of a junction
        self.parent_junction: Optional[Junction] = None
    
    def add_waypoint(self, waypoint: Waypoint) -> bool:
        """
        Add a waypoint to this wire.
        
        Args:
            waypoint: Waypoint to add
            
        Returns:
            True if waypoint was added, False if waypoint_id already exists
        """
        if waypoint.waypoint_id in self.waypoints:
            return False
        
        self.waypoints[waypoint.waypoint_id] = waypoint
        return True
    
    def remove_waypoint(self, waypoint_id: str) -> Optional[Waypoint]:
        """
        Remove a waypoint from this wire.
        
        Args:
            waypoint_id: ID of waypoint to remove
            
        Returns:
            Removed Waypoint object, or None if not found
        """
        return self.waypoints.pop(waypoint_id, None)
    
    def get_waypoint(self, waypoint_id: str) -> Optional[Waypoint]:
        """
        Get a waypoint by ID.
        
        Args:
            waypoint_id: ID of waypoint to retrieve
            
        Returns:
            Waypoint object or None if not found
        """
        return self.waypoints.get(waypoint_id)
    
    def get_all_waypoints(self) -> List[Waypoint]:
        """
        Get all waypoints.
        
        Returns:
            List of all Waypoint objects
        """
        return list(self.waypoints.values())
    
    def add_junction(self, junction: Junction) -> bool:
        """
        Add a junction to this wire.
        
        Args:
            junction: Junction to add
            
        Returns:
            True if junction was added, False if junction_id already exists
        """
        if junction.junction_id in self.junctions:
            return False
        
        self.junctions[junction.junction_id] = junction
        return True
    
    def remove_junction(self, junction_id: str) -> Optional[Junction]:
        """
        Remove a junction from this wire.
        
        Args:
            junction_id: ID of junction to remove
            
        Returns:
            Removed Junction object, or None if not found
        """
        return self.junctions.pop(junction_id, None)
    
    def get_junction(self, junction_id: str) -> Optional[Junction]:
        """
        Get a junction by ID.
        
        Args:
            junction_id: ID of junction to retrieve
            
        Returns:
            Junction object or None if not found
        """
        return self.junctions.get(junction_id)
    
    def get_all_junctions(self) -> List[Junction]:
        """
        Get all junctions.
        
        Returns:
            List of all Junction objects
        """
        return list(self.junctions.values())
    
    def get_all_connected_tabs(self) -> List[str]:
        """
        Get all tab IDs connected by this wire and its junctions.
        
        This traverses the entire wire hierarchy to find all tabs that
        are part of this wire network.
        
        Returns:
            List of all connected tab IDs
        """
        tabs = [self.start_tab_id]
        
        if self.end_tab_id:
            tabs.append(self.end_tab_id)
        
        # Recursively get tabs from child wires in junctions
        for junction in self.junctions.values():
            for child_wire in junction.get_all_child_wires():
                tabs.extend(child_wire.get_all_connected_tabs())
        
        return tabs
    
    def to_dict(self) -> dict:
        """
        Serialize wire to dictionary (matches .rsim schema).
        
        Returns:
            Dictionary representation of wire
        """
        result = {
            'wire_id': self.wire_id,
            'start_tab_id': self.start_tab_id
        }
        
        # Optional fields (per schema)
        if self.end_tab_id is not None:
            result['end_tab_id'] = self.end_tab_id
        
        if self.waypoints:
            result['waypoints'] = [wp.to_dict() for wp in self.waypoints.values()]
        
        if self.junctions:
            result['junctions'] = [junc.to_dict() for junc in self.junctions.values()]
        
        return result
    
    @classmethod
    def from_dict(cls, data: dict, parent_junction: Optional[Junction] = None) -> 'Wire':
        """
        Deserialize wire from dictionary (matches .rsim schema).
        
        Args:
            data: Dictionary containing wire data
            parent_junction: Optional parent junction if this is a child wire
            
        Returns:
            New Wire instance
        """
        wire = cls(
            wire_id=data['wire_id'],
            start_tab_id=data['start_tab_id'],
            end_tab_id=data.get('end_tab_id')
        )
        
        wire.parent_junction = parent_junction
        
        # Deserialize waypoints (array in schema)
        for wp_data in data.get('waypoints', []):
            waypoint = Waypoint.from_dict(wp_data)
            wire.waypoints[waypoint.waypoint_id] = waypoint
        
        # Deserialize junctions (array in schema)
        for junc_data in data.get('junctions', []):
            junction = Junction.from_dict(junc_data, parent_wire=wire)
            wire.junctions[junction.junction_id] = junction
        
        return wire
    
    def __repr__(self):
        end = f"→{self.end_tab_id}" if self.end_tab_id else "→Junction"
        return f"Wire({self.wire_id}: {self.start_tab_id}{end}, {len(self.waypoints)} waypoints, {len(self.junctions)} junctions)"

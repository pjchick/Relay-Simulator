"""
Test suite for Wire Structure Classes (Phase 2.1)

Comprehensive tests for Waypoint, Junction, and Wire classes including
wire hierarchy, junction connections, and serialization.
"""

import sys
import os

# Add parent directory to path to import relay_simulator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.wire import Waypoint, Junction, Wire


def test_waypoint_creation():
    """Test Waypoint class creation."""
    print("\n=== Testing Waypoint Creation ===")
    
    wp = Waypoint("waypoint1", (100, 200))
    
    assert wp.waypoint_id == "waypoint1"
    assert wp.position == (100, 200)
    print(f"✓ Waypoint created: {wp}")
    
    print("✓ Waypoint creation tests passed")


def test_waypoint_serialization():
    """Test Waypoint serialization."""
    print("\n=== Testing Waypoint Serialization ===")
    
    wp1 = Waypoint("waypoint1", (150, 250))
    
    # Serialize
    data = wp1.to_dict()
    assert data['waypoint_id'] == "waypoint1"
    assert data['position'] == [150, 250]
    print(f"✓ Serialized: {data}")
    
    # Deserialize
    wp2 = Waypoint.from_dict(data)
    assert wp2.waypoint_id == wp1.waypoint_id
    assert wp2.position == wp1.position
    print(f"✓ Deserialized: {wp2}")
    
    print("✓ Waypoint serialization tests passed")


def test_junction_creation():
    """Test Junction class creation."""
    print("\n=== Testing Junction Creation ===")
    
    junction = Junction("junc001", (300, 400))
    
    assert junction.junction_id == "junc001"
    assert junction.position == (300, 400)
    assert len(junction.child_wires) == 0
    print(f"✓ Junction created: {junction}")
    
    print("✓ Junction creation tests passed")


def test_junction_add_child_wire():
    """Test adding child wires to junction."""
    print("\n=== Testing Junction Add Child Wire ===")
    
    junction = Junction("junc001", (300, 400))
    
    wire1 = Wire("wire001", "tab001", "tab002")
    result = junction.add_child_wire(wire1)
    
    assert result == True
    assert len(junction.child_wires) == 1
    assert "wire001" in junction.child_wires
    assert wire1.parent_junction == junction
    print(f"✓ Added child wire: {len(junction.child_wires)} total")
    
    # Try to add duplicate
    wire_dup = Wire("wire001", "tab003", "tab004")
    result = junction.add_child_wire(wire_dup)
    
    assert result == False
    assert len(junction.child_wires) == 1
    print(f"✓ Duplicate wire ID rejected")
    
    # Add more wires
    wire2 = Wire("wire002", "tab005", "tab006")
    wire3 = Wire("wire003", "tab007", "tab008")
    junction.add_child_wire(wire2)
    junction.add_child_wire(wire3)
    
    assert len(junction.child_wires) == 3
    print(f"✓ Added 3 child wires total")
    
    print("✓ Junction add child wire tests passed")


def test_junction_remove_child_wire():
    """Test removing child wires from junction."""
    print("\n=== Testing Junction Remove Child Wire ===")
    
    junction = Junction("junc001", (300, 400))
    wire1 = Wire("wire001", "tab001", "tab002")
    wire2 = Wire("wire002", "tab003", "tab004")
    junction.add_child_wire(wire1)
    junction.add_child_wire(wire2)
    
    # Remove wire
    removed = junction.remove_child_wire("wire001")
    
    assert removed == wire1
    assert len(junction.child_wires) == 1
    assert "wire001" not in junction.child_wires
    assert removed.parent_junction is None
    print(f"✓ Removed wire: {len(junction.child_wires)} remaining")
    
    # Try to remove non-existent
    removed = junction.remove_child_wire("nonexistent")
    assert removed is None
    print(f"✓ Remove non-existent returns None")
    
    print("✓ Junction remove child wire tests passed")


def test_junction_get_child_wires():
    """Test getting child wires from junction."""
    print("\n=== Testing Junction Get Child Wires ===")
    
    junction = Junction("junc001", (300, 400))
    wire1 = Wire("wire001", "tab001", "tab002")
    wire2 = Wire("wire002", "tab003", "tab004")
    junction.add_child_wire(wire1)
    junction.add_child_wire(wire2)
    
    # Get specific wire
    retrieved = junction.get_child_wire("wire001")
    assert retrieved == wire1
    print(f"✓ Retrieved wire by ID: {retrieved.wire_id}")
    
    # Get all wires
    all_wires = junction.get_all_child_wires()
    assert len(all_wires) == 2
    assert wire1 in all_wires
    assert wire2 in all_wires
    print(f"✓ Retrieved all wires: {len(all_wires)} wires")
    
    print("✓ Junction get child wires tests passed")


def test_wire_creation():
    """Test Wire class creation."""
    print("\n=== Testing Wire Creation ===")
    
    # Wire with end tab
    wire1 = Wire("wire001", "tab001", "tab002")
    
    assert wire1.wire_id == "wire001"
    assert wire1.start_tab_id == "tab001"
    assert wire1.end_tab_id == "tab002"
    assert len(wire1.waypoints) == 0
    assert len(wire1.junctions) == 0
    assert wire1.parent_junction is None
    print(f"✓ Wire with end tab: {wire1}")
    
    # Wire ending at junction (no end tab)
    wire2 = Wire("wire002", "tab003")
    
    assert wire2.end_tab_id is None
    print(f"✓ Wire without end tab: {wire2}")
    
    print("✓ Wire creation tests passed")


def test_wire_waypoints():
    """Test wire waypoint management."""
    print("\n=== Testing Wire Waypoints ===")
    
    wire = Wire("wire001", "tab001", "tab002")
    
    # Add waypoints
    wp1 = Waypoint("wp001", (100, 100))
    result = wire.add_waypoint(wp1)
    
    assert result == True
    assert len(wire.waypoints) == 1
    assert "wp001" in wire.waypoints
    print(f"✓ Added waypoint: {len(wire.waypoints)} total")
    
    # Try to add duplicate
    wp_dup = Waypoint("wp001", (200, 200))
    result = wire.add_waypoint(wp_dup)
    
    assert result == False
    assert len(wire.waypoints) == 1
    print(f"✓ Duplicate waypoint ID rejected")
    
    # Add more waypoints
    wp2 = Waypoint("wp002", (150, 150))
    wp3 = Waypoint("wp003", (200, 150))
    wire.add_waypoint(wp2)
    wire.add_waypoint(wp3)
    
    assert len(wire.waypoints) == 3
    print(f"✓ Added 3 waypoints total")
    
    # Get waypoint
    retrieved = wire.get_waypoint("wp002")
    assert retrieved == wp2
    print(f"✓ Retrieved waypoint: {retrieved}")
    
    # Get all waypoints
    all_wps = wire.get_all_waypoints()
    assert len(all_wps) == 3
    print(f"✓ Retrieved all waypoints: {len(all_wps)}")
    
    # Remove waypoint
    removed = wire.remove_waypoint("wp001")
    assert removed == wp1
    assert len(wire.waypoints) == 2
    print(f"✓ Removed waypoint: {len(wire.waypoints)} remaining")
    
    print("✓ Wire waypoints tests passed")


def test_wire_junctions():
    """Test wire junction management."""
    print("\n=== Testing Wire Junctions ===")
    
    wire = Wire("wire001", "tab001")
    
    # Add junction
    junc1 = Junction("junc001", (300, 300))
    result = wire.add_junction(junc1)
    
    assert result == True
    assert len(wire.junctions) == 1
    assert "junc001" in wire.junctions
    print(f"✓ Added junction: {len(wire.junctions)} total")
    
    # Try to add duplicate
    junc_dup = Junction("junc001", (400, 400))
    result = wire.add_junction(junc_dup)
    
    assert result == False
    assert len(wire.junctions) == 1
    print(f"✓ Duplicate junction ID rejected")
    
    # Get junction
    retrieved = wire.get_junction("junc001")
    assert retrieved == junc1
    print(f"✓ Retrieved junction: {retrieved}")
    
    # Get all junctions
    all_juncs = wire.get_all_junctions()
    assert len(all_juncs) == 1
    print(f"✓ Retrieved all junctions: {len(all_juncs)}")
    
    # Remove junction
    removed = wire.remove_junction("junc001")
    assert removed == junc1
    assert len(wire.junctions) == 0
    print(f"✓ Removed junction: {len(wire.junctions)} remaining")
    
    print("✓ Wire junctions tests passed")


def test_wire_hierarchy():
    """Test wire parent/child hierarchy."""
    print("\n=== Testing Wire Hierarchy ===")
    
    # Create parent wire with junction
    parent_wire = Wire("wire001", "tab001")
    junction = Junction("junc001", (300, 300))
    parent_wire.add_junction(junction)
    
    # Add child wires to junction
    child1 = Wire("wire002", "tab002", "tab003")
    child2 = Wire("wire003", "tab004", "tab005")
    junction.add_child_wire(child1)
    junction.add_child_wire(child2)
    
    assert child1.parent_junction == junction
    assert child2.parent_junction == junction
    print(f"✓ Child wires have parent junction reference")
    
    # Verify hierarchy navigation
    assert len(junction.child_wires) == 2
    assert junction in parent_wire.junctions.values()
    print(f"✓ Can navigate parent → junction → children")
    
    print("✓ Wire hierarchy tests passed")


def test_wire_nested_junctions():
    """Test nested junction structure."""
    print("\n=== Testing Nested Junctions ===")
    
    # Create main wire with junction
    main_wire = Wire("wire001", "tab001")
    junc1 = Junction("junc001", (300, 300))
    main_wire.add_junction(junc1)
    
    # Add child wire to first junction
    child1 = Wire("wire002", "tab002")
    junc1.add_child_wire(child1)
    
    # Add another junction to the child wire
    junc2 = Junction("junc002", (400, 400))
    child1.add_junction(junc2)
    
    # Add grandchild wires
    grandchild1 = Wire("wire003", "tab003", "tab004")
    grandchild2 = Wire("wire004", "tab005", "tab006")
    junc2.add_child_wire(grandchild1)
    junc2.add_child_wire(grandchild2)
    
    # Verify structure
    assert len(main_wire.junctions) == 1
    assert len(junc1.child_wires) == 1
    assert len(child1.junctions) == 1
    assert len(junc2.child_wires) == 2
    print(f"✓ Nested junction structure: main → junc1 → child → junc2 → 2 grandchildren")
    
    print("✓ Nested junctions tests passed")


def test_wire_get_all_connected_tabs():
    """Test getting all connected tabs in wire network."""
    print("\n=== Testing Get All Connected Tabs ===")
    
    # Simple wire: tab001 → tab002
    wire1 = Wire("wire001", "tab001", "tab002")
    tabs = wire1.get_all_connected_tabs()
    
    assert len(tabs) == 2
    assert "tab001" in tabs
    assert "tab002" in tabs
    print(f"✓ Simple wire connects 2 tabs: {tabs}")
    
    # Wire with junction
    wire2 = Wire("wire002", "tab003")
    junc = Junction("junc001", (300, 300))
    wire2.add_junction(junc)
    
    child1 = Wire("wire003", "tab004", "tab005")
    child2 = Wire("wire004", "tab006", "tab007")
    junc.add_child_wire(child1)
    junc.add_child_wire(child2)
    
    tabs = wire2.get_all_connected_tabs()
    
    assert len(tabs) == 5  # tab003, tab004, tab005, tab006, tab007
    assert "tab003" in tabs
    assert "tab004" in tabs
    assert "tab005" in tabs
    assert "tab006" in tabs
    assert "tab007" in tabs
    print(f"✓ Junction wire connects 5 tabs: {tabs}")
    
    print("✓ Get all connected tabs tests passed")


def test_waypoint_serialization_roundtrip():
    """Test waypoint serialization roundtrip."""
    print("\n=== Testing Waypoint Serialization Roundtrip ===")
    
    wp1 = Waypoint("wp001", (123, 456))
    
    # Serialize and deserialize
    data = wp1.to_dict()
    wp2 = Waypoint.from_dict(data)
    
    assert wp2.waypoint_id == wp1.waypoint_id
    assert wp2.position == wp1.position
    print(f"✓ Roundtrip preserves data")
    
    print("✓ Waypoint serialization roundtrip tests passed")


def test_junction_serialization():
    """Test junction serialization."""
    print("\n=== Testing Junction Serialization ===")
    
    junction = Junction("junc001", (300, 400))
    wire1 = Wire("wire001", "tab001", "tab002")
    wire2 = Wire("wire002", "tab003", "tab004")
    junction.add_child_wire(wire1)
    junction.add_child_wire(wire2)
    
    # Serialize
    data = junction.to_dict()
    
    assert data['junction_id'] == "junc001"
    assert data['position'] == [300, 400]
    assert len(data['child_wires']) == 2
    assert 'wire001' in data['child_wires']
    assert 'wire002' in data['child_wires']
    print(f"✓ Serialized junction with {len(data['child_wires'])} child wires")
    
    # Deserialize
    junc2 = Junction.from_dict(data)
    
    assert junc2.junction_id == junction.junction_id
    assert junc2.position == junction.position
    assert len(junc2.child_wires) == 2
    print(f"✓ Deserialized junction: {junc2}")
    
    print("✓ Junction serialization tests passed")


def test_wire_serialization():
    """Test wire serialization."""
    print("\n=== Testing Wire Serialization ===")
    
    wire = Wire("wire001", "tab001", "tab002")
    wp1 = Waypoint("wp001", (100, 100))
    wp2 = Waypoint("wp002", (200, 200))
    wire.add_waypoint(wp1)
    wire.add_waypoint(wp2)
    
    # Serialize
    data = wire.to_dict()
    
    assert data['wire_id'] == "wire001"
    assert data['start_tab_id'] == "tab001"
    assert data['end_tab_id'] == "tab002"
    assert len(data['waypoints']) == 2
    print(f"✓ Serialized wire with {len(data['waypoints'])} waypoints")
    
    # Deserialize
    wire2 = Wire.from_dict(data)
    
    assert wire2.wire_id == wire.wire_id
    assert wire2.start_tab_id == wire.start_tab_id
    assert wire2.end_tab_id == wire.end_tab_id
    assert len(wire2.waypoints) == 2
    print(f"✓ Deserialized wire: {wire2}")
    
    print("✓ Wire serialization tests passed")


def test_wire_complex_serialization():
    """Test complex wire structure serialization."""
    print("\n=== Testing Complex Wire Serialization ===")
    
    # Create complex structure
    wire = Wire("wire001", "tab001")
    wp1 = Waypoint("wp001", (100, 100))
    wire.add_waypoint(wp1)
    
    junc1 = Junction("junc001", (200, 200))
    wire.add_junction(junc1)
    
    child1 = Wire("wire002", "tab002", "tab003")
    child2 = Wire("wire003", "tab004", "tab005")
    junc1.add_child_wire(child1)
    junc1.add_child_wire(child2)
    
    # Serialize
    data = wire.to_dict()
    
    assert len(data['waypoints']) == 1
    assert len(data['junctions']) == 1
    assert len(data['junctions']['junc001']['child_wires']) == 2
    print(f"✓ Serialized complex structure")
    
    # Deserialize
    wire2 = Wire.from_dict(data)
    
    assert len(wire2.waypoints) == 1
    assert len(wire2.junctions) == 1
    junc2 = wire2.get_junction("junc001")
    assert len(junc2.child_wires) == 2
    print(f"✓ Deserialized complex structure")
    
    # Verify parent references
    for child in junc2.get_all_child_wires():
        assert child.parent_junction == junc2
    print(f"✓ Parent references restored")
    
    print("✓ Complex wire serialization tests passed")


def test_wire_repr():
    """Test wire string representation."""
    print("\n=== Testing Wire Repr ===")
    
    wire1 = Wire("wire001", "tab001", "tab002")
    repr1 = repr(wire1)
    print(f"✓ Wire repr: {repr1}")
    assert "wire001" in repr1
    assert "tab001" in repr1
    assert "tab002" in repr1
    
    wire2 = Wire("wire002", "tab003")
    repr2 = repr(wire2)
    print(f"✓ Junction wire repr: {repr2}")
    assert "Junction" in repr2
    
    print("✓ Wire repr tests passed")


def run_all_tests():
    """Run all Wire Structure tests."""
    print("=" * 60)
    print("WIRE STRUCTURE CLASSES TEST SUITE (Phase 2.1)")
    print("=" * 60)
    
    try:
        test_waypoint_creation()
        test_waypoint_serialization()
        test_junction_creation()
        test_junction_add_child_wire()
        test_junction_remove_child_wire()
        test_junction_get_child_wires()
        test_wire_creation()
        test_wire_waypoints()
        test_wire_junctions()
        test_wire_hierarchy()
        test_wire_nested_junctions()
        test_wire_get_all_connected_tabs()
        test_waypoint_serialization_roundtrip()
        test_junction_serialization()
        test_wire_serialization()
        test_wire_complex_serialization()
        test_wire_repr()
        
        print("\n" + "=" * 60)
        print("✓ ALL WIRE STRUCTURE TESTS PASSED")
        print("=" * 60)
        print("\nSection 2.1 Wire Structure Classes Requirements:")
        print("✓ Define Waypoint class")
        print("  ✓ WaypointId (string)")
        print("  ✓ Position (X, Y)")
        print("✓ Define Junction class")
        print("  ✓ JunctionId (string)")
        print("  ✓ Position (X, Y)")
        print("  ✓ Collection of child Wires")
        print("  ✓ Add/remove/get child wires")
        print("✓ Define Wire class")
        print("  ✓ WireId (string)")
        print("  ✓ StartTabId (reference)")
        print("  ✓ EndTabId (reference, can be null if junction)")
        print("  ✓ Collection of Waypoints")
        print("  ✓ Collection of Junctions")
        print("  ✓ Parent junction (if nested)")
        print("  ✓ Add/remove/get waypoints")
        print("  ✓ Add/remove/get junctions")
        print("  ✓ Get all connected tabs")
        print("✓ Implement wire hierarchy")
        print("  ✓ Nested wire structure")
        print("  ✓ Navigate parent/child relationships")
        print("  ✓ Multi-level nesting support")
        print("✓ Add serialization support")
        print("  ✓ Waypoint.to_dict() / from_dict()")
        print("  ✓ Junction.to_dict() / from_dict()")
        print("  ✓ Wire.to_dict() / from_dict()")
        print("  ✓ Complex structure serialization")
        print("✓ Tests")
        print("  ✓ Test wire creation")
        print("  ✓ Test wire hierarchy")
        print("  ✓ Test junction connections")
        print("  ✓ Test nested junctions")
        print("  ✓ Test serialization")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

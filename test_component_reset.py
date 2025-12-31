"""
Test to verify that switches and thumbwheels reset properly at simulation start.
"""

import sys
import os

# Add relay_simulator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'relay_simulator'))

from components.switch import Switch
from components.thumbwheel import Thumbwheel


class MockVnetManager:
    """Mock VnetManager for testing."""
    def mark_tab_dirty(self, tab_id):
        pass


def test_switch_reset():
    """Test that switches reset to OFF at sim_start."""
    print("Testing Switch reset...")
    
    # Create a switch
    switch = Switch("test_switch", "test_page")
    
    # Simulate user turning it ON
    switch._is_on = True
    print(f"  Switch state after user interaction: {switch._is_on} (ON)")
    
    # Call sim_start (simulates starting a new simulation)
    vnet_mgr = MockVnetManager()
    switch.sim_start(vnet_mgr, None)
    
    # Verify it's now OFF
    print(f"  Switch state after sim_start: {switch._is_on} (OFF)")
    assert switch._is_on == False, "Switch should be OFF after sim_start"
    
    print("  ✓ Switch properly resets to OFF")
    return True


def test_thumbwheel_reset():
    """Test that thumbwheels reset to 0 at sim_start."""
    print("\nTesting Thumbwheel reset...")
    
    # Create a thumbwheel
    thumbwheel = Thumbwheel("test_thumbwheel", "test_page")
    
    # Simulate user setting it to a non-zero value
    thumbwheel._set_value(7)
    print(f"  Thumbwheel value after user interaction: {thumbwheel._get_value()}")
    
    # Call sim_start (simulates starting a new simulation)
    vnet_mgr = MockVnetManager()
    thumbwheel.sim_start(vnet_mgr, None)
    
    # Verify it's now 0
    print(f"  Thumbwheel value after sim_start: {thumbwheel._get_value()}")
    assert thumbwheel._get_value() == 0, "Thumbwheel should be 0 after sim_start"
    
    print("  ✓ Thumbwheel properly resets to 0")
    return True


if __name__ == "__main__":
    try:
        print("=" * 60)
        print("Testing Component Reset at Simulation Start")
        print("=" * 60)
        
        test_switch_reset()
        test_thumbwheel_reset()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("Switches reset to OFF and thumbwheels reset to 0")
        print("when simulation starts.")
        
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

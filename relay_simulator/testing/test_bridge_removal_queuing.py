"""
Simple Unit Test for Bridge Removal Component Queuing

Tests that when a bridge is removed, components connected to the affected VNETs
are queued for updates.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.vnet import VNET
from core.bridge import Bridge
from core.tab import Tab
from core.pin import Pin
from components.gnd import GND
from components.ground_dpdt_relay import GroundDPDTRelay
from simulation.bridge_manager import BridgeManager
from simulation.component_update_coordinator import ComponentUpdateCoordinator
from simulation.dirty_flag_manager import DirtyFlagManager
from core.id_manager import IDManager
from core.state import PinState


def test_bridge_removal_queues_components():
    """
    Test that removing a bridge queues components connected to affected VNETs.
    """
    print("\n" + "=" * 60)
    print("Test: Bridge Removal Queues Components")
    print("=" * 60)
    
    # Create components
    page_id = "page1"
    gnd_comp = GND(component_id="gnd1", page_id=page_id)
    relay = GroundDPDTRelay(component_id="relay1", page_id=page_id)
    
    components = {
        gnd_comp.component_id: gnd_comp,
        relay.component_id: relay
    }
    
    # Collect tabs
    tabs = {}
    for comp in components.values():
        for pin in comp.pins.values():
            for tab in pin.tabs.  values():
                tabs[tab.tab_id] = tab
    
    # Create 2 VNETs
    vnet1_id = "vnet1"
    vnet2_id = "vnet2"
    
    vnet1 = VNET(vnet1_id, page_id)
    vnet2 = VNET(vnet2_id, page_id)
    
    # Add tabs to VNETs
    relay_gnd_tab = list(relay._gnd_pin.tabs.values())[0]
    gnd_tab = list(gnd_comp.pins[list(gnd_comp.pins.keys())[0]].tabs.values())[0]
    
    vnet1.add_tab(relay_gnd_tab.tab_id)
    vnet2.add_tab(gnd_tab.tab_id)
    
    vnets = {vnet1_id: vnet1, vnet2_id: vnet2}
    
    # Create managers
    id_manager = IDManager()
    dirty_manager = DirtyFlagManager(vnets)
    coordinator = ComponentUpdateCoordinator(components, tabs)
    bridges = {}
    bridge_manager = BridgeManager(bridges, id_manager, vnets, coordinator)
    
    # Create a bridge between the two VNETs
    bridge_id = bridge_manager.create_bridge(vnet1_id, vnet2_id, "test_component")
    
    print(f"Created bridge {bridge_id} between {vnet1_id} and {vnet2_id}")
    print(f"Components connected to VNET1: relay={relay.component_id}")
    print(f"Components connected to VNET2: gnd={gnd_comp.component_id}")
    
    # Now remove the bridge
    print("\nRemoving bridge...")
    bridge_manager.remove_bridge(bridge_id)
    
    # Check if components were queued
    queued = coordinator._queued_components
    print(f"\nComponents queued for update: {queued}")
    
    if relay.component_id in queued:
        print(f"✅ Relay was queued for update")
    else:
        print(f"❌ Relay was NOT queued for update")
        return False
    
    if gnd_comp.component_id in queued:
        print(f"✅ GND was queued for update")
    else:
        print(f"❌ GND was NOT queued for update")
        return False
    
    print("\n" + "=" * 60)
    print("✅ TEST PASSED: Components correctly queued on bridge removal")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_bridge_removal_queues_components()
    exit(0 if success else 1)

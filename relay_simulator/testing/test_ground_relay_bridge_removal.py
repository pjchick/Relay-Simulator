"""
Test Ground DPDT Relay - Bridge Removal Scenario

This test validates that when a relay loses its GND connection due to
another relay removing a bridge, it immediately de-energizes.

Scenario:
1. Relay B (regular DPDT) is energized, creating a bridge from Relay A's GND pin to actual GND
2. Relay A (Ground DPDT) energizes because it has COIL HIGH and GND connected through bridge
3. Relay B de-energizes, removing the bridge
4. Relay A should immediately de-energize (loses GND connection)

Author: AI Assistant
Date: 2026-02-11
"""

import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.vnet import VNET
from core.tab import Tab
from core.pin import Pin
from core.state import PinState
from components.gnd import GND
from components.ground_dpdt_relay import GroundDPDTRelay
from components.dpdt_relay import DPDTRelay
from components.vcc import VCC
from core.vnet_builder import VnetBuilder
from simulation.vnet_manager import VnetManager
from simulation.bridge_manager import BridgeManager
from simulation.dirty_flag_manager import DirtyFlagManager
from simulation.component_update_coordinator import ComponentUpdateCoordinator
from simulation.simulation_engine import SimulationEngine
from core.id_manager import IDManager


def test_ground_relay_bridge_removal():
    """
    Test that Ground DPDT Relay immediately de-energizes when bridge to GND is removed.
    
    Circuit:
    VCC ---> Relay A COIL
    Relay A GND ---> Relay B COM1
    Relay B NO1 ---> GND component
    VCC ---> Relay B COIL
    
    Sequence:
    1. Initial: Both relays energized (Relay A has GND through Relay B's bridge)
    2. De-energize Relay B (remove VCC from its coil)
    3. Verify: Relay A immediately de-energizes (loses GND connection)
    """
    print("\n" + "=" * 60)
    print("Test: Ground Relay Bridge Removal")
    print("=" * 60)
    
    # Create components
    page_id = "page1"
    vcc = VCC(component_id="vcc1", page_id=page_id)
    gnd_comp = GND(component_id="gnd1", page_id=page_id)
    relay_a = GroundDPDTRelay(component_id="relay_a", page_id=page_id)
    relay_b = DPDTRelay(component_id="relay_b", page_id=page_id)
    
    components = {
        vcc.component_id: vcc,
        gnd_comp.component_id: gnd_comp,
        relay_a.component_id: relay_a,
        relay_b.component_id: relay_b
    }
    
    # Collect all tabs
    tabs = {}
    for comp in components.values():
        for pin_id, pin in comp.pins.items():
            for tab_id, tab in pin.tabs.items():
                tabs[tab_id] = tab
    
    print(f"Created {len(components)} components")
    print(f"Created {len(tabs)} tabs")
    
    # Create VNETs and bridges
    vnets = {}
    bridges = {}
    
    # Build initial VNETs (without bridges yet)
    builder = VnetBuilder()
    
    # VNET 1: VCC to both relay coils
    vcc_tab = list(vcc.pins[list(vcc.pins.keys())[0]].tabs.values())[0]
    relay_a_coil_tab = list(relay_a._coil_pin.tabs.values())[0]
    relay_b_coil_tab = list(relay_b._coil_pin.tabs.values())[0]
    
    vnet1_id = "vnet_vcc"
    vnet1 = VNET(vnet1_id, vcc.page_id or "page1")
    vnet1.add_tab(vcc_tab.tab_id)
    vnet1.add_tab(relay_a_coil_tab.tab_id)
    vnet1.add_tab(relay_b_coil_tab.tab_id)
    vnets[vnet1_id] = vnet1
    
    # Assign tabs to VNET
    vcc_tab.vnet_id = vnet1_id
    relay_a_coil_tab.vnet_id = vnet1_id
    relay_b_coil_tab.vnet_id = vnet1_id
    
    # VNET 2: Relay A GND to Relay B COM1 (will be bridged to GND)
    relay_a_gnd_tab = list(relay_a._gnd_pin.tabs.values())[0]
    relay_b_com1_tab = list(relay_b._com1_pin.tabs.values())[0]
    
    vnet2_id = "vnet_relay_a_gnd"
    vnet2 = VNET(vnet2_id, relay_a.page_id or "page1")
    vnet2.add_tab(relay_a_gnd_tab.tab_id)
    vnet2.add_tab(relay_b_com1_tab.tab_id)
    vnets[vnet2_id] = vnet2
    
    relay_a_gnd_tab.vnet_id = vnet2_id
    relay_b_com1_tab.vnet_id = vnet2_id
    
    # VNET 3: Relay B NO1 to actual GND
    relay_b_no1_tab = list(relay_b._no1_pin.tabs.values())[0]
    gnd_tab = list(gnd_comp.pins[list(gnd_comp.pins.keys())[0]].tabs.values())[0]
    
    vnet3_id = "vnet_gnd"
    vnet3 = VNET(vnet3_id, gnd_comp.page_id or "page1")
    vnet3.add_tab(relay_b_no1_tab.tab_id)
    vnet3.add_tab(gnd_tab.tab_id)
    vnets[vnet3_id] = vnet3
    
    relay_b_no1_tab.vnet_id = vnet3_id
    gnd_tab.vnet_id = vnet3_id
    
    print(f"Created {len(vnets)} VNETs")
    
    # Create simulation engine
    id_manager = IDManager()
    dirty_manager = DirtyFlagManager(vnets)
    coordinator = ComponentUpdateCoordinator(components, tabs)
    vnet_manager = VnetManager(vnets, tabs, dirty_manager)
    bridge_manager = BridgeManager(bridges, id_manager, vnets, coordinator)
    
    # Initialize components
    for comp in components.values():
        comp.sim_start(vnet_manager, bridge_manager)
    
    # Set VCC to HIGH
    vnet1.state = PinState.HIGH
    
    # Update all pins from their VNETs
    for comp in components.values():
        for pin in comp.pins.values():
            for tab in pin.tabs.values():
                if tab.vnet_id:
                    vnet = vnets.get(tab.vnet_id)
                    if vnet:
                        pin.set_state(vnet.state)
    
    # Run simulate_logic on all components to evaluate state
    for comp in components.values():
        comp.simulate_logic(vnet_manager, bridge_manager)
    
    # Give relays time to energize and create bridges (10ms delay)
    time.sleep(0.015)
    
    print(f"Bridges created: {len(bridges)}")
    for bridge_id, bridge in bridges.items():
        print(f"  Bridge {bridge_id}: {bridge.vnet_id1} <-> {bridge.vnet_id2}")
    
    # Run simulate_logic again now that bridges are created
    for comp in components.values():
        comp.simulate_logic(vnet_manager, bridge_manager)
    
    print("\nPhase 1: Both relays should be energized")
    print("-" * 60)
    print(f"VNET1 (VCC) state: {vnet1.state}")
    print(f"Relay A COIL VNET ID: {relay_a_coil_tab.vnet_id}")
    print(f"Relay A COIL state: {relay_a._coil_pin.state}")
    print(f"Relay A GND connected: {relay_a._is_gnd_connected(vnet_manager)}")
    print(f"Relay A energized: {relay_a._is_energized}")
    print(f"Relay A target energized: {relay_a._target_energized}")
    print(f"Relay A timer active: {relay_a._timer_active}")
    print(f"Relay B energized: {relay_b._is_energized}")
    
    if not relay_a._is_energized or not relay_b._is_energized:
        print("❌ FAIL: Relays should be energized initially")
        return False
    
    print("✅ Phase 1 PASS: Both relays energized")
    
    # Now de-energize Relay B by removing VCC from its coil
    print("\nPhase 2: De-energize Relay B (remove bridge)")
    print("-" * 60)
    
    # Remove relay B's coil from VCC VNET
    vnet1.remove_tab(relay_b_coil_tab.tab_id)
    relay_b_coil_tab.vnet_id = None
    
    # Create separate VNET for relay B coil (FLOAT)
    vnet4_id = "vnet_relay_b_coil"
    vnet4 = VNET(vnet4_id, relay_b.page_id or "page1")
    vnet4.add_tab(relay_b_coil_tab.tab_id)
    vnet4.state = PinState.FLOAT
    vnets[vnet4_id] = vnet4
    relay_b_coil_tab.vnet_id = vnet4_id
    
    # Mark Relay B dirty and run its simulate_logic
    coordinator.queue_component_update(relay_b.component_id)
    coordinator.start_updates()
    pending = coordinator.get_pending_components()
    
    for comp in pending:
        comp.simulate_logic(vnet_manager, bridge_manager)
        coordinator.mark_update_complete(comp.component_id)
    
    # Wait for relay B to de-energize and remove bridges
    time.sleep(0.015)
    
    print(f"Relay B energized: {relay_b._is_energized}")
    print(f"Bridges remaining: {len(bridges)}")
    
    # Now mark Relay A dirty (it should be marked automatically when bridge removed)
    # Run simulation cycle to check Relay A
    coordinator.queue_component_update(relay_a.component_id)
    coordinator.start_updates()
    pending = coordinator.get_pending_components()
    
    for comp in pending:
        comp.simulate_logic(vnet_manager, bridge_manager)
        coordinator.mark_update_complete(comp.component_id)
    
    print(f"Relay A energized: {relay_a._is_energized}")
    
    if relay_a._is_energized:
        print("❌ FAIL: Relay A should have de-energized when bridge removed")
        return False
    
    print("✅ Phase 2 PASS: Relay A de-energized when bridge removed")
    print("\n" + "=" * 60)
    print("✅ TEST PASSED: Bridge removal correctly detected")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_ground_relay_bridge_removal()
    exit(0 if success else 1)

"""
Test script for GroundDPDTRelay component.

Tests the energization logic:
1. Relay does NOT energize with COIL HIGH but no GND connection
2. Relay DOES energize with COIL HIGH and GND connected
"""

import sys
import time

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.document import Document
from core.page import Page
from components.ground_dpdt_relay import GroundDPDTRelay
from components.dpdt_relay import DPDTRelay
from components.gnd import GND
from components.vcc import VCC
from core.wire import Wire
from core.vnet_builder import VnetBuilder
from simulation.vnet_manager import VnetManager
from simulation.bridge_manager import BridgeManager
from simulation.dirty_flag_manager import DirtyFlagManager
from core.state import PinState


def test_ground_relay_without_gnd():
    """Test relay with COIL HIGH but no GND connection - should NOT energize."""
    print("\nTest 1: GroundDPDTRelay with COIL HIGH but no GND connection")
    print("-" * 60)
    
    # Create components
    relay = GroundDPDTRelay("relay001", "page001")
    vcc = VCC("vcc001", "page001")
    
    # Build VNETs manually for testing
    from core.vnet import VNET
    
    # Get pins
    coil_pin = relay.get_pin_by_name("COIL")
    gnd_pin_relay = relay.get_pin_by_name("GND")
    vcc_pin = list(vcc.pins.values())[0]
    
    # VNET 1: VCC to COIL (COIL will be HIGH)
    vnet1 = VNET("vnet001", "page001")
    for tab in vcc_pin.tabs.values():
        vnet1.add_tab(tab.tab_id)
    for tab in coil_pin.tabs.values():
        vnet1.add_tab(tab.tab_id)
    
    # VNET 2: GND pin NOT connected to any GND component (just floating)
    vnet2 = VNET("vnet002", "page001")
    for tab in gnd_pin_relay.tabs.values():
        vnet2.add_tab(tab.tab_id)
    
    vnets = {"vnet001": vnet1, "vnet002": vnet2}
    tabs = {}
    for comp in [relay, vcc]:
        for pin in comp.pins.values():
            for tab in pin.tabs.values():
                tabs[tab.tab_id] = tab
    
    print(f"Created {len(vnets)} VNETs")
    print(f"Created {len(tabs)} tabs")
    
    # Create managers
    from core.id_manager import IDManager
    id_manager = IDManager()
    dirty_manager = DirtyFlagManager(vnets)
    vnet_manager = VnetManager(vnets, tabs, dirty_manager)
    bridge_manager = BridgeManager({}, id_manager, vnets)
    
    # Start simulation
    relay.sim_start(vnet_manager, bridge_manager)
    vcc.sim_start(vnet_manager, bridge_manager)
    
    # Manually propagate VCC state to VNET (in real simulation, state propagator does this)
    vnet1.state = PinState.HIGH
    
    # Run simulation logic
    relay.simulate_logic(vnet_manager, bridge_manager)
    
    # Let timer complete
    time.sleep(0.02)
    
    # Check result
    print(f"Relay energized: {relay.is_energized()}")
    print(f"Expected: False (no GND connection)")
    
    if relay.is_energized():
        print("❌ FAIL: Relay should NOT energize without GND connection")
        return False
    else:
        print("✅ PASS: Relay correctly stays de-energized")
        return True


def test_ground_relay_with_gnd():
    """Test relay with COIL HIGH and GND connected - should energize."""
    print("\nTest 2: GroundDPDTRelay with COIL HIGH and GND connected")
    print("-" * 60)
    
    # Create components
    relay = GroundDPDTRelay("relay001", "page001")
    vcc = VCC("vcc001", "page001")
    gnd = GND("gnd001", "page001")
    
    # Get pins
    coil_pin = relay.get_pin_by_name("COIL")
    gnd_pin_relay = relay.get_pin_by_name("GND")
    vcc_pin = list(vcc.pins.values())[0]
    gnd_pin = list(gnd.pins.values())[0]
    
    # Build VNETs manually for testing
    from core.vnet import VNET
    
    # VNET 1: VCC to COIL
    vnet1 = VNET("vnet001", "page001")
    for tab in vcc_pin.tabs.values():
        vnet1.add_tab(tab.tab_id)
    for tab in coil_pin.tabs.values():
        vnet1.add_tab(tab.tab_id)
    
    # VNET 2: GND to relay GND pin
    vnet2 = VNET("vnet002", "page001")
    for tab in gnd_pin.tabs.values():
        vnet2.add_tab(tab.tab_id)
    for tab in gnd_pin_relay.tabs.values():
        vnet2.add_tab(tab.tab_id)
    
    vnets = {"vnet001": vnet1, "vnet002": vnet2}
    tabs = {}
    for comp in [relay, vcc, gnd]:
        for pin in comp.pins.values():
            for tab in pin.tabs.values():
                tabs[tab.tab_id] = tab
    
    print(f"Created {len(vnets)} VNETs")
    print(f"Created {len(tabs)} tabs")
    
    # Create managers
    from core.id_manager import IDManager
    id_manager = IDManager()
    dirty_manager = DirtyFlagManager(vnets)
    vnet_manager = VnetManager(vnets, tabs, dirty_manager)
    bridge_manager = BridgeManager({}, id_manager, vnets)
    
    # Start simulation
    relay.sim_start(vnet_manager, bridge_manager)
    vcc.sim_start(vnet_manager, bridge_manager)
    gnd.sim_start(vnet_manager, bridge_manager)
    
    # Manually propagate VCC state to VNET (in real simulation, state propagator does this)
    vnet1.state = PinState.HIGH
    
    # Run simulation logic
    relay.simulate_logic(vnet_manager, bridge_manager)
    
    # Let timer complete
    time.sleep(0.02)
    
    # Check result
    print(f"Relay energized: {relay.is_energized()}")
    print(f"Expected: True (COIL HIGH and GND connected)")
    
    if not relay.is_energized():
        print("❌ FAIL: Relay should energize with COIL HIGH and GND connected")
        return False
    else:
        print("✅ PASS: Relay correctly energizes")
        return True


def test_ground_relay_with_gnd_through_bridge():
    """Test relay with COIL HIGH and GND connected through another relay's bridge."""
    print("\nTest 3: GroundDPDTRelay with GND connected through bridge")
    print("-" * 60)
    
    # Create components
    relay_a = GroundDPDTRelay("relayA", "page001")
    relay_b = DPDTRelay("relayB", "page001")
    vcc = VCC("vcc001", "page001")
    gnd = GND("gnd001", "page001")
    
    # Get pins
    coil_a = relay_a.get_pin_by_name("COIL")
    gnd_pin_a = relay_a.get_pin_by_name("GND")
    
    coil_b = relay_b.get_pin_by_name("COIL")
    com1_b = relay_b.get_pin_by_name("COM1")
    no1_b = relay_b.get_pin_by_name("NO1")
    
    vcc_pin = list(vcc.pins.values())[0]
    gnd_pin = list(gnd.pins.values())[0]
    
    # Build VNETs manually for testing
    from core.vnet import VNET
    
    # VNET 1: VCC to both COILs (both relays energized)
    vnet1 = VNET("vnet001", "page001")
    for tab in vcc_pin.tabs.values():
        vnet1.add_tab(tab.tab_id)
    for tab in coil_a.tabs.values():
        vnet1.add_tab(tab.tab_id)
    for tab in coil_b.tabs.values():
        vnet1.add_tab(tab.tab_id)
    
    # VNET 2: Relay A's GND pin to Relay B's COM1
    vnet2 = VNET("vnet002", "page001")
    for tab in gnd_pin_a.tabs.values():
        vnet2.add_tab(tab.tab_id)
    for tab in com1_b.tabs.values():
        vnet2.add_tab(tab.tab_id)
    
    # VNET 3: Relay B's NO1 to GND component
    vnet3 = VNET("vnet003", "page001")
    for tab in no1_b.tabs.values():
        vnet3.add_tab(tab.tab_id)
    for tab in gnd_pin.tabs.values():
        vnet3.add_tab(tab.tab_id)
    
    vnets = {"vnet001": vnet1, "vnet002": vnet2, "vnet003": vnet3}
    tabs = {}
    for comp in [relay_a, relay_b, vcc, gnd]:
        for pin in comp.pins.values():
            for tab in pin.tabs.values():
                tabs[tab.tab_id] = tab
    
    print(f"Created {len(vnets)} VNETs")
    print(f"Created {len(tabs)} tabs")
    
    # Create managers
    from core.id_manager import IDManager
    id_manager = IDManager()
    dirty_manager = DirtyFlagManager(vnets)
    vnet_manager = VnetManager(vnets, tabs, dirty_manager)
    bridge_manager = BridgeManager({}, id_manager, vnets)
    
    # Start simulation
    relay_a.sim_start(vnet_manager, bridge_manager)
    relay_b.sim_start(vnet_manager, bridge_manager)
    vcc.sim_start(vnet_manager, bridge_manager)
    gnd.sim_start(vnet_manager, bridge_manager)
    
    # Manually propagate VCC state to VNET
    vnet1.state = PinState.HIGH
    
    # Relay B should create a bridge from COM1 to NO1 when energized
    # This simulates the bridge creation
    relay_b.simulate_logic(vnet_manager, bridge_manager)
    time.sleep(0.02)  # Wait for relay B timer
    
    # Now check if Relay A detects GND through the bridge
    relay_a.simulate_logic(vnet_manager, bridge_manager)
    time.sleep(0.02)  # Wait for relay A timer
    
    # Check result
    print(f"Relay A energized: {relay_a.is_energized()}")
    print(f"Relay B energized: {relay_b.is_energized()}")
    print(f"Expected: Both True (GND connected through Relay B's bridge)")
    
    if not relay_a.is_energized() or not relay_b.is_energized():
        print("❌ FAIL: Relay A should energize when GND is connected through Relay B")
        return False
    else:
        print("✅ PASS: Relay A correctly energizes with bridged GND connection")
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("GroundDPDTRelay Component Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(test_ground_relay_without_gnd())
    results.append(test_ground_relay_with_gnd())
    results.append(test_ground_relay_with_gnd_through_bridge())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

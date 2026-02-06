"""
Test SubCircuit simulation with SubTest1.rsim

This script loads the file, starts simulation, and simulates clicking the switch.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'relay_simulator'))

from fileio.document_loader import DocumentLoader
from components.factory import get_factory
from simulation.engine_factory import create_engine
from core.state import PinState

def test_subcircuit_simulation():
    """Test SubCircuit simulation."""
    
    print("="*70)
    print("SubCircuit Simulation Test")
    print("="*70)
    print()
    
    # Load document
    print("Loading SubTest1.rsim...")
    factory = get_factory()
    loader = DocumentLoader(factory)
    doc = loader.load_from_file('examples/SubTest1.rsim')
    print(f"[OK] Loaded document with {len(doc.pages)} pages")
    print()
    
    # Build simulation structures
    print("Building simulation structures...")
    from core.vnet_builder import VnetBuilder
    
    vnets = {}
    tabs = {}
    bridges = {}
    components = {}
    
    # Collect all components and tabs
    print("Components by page:")
    for page in doc.get_all_pages():
        page_comps = list(page.get_all_components())
        print(f"  {page.page_id} ({len(page_comps)} components):")
        for component in page_comps:
            link_info = f" [link: {component.link_name}]" if hasattr(component, 'link_name') and component.link_name else ""
            print(f"    {component.component_id}: {component.component_type}{link_info}")
            components[component.component_id] = component
            for pin in component.get_all_pins().values():
                pin._state = PinState.FLOAT
                for tab in pin.tabs.values():
                    tab._state = PinState.FLOAT
                    tabs[tab.tab_id] = tab
    print()
    
    # Build VNETs
    vnet_builder = VnetBuilder(doc.id_manager)
    for page in doc.get_all_pages():
        page_vnets = vnet_builder.build_vnets_for_page(page)
        for vnet in page_vnets:
            vnets[vnet.vnet_id] = vnet
    
    # Debug: Show VNETs with link names
    print("VNETs with link names:")
    for vnet_id, vnet in vnets.items():
        if vnet.link_names:
            print(f"  VNET {vnet_id}:")
            print(f"    Link names: {vnet.link_names}")
            print(f"    Tabs: {vnet.tab_ids}")
    print()
    
    print(f"  Components: {len(components)}")
    print(f"  Tabs: {len(tabs)}")
    print(f" VNETs: {len(vnets)}")
    print()
    
    # Create simulation engine
    print("Creating simulation engine...")
    engine = create_engine(vnets, tabs, bridges, components, mode='single')
    
    print(f"  Bridges dict: {len(bridges)} bridges")
    for bridge_id, bridge in bridges.items():
        print(f"    Bridge {bridge_id}: {bridge.vnet_id1} <-> {bridge.vnet_id2}")
    print()
    
    if not engine.initialize():
        print("[OK] Failed to initialize simulation")
        return False
    
    print("[OK] Simulation initialized")
    
    # Check if bridges were registered
    print(f"  After init - Bridges dict: {len(bridges)} bridges")
    for bridge_id, bridge in bridges.items():
        v1 = vnets.get(bridge.vnet_id1)
        v2 = vnets.get(bridge.vnet_id2)
        v1_info = f"{bridge.vnet_id1} ({list(v1.tab_ids)[0] if v1 and v1.tab_ids else '?'})"
        v2_info = f"{bridge.vnet_id2} ({list(v2.tab_ids)[0] if v2 and v2.tab_ids else '?'})"
        print(f"    Bridge {bridge_id}: {v1_info} <-> {v2_info}")
    print()
    
    # Find components
    main_page = doc.get_all_pages()[0]
    switch = None
    subcircuit = None
    indicator = None
    
    for comp in main_page.components.values():
        if comp.component_type == "Switch":
            switch = comp
        elif comp.component_type == "SubCircuit":
            subcircuit = comp
        elif comp.component_type == "Indicator":
            indicator = comp
    
    print(f"Switch: {switch.component_id if switch else 'NOT FOUND'}")
    print(f"SubCircuit: {subcircuit.component_id if subcircuit else 'NOT FOUND'}")
    print(f"Indicator: {indicator.component_id if indicator else 'NOT FOUND'}")
    print()
    
    # DEBUG: Check VNET connections
    print(f"DEBUG: VNET Information")
    print(f"  Total VNETs: {len(vnets)}")
    
    # Find which VNET contains the switch pin
    switch_pin_tab = f"{switch.component_id}.pin1.tab1"
    switch_vnet_id = None
    for vnet_id, vnet in vnets.items():
        if switch_pin_tab in vnet.tab_ids:
            switch_vnet_id = vnet_id
            print(f"  Switch tab {switch_pin_tab} is in VNET {vnet_id}")
            print(f"    VNET has {len(vnet.tab_ids)} tabs: {vnet.tab_ids}")
            break
    
    # Find which VNET contains the SubCircuit SUB_IN pin
    sub_in_tab = f"{subcircuit.component_id}.SUB_IN.tab1"
    sub_in_vnet_id = None
    for vnet_id, vnet in vnets.items():
        if sub_in_tab in vnet.tab_ids:
            sub_in_vnet_id = vnet_id
            print(f"  SubCircuit SUB_IN tab {sub_in_tab} is in VNET {vnet_id}")
            print(f"    VNET has {len(vnet.tab_ids)} tabs: {vnet.tab_ids}")
            break
    
    # Find which VNET contains the internal Link tab (should be bridged to SUB_IN)
    link_in_tab = "fc0145a6.pin1.tab1"  # From debug output: bridge target
    link_in_vnet_id = None
    for vnet_id, vnet in vnets.items():
        if link_in_tab in vnet.tab_ids:
            link_in_vnet_id = vnet_id
            print(f"  Internal Link IN tab {link_in_tab} is in VNET {vnet_id}")
            print(f"    VNET has {len(vnet.tab_ids)} tabs: {vnet.tab_ids}")
            print(f"    VNET state: {vnet.state}")
            break
    
    print()
   
    # Run initial simulation
    print("Running initial simulation...")
    result = engine.run()
    print(f"  Stable: {result.stable}")
    print(f"  Iterations: {result.iterations}")
    print()
    
    # Check initial states
    print("Initial states:")
    if switch:
        print(f"  Switch is_on: {switch._is_on}")
        for pin in switch.pins.values():
            print(f"    Pin {pin.pin_id}: {pin.state}")
    
    if subcircuit:
        for pin_id, pin in subcircuit.pins.items():
            print(f"  SubCircuit pin {pin_id}: {pin.state}")
    
    if indicator:
        for pin in indicator.pins.values():
            print(f"  Indicator pin {pin.pin_id}: {pin.state}")
    print()
    
    # Simulate pressing the switch
    print("Simulating switch press (setting to ON)...")
    if switch:
        switch._is_on = True  # Turn on
        # Mark switch tabs dirty
        for pin in switch.pins.values():
            pin.set_state(PinState.HIGH)
            for tab in pin.tabs.values():
                engine.vnet_manager.mark_tab_dirty(tab.tab_id)
    
    # Run simulation again
    print("Running simulation after switch press...")
    result = engine.run()
    print(f"  Stable: {result.stable}")
    print(f"  Iterations: {result.iterations}")
    
    # Wait for relay timer to complete (relay has 10ms switching delay)
    import time
    print("\nWaiting 50ms for relay timer...")
    time.sleep(0.05)  # Wait 50ms to be safe
    
    # Run simulation again to propagate relay contact changes
    print("Running simulation after relay timer...")
    result = engine.run()
    print(f"  Stable: {result.stable}")
    print(f"  Iterations: {result.iterations}")
    
    # Check VNET states after simulation
    print(f"\nVNET states after switch press:")
    for vnet_id in [sub_in_vnet_id, link_in_vnet_id]:
        if vnet_id:
            vnet = vnets.get(vnet_id)
            if vnet:
                print(f"  VNET {vnet_id}: {vnet.state}")
                print(f"    Tabs: {vnet.tab_ids}")
                print(f"    Bridges: {vnet.bridge_ids}")
    
    # Check ALL VNETs to see internal state
    print(f"\nALL VNET states (showing HIGH only):")
    for vnet_id, vnet in vnets.items():
        if vnet.state == PinState.HIGH:
            # Get first tab to show context
            first_tab = list(vnet.tab_ids)[0] if vnet.tab_ids else "no tabs"
            print(f"  VNET {vnet_id}: HIGH - {first_tab}")
    
    # Check relay coil specifically
    relay = components.get('78f462e5')
    if relay:
        print(f"\nRelay 78f462e5 state:")
        for pin_id, pin in relay.pins.items():
            pin_name = pin_id.split('.')[-1]
            # Get VNET for this pin's tab
            if pin.tabs:
                tab = list(pin.tabs.values())[0]
                vnet = None
                for v_id, v in vnets.items():
                    if tab.tab_id in v.tab_ids:
                        vnet = v
                        break
                vnet_state = vnet.state if vnet else "NO_VNET"
                print(f"  {pin_name}: pin.state={pin.state}, vnet.state={vnet_state}")
    print()
    
    # Check states after switch press
    print("States after switch press:")
    if switch:
        print(f"  Switch is_on: {switch._is_on}")
        for pin in switch.pins.values():
            print(f"    Pin {pin.pin_id}: {pin.state}")
    
    if subcircuit:
        for pin_id, pin in subcircuit.pins.items():
            print(f"  SubCircuit pin {pin_id}: {pin.state}")
    
    if indicator:
        for pin in indicator.pins.values():
            print(f"  Indicator pin {pin.pin_id}: {pin.state}")
    print()
    
    # Check if indicator is lit
    success = False
    if indicator:
        # Check VNET state, not pin state (indicator is passive)
        indicator_pin = list(indicator.pins.values())[0]
        indicator_tab = list(indicator_pin.tabs.values())[0]
        
        # Get VNET for indicator tab
        indicator_vnet = None
        for vnet_id, vnet in vnets.items():
            if indicator_tab.tab_id in vnet.tab_ids:
                indicator_vnet = vnet
                break
        
        print(f"Indicator VNET check:")
        print(f"  Indicator tab: {indicator_tab.tab_id}")
        if indicator_vnet:
            print(f"  VNET ID: {indicator_vnet.vnet_id}")
            print(f"  VNET state: {indicator_vnet.state}")
            print(f"  VNET tabs: {indicator_vnet.tab_ids}")
            print(f"  VNET bridges: {indicator_vnet.bridge_ids}")
            
            if indicator_vnet.state == PinState.HIGH:
                print("[OK] SUCCESS: Indicator VNET is HIGH!")
                success = True
            else:
                print("[OK] FAILURE: Indicator VNET is not HIGH")
        else:
            print("  ERROR: Could not find VNET for indicator")
    
    print("="*70)
    return success


if __name__ == "__main__":
    try:
        success = test_subcircuit_simulation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[OK] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


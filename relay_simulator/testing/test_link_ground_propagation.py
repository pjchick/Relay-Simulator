"""
Test for Link Ground Propagation Issue

Tests the scenario where ground propagation through Link objects is not working correctly.
"""

import sys
import os

# Add parent directory to path to import relay_simulator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fileio.document_loader import load_document
from core.vnet_builder import VnetBuilder
from core.link_resolver import LinkResolver


def test_link_ground_propagation():
    """Test that ground propagates correctly through Link objects."""
    print("\n=== Testing Link Ground Propagation ===")
    
    # Load the example file
    filepath = os.path.join(os.path.dirname(__file__), '..', '..', 'examples', 'Link Ground Propergation.rsim')
    doc = load_document(filepath)
    
    print(f"✓ Loaded document with {len(doc.get_all_pages())} page(s)")
    
    # Build VNETs for all pages
    builder = VnetBuilder()
    all_vnets = []
    for page in doc.get_all_pages():
        page_vnets = builder.build_vnets_for_page(page)
        all_vnets.extend(page_vnets)
    
    print(f"✓ Built {len(all_vnets)} VNETs")
    
    # Show VNET details before link resolution
    print("\nVNETs before link resolution:")
    for i, vnet in enumerate(all_vnets):
        tabs = vnet.get_all_tabs()
        print(f"  VNET {i+1}: {len(tabs)} tabs, links: {vnet.get_all_links()}")
        for tab_id in tabs:
            print(f"    - {tab_id}")
    
    # Resolve links
    resolver = LinkResolver()
    result = resolver.resolve_links(doc, all_vnets)
    
    print(f"\n✓ Link resolution: {result}")
    print(f"  Total links: {result.total_links}")
    print(f"  Resolved links: {result.resolved_links}")
    print(f"  VNETs with links: {result.vnets_with_links}")
    
    # Show VNET details after link resolution
    print("\nVNETs after link resolution:")
    for i, vnet in enumerate(all_vnets):
        tabs = vnet.get_all_tabs()
        links = vnet.get_all_links()
        print(f"  VNET {i+1}: {len(tabs)} tabs, links: {links}")
        for tab_id in tabs:
            print(f"    - {tab_id}")
    
    # Check for the specific issue
    print("\n=== Checking for Link components ===")
    for page in doc.get_all_pages():
        for component in page.get_all_components():
            if hasattr(component, 'component_type') and component.component_type == "Link":
                link_name = getattr(component, 'link_name', None)
                print(f"  Found Link: {component.component_id}, link_name: {link_name}")
                
                # Find which VNET contains this Link's tab
                for pin in component.get_all_pins().values():
                    for tab in pin.tabs.values():
                        for vnet in all_vnets:
                            if vnet.has_tab(tab.tab_id):
                                print(f"    Tab {tab.tab_id} is in VNET with links: {vnet.get_all_links()}")
    
    # Check for GND components
    print("\n=== Checking for GND components ===")
    for page in doc.get_all_pages():
        for component in page.get_all_components():
            if hasattr(component, 'component_type') and component.component_type == "GND":
                print(f"  Found GND: {component.component_id}")
                
                # Find which VNET contains this GND's tab
                for pin in component.get_all_pins().values():
                    for tab in pin.tabs.values():
                        for vnet in all_vnets:
                            if vnet.has_tab(tab.tab_id):
                                print(f"    Tab {tab.tab_id} is in VNET with links: {vnet.get_all_links()}")
    
    # Check for GroundDPDTRelay components
    print("\n=== Checking for GroundDPDTRelay components ===")
    for page in doc.get_all_pages():
        for component in page.get_all_components():
            if hasattr(component, 'component_type') and component.component_type == "GroundDPDTRelay":
                print(f"  Found GroundDPDTRelay: {component.component_id}")
                
                # Find which VNET contains the GND pin's tab
                gnd_pin = None
                for pin_name, pin in component.get_all_pins().items():
                    if pin_name.endswith('.GND'):
                        gnd_pin = pin
                        break
                
                if gnd_pin:
                    for tab in gnd_pin.tabs.values():
                        for vnet in all_vnets:
                            if vnet.has_tab(tab.tab_id):
                                print(f"    GND pin tab {tab.tab_id} is in VNET with links: {vnet.get_all_links()}")
    
    print("\n✓ Link ground propagation test complete")


if __name__ == "__main__":
    test_link_ground_propagation()

"""Check the latch circuit wiring."""
import json

# Load the file  
with open('examples/SubTest1.rsim', 'r') as f:
    doc = json.load(f)

# Find the internal logic page (not FOOTPRINT)
internal_page = None
for page in doc['pages']:
    if page.get('name') != 'FOOTPRINT' and any(c['component_type'] == 'DPDTRelay' for c in page.get('components', [])):
        internal_page = page
        break

if not internal_page:
    print("Could not find internal logic page")
    exit(1)

print(f"Internal page: {internal_page['page_id']} - {internal_page.get('name', 'Unnamed')}")
print()

# Find all components
print("Components:")
for comp in internal_page['components']:
    print(f"  {comp['component_id']}: {comp['component_type']}")
    if comp['component_type'] == 'Link':
        print(f"    link_name: {comp.get('link_name', 'NONE')}")
print()

# Find relay and show its pins
relay = [c for c in internal_page['components'] if c['component_type'] == 'DPDTRelay'][0]
print(f"Relay {relay['component_id']} pins:")
for pin in relay['pins']:
    pin_name = pin['pin_id'].split('.')[-1]  # Get just the pin name
    print(f"  {pin_name}")
print()

# Find wires and show connections
print("Wires:")
for wire in internal_page.get('wires', []):
    start = wire['start_tab_id']
    end = wire.get('end_tab_id', 'NONE')
    print(f"  {start} --> {end}")

"""
Repair Corrupted Sub-Circuit Instance Files

This script repairs .rsim files that have corrupted tab IDs in sub-circuit instance pages
caused by the ID regeneration bug. It reconstructs the correct tab IDs by mapping from
the template definition.
"""

import json
import sys
from pathlib import Path

def repair_subcircuit_file(filepath):
    """
    Repair corrupted tab IDs in sub-circuit instance wires.
    
    The bug caused tab IDs like "afccd56d.pin1.tab1" to become "afccd56d.ea5cfb12.3b9845c7"
    This script uses the template to reconstruct the correct pin/tab names.
    """
    print(f"Loading file: {filepath}")
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Get all sub-circuit definitions
    sub_circuits = data.get('sub_circuits', {})
    
    if not sub_circuits:
        print("No sub-circuits found in file")
        return False
    
    repairs_made = 0
    
    # Process each sub-circuit definition
    for sc_id, sc_def in sub_circuits.items():
        print(f"\nProcessing sub-circuit: {sc_def['name']} ({sc_id})")
        
        # Get template pages
        template_pages = {p['page_id']: p for p in sc_def['pages']}
        
        # Process each instance
        for inst_id, instance in sc_def.get('instances', {}).items():
            print(f"  Instance: {inst_id}")
            
            # Get page ID mapping (template -> instance)
            page_id_map = instance['page_id_map']
            
            # Build component ID mapping (template -> instance)
            comp_id_map = {}
            
            for template_page_id, instance_page_id in page_id_map.items():
                # Find the instance page in the document
                instance_page = None
                for page in data['pages']:
                    if page['page_id'] == instance_page_id:
                        instance_page = page
                        break
                
                if not instance_page:
                    continue
                
                template_page = template_pages.get(template_page_id)
                if not template_page:
                    continue
                
                # Build tab ID mapping: template tab ID → correct instance tab ID
                tab_id_map = {}
                
                for t_comp in template_page.get('components', []):
                    for i_comp in instance_page.get('components', []):
                        # Match components by type and position
                        if (t_comp['component_type'] == i_comp['component_type'] and
                            t_comp['position'] == i_comp['position']):
                            
                            comp_id_map[t_comp['component_id']] = i_comp['component_id']
                            
                            # Map all tabs from this component
                            for t_pin in t_comp.get('pins', []):
                                t_pin_id = t_pin['pin_id']
                                t_pin_parts = t_pin_id.split('.')
                                
                                # Extract pin name (everything after component ID)
                                t_pin_name = '.'.join(t_pin_parts[1:]) if len(t_pin_parts) > 1 else t_pin_id
                                
                                for t_tab in t_pin.get('tabs', []):
                                    t_tab_id = t_tab['tab_id']
                                    t_tab_parts = t_tab_id.split('.')
                                    
                                    # Reconstruct correct instance tab ID
                                    # Format: instance_comp_id.pin_name.tab_name
                                    if len(t_tab_parts) >= 3:
                                        pin_name = t_tab_parts[1]
                                        tab_name = '.'.join(t_tab_parts[2:])  # Handle multi-part tab names
                                        correct_instance_tab_id = f"{i_comp['component_id']}.{pin_name}.{tab_name}"
                                        tab_id_map[t_tab_id] = correct_instance_tab_id
                            
                            break  # Found matching component, move to next template component
                
                # Now repair wires in this instance page
                template_wires = template_page.get('wires', [])
                instance_wires = instance_page.get('wires', [])
                
                print(f"    Page: {template_page['name']} → {instance_page['name']}")
                print(f"      Template wires: {len(template_wires)}, Instance wires: {len(instance_wires)}")
                
                # Match wires by index (they should be in the same order)
                for idx, (t_wire, i_wire) in enumerate(zip(template_wires, instance_wires)):
                    # Get template tab IDs
                    template_start = t_wire.get('start_tab_id', '')
                    template_end = t_wire.get('end_tab_id', '')
                    
                    # Map to correct instance tab IDs
                    if template_start in tab_id_map:
                        correct_start = tab_id_map[template_start]
                        current_start = i_wire.get('start_tab_id', '')
                        
                        if current_start != correct_start:
                            print(f"      Wire {idx}: start {current_start} → {correct_start}")
                            i_wire['start_tab_id'] = correct_start
                            repairs_made += 1
                    
                    if template_end in tab_id_map:
                        correct_end = tab_id_map[template_end]
                        current_end = i_wire.get('end_tab_id', '')
                        
                        if current_end != correct_end:
                            print(f"      Wire {idx}: end {current_end} → {correct_end}")
                            i_wire['end_tab_id'] = correct_end
                            repairs_made += 1
    
    if repairs_made > 0:
        # Save repaired file
        backup_path = filepath.replace('.rsim', '_backup.rsim')
        print(f"\nCreating backup: {backup_path}")
        with open(backup_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saving repaired file: {filepath}")
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✓ Repaired {repairs_made} wire endpoints")
        return True
    else:
        print("\n✓ No repairs needed (file is already clean)")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python repair_subcircuit_file.py <path_to_rsim_file>")
        print("\nExample:")
        print("  python tools\\repair_subcircuit_file.py examples\\SubTest1.rsim")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not Path(filepath).exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    try:
        success = repair_subcircuit_file(filepath)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error repairing file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

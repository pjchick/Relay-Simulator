"""
Script to create example .rsim files from the example_files module.
"""

from pathlib import Path
import json

from fileio.example_files import (
    SIMPLE_SWITCH_LED,
    RELAY_CIRCUIT,
    CROSS_PAGE_LINKS,
    WIRE_WITH_JUNCTION,
    COMPLEX_CIRCUIT
)


def create_example_files(output_dir: str = '../examples'):
    """
    Create .rsim example files in the examples directory.
    
    Args:
        output_dir: Directory to create example files in
    """
    # Get absolute path
    script_dir = Path(__file__).parent
    examples_dir = (script_dir / output_dir).resolve()
    examples_dir.mkdir(exist_ok=True)
    
    # Define examples to create
    examples = [
        ('01_simple_switch_led.rsim', SIMPLE_SWITCH_LED),
        ('02_relay_circuit.rsim', RELAY_CIRCUIT),
        ('03_cross_page_links.rsim', CROSS_PAGE_LINKS),
        ('04_wire_with_junction.rsim', WIRE_WITH_JUNCTION),
        ('05_complex_circuit.rsim', COMPLEX_CIRCUIT)
    ]
    
    print(f"Creating example files in: {examples_dir}")
    
    for filename, json_string in examples:
        filepath = examples_dir / filename
        
        # Parse and re-format with proper indentation
        data = json.loads(json_string)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"  Created: {filename}")
    
    print(f"\nCreated {len(examples)} example files successfully!")


if __name__ == '__main__':
    create_example_files()

"""
Demo of OutputFormatter capabilities.
"""

from networking.output_formatter import (
    OutputFormatter,
    Alignment,
    ANSIColor,
    format_component_table,
    format_vnet_table
)


def demo_basic_table():
    """Demonstrate basic table formatting."""
    print("=== BASIC TABLE (ASCII, No Colors) ===\n")
    
    formatter = OutputFormatter(use_colors=False, use_unicode=False)
    
    headers = ['Component ID', 'Type', 'Page', 'State']
    rows = [
        ['SW1', 'Switch', 'Main', 'ON'],
        ['LED1', 'Indicator', 'Main', 'OFF'],
        ['RLY1', 'DPDT Relay', 'Control', 'Energized'],
        ['VCC1', 'VCC', 'Main', 'HIGH']
    ]
    
    table = formatter.format_table(headers, rows)
    print(table)
    print()


def demo_unicode_table():
    """Demonstrate Unicode box characters."""
    print("=== UNICODE TABLE ===\n")
    
    formatter = OutputFormatter(use_colors=False, use_unicode=True)
    
    headers = ['VNET ID', 'State', 'Tabs', 'Dirty']
    rows = [
        ['vnet_001', 'HIGH', '5', 'No'],
        ['vnet_002', 'FLOAT', '3', 'Yes'],
        ['vnet_003', 'HIGH', '8', 'No']
    ]
    
    alignments = [Alignment.LEFT, Alignment.CENTER, Alignment.RIGHT, Alignment.CENTER]
    table = formatter.format_table(headers, rows, alignments)
    print(table)
    print()


def demo_colored_table():
    """Demonstrate colored output."""
    print("=== COLORED TABLE ===\n")
    
    formatter = OutputFormatter(use_colors=True, use_unicode=True)
    
    headers = ['ID', 'Status', 'Count']
    rows = [
        [formatter.colorize('SW1', ANSIColor.CYAN), 
         formatter.colorize('ACTIVE', ANSIColor.GREEN), 
         '100'],
        [formatter.colorize('LED1', ANSIColor.CYAN), 
         formatter.colorize('INACTIVE', ANSIColor.RED), 
         '0'],
    ]
    
    table = formatter.format_table(headers, rows)
    print(table)
    print()


def demo_lists():
    """Demonstrate list formatting."""
    print("=== LISTS ===\n")
    
    formatter = OutputFormatter(use_colors=False)
    
    # Bulleted list
    print("Bulleted List:")
    items = ['Component commands', 'VNET commands', 'Debug commands']
    print(formatter.format_list(items))
    print()
    
    # Numbered list
    print("Numbered List:")
    steps = ['Load document', 'Build VNETs', 'Start simulation', 'Check status']
    print(formatter.format_list(steps, numbered=True))
    print()


def demo_key_value():
    """Demonstrate key-value formatting."""
    print("=== KEY-VALUE PAIRS ===\n")
    
    formatter = OutputFormatter(use_colors=True)
    
    data = {
        'Document': 'test.rsim',
        'Pages': 3,
        'Components': 15,
        'Simulation': 'Running',
        'Iterations': 1234
    }
    
    print(formatter.format_key_value(data))
    print()


def demo_sections():
    """Demonstrate section formatting."""
    print("=== SECTIONS ===\n")
    
    formatter = OutputFormatter(use_colors=True, use_unicode=True)
    
    # Component section
    comp_data = {
        'ID': 'SW1',
        'Type': 'Switch',
        'State': 'ON',
        'Position': '(100, 200)'
    }
    comp_content = formatter.format_key_value(comp_data)
    comp_section = formatter.format_section("Component Details", comp_content, ANSIColor.BLUE)
    print(comp_section)
    print()
    
    # Statistics section
    stats_table = formatter.format_table(
        ['Metric', 'Value'],
        [
            ['Total Iterations', '1,234'],
            ['Time to Stable', '0.045s'],
            ['Components Updated', '15']
        ],
        alignments=[Alignment.LEFT, Alignment.RIGHT]
    )
    stats_section = formatter.format_section("Simulation Statistics", stats_table, ANSIColor.GREEN)
    print(stats_section)
    print()


def demo_word_wrap():
    """Demonstrate word wrapping."""
    print("=== WORD WRAP ===\n")
    
    formatter = OutputFormatter(terminal_width=50, use_colors=False)
    
    long_text = ("This is a very long piece of text that needs to be wrapped "
                 "to fit within the terminal width of 50 characters. It should "
                 "break at word boundaries.")
    
    wrapped = formatter.word_wrap(long_text)
    print(wrapped)
    print()


def demo_convenience_functions():
    """Demonstrate convenience formatting functions."""
    print("=== CONVENIENCE FUNCTIONS ===\n")
    
    formatter = OutputFormatter(use_colors=False, use_unicode=True)
    
    # Component table
    print("Components:")
    components = [
        {'id': 'SW1', 'type': 'Switch', 'page': 'Main', 'state': 'ON'},
        {'id': 'LED1', 'type': 'Indicator', 'page': 'Main', 'state': 'OFF'},
        {'id': 'RLY1', 'type': 'DPDT Relay', 'page': 'Control', 'state': 'Energized'}
    ]
    print(format_component_table(formatter, components))
    print()
    
    # VNET table
    print("VNETs:")
    vnets = [
        {'id': 'vnet_001', 'state': 'HIGH', 'tabs': 5, 'dirty': False},
        {'id': 'vnet_002', 'state': 'FLOAT', 'tabs': 3, 'dirty': True}
    ]
    print(format_vnet_table(formatter, vnets))
    print()


def demo_complete_output():
    """Demonstrate a complete formatted output."""
    print("=== COMPLETE SIMULATION STATUS ===\n")
    
    formatter = OutputFormatter(use_colors=True, use_unicode=True, terminal_width=80)
    
    # Header
    title = formatter.colorize("Relay Simulator III - Status Report", ANSIColor.BOLD + ANSIColor.CYAN)
    print(title)
    print("=" * 80)
    print()
    
    # Document info
    doc_info = formatter.format_section(
        "Document Information",
        formatter.format_key_value({
            'Filename': 'control_circuit.rsim',
            'Pages': 2,
            'Components': 8,
            'Wires': 12
        }),
        ANSIColor.YELLOW
    )
    print(doc_info)
    print()
    
    # Simulation status
    sim_info = formatter.format_section(
        "Simulation Status",
        formatter.format_key_value({
            'State': formatter.colorize('RUNNING', ANSIColor.GREEN),
            'Mode': 'Normal',
            'Iterations': 1234,
            'Time to Stable': '0.045s',
            'Oscillating': formatter.colorize('No', ANSIColor.GREEN)
        }),
        ANSIColor.YELLOW
    )
    print(sim_info)
    print()
    
    # Component table
    components_section = formatter.format_section(
        "Active Components",
        format_component_table(formatter, [
            {'id': 'SW1', 'type': 'Switch', 'page': 'Main', 'state': 'ON'},
            {'id': 'RLY1', 'type': 'DPDT Relay', 'page': 'Main', 'state': 'Energized'},
            {'id': 'LED1', 'type': 'Indicator', 'page': 'Output', 'state': 'ON'}
        ]),
        ANSIColor.YELLOW
    )
    print(components_section)
    print()


if __name__ == '__main__':
    demo_basic_table()
    demo_unicode_table()
    demo_colored_table()
    demo_lists()
    demo_key_value()
    demo_sections()
    demo_word_wrap()
    demo_convenience_functions()
    print("\n" + "=" * 80 + "\n")
    demo_complete_output()

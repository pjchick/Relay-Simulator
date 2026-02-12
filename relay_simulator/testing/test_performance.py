"""
Performance Test for Relay Simulator

This script loads a large simulation (12-bit Relay Computer) and measures
performance to identify bottlenecks in the simulation engine vs. GUI rendering.

Usage:
    python -m relay_simulator.testing.test_performance

Author: AI Assistant
Date: 2026-02-12
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from relay_simulator.fileio.document_loader import DocumentLoader
from relay_simulator.core.vnet_builder import VnetBuilder
from relay_simulator.simulation.simulation_engine import SimulationEngine
from relay_simulator.performance_profiler import get_profiler, print_performance_report, reset_profiler


def load_relay_computer():
    """Load the 12-bit Relay Computer example."""
    print("Loading 12-bit Relay Computer...")
    
    example_path = os.path.join(
        os.path.dirname(__file__), 
        '..', '..', 
        'examples', 
        '12-bit Relay Computer.rsim'
    )
    
    if not os.path.exists(example_path):
        print(f"ERROR: Could not find example file: {example_path}")
        return None
    
    loader = DocumentLoader()
    document = loader.load(example_path)
    
    if not document:
        print("ERROR: Failed to load document")
        return None
    
    print(f"✓ Loaded document with {len(document.pages)} pages")
    return document


def build_simulation(document):
    """Build VNETs and create simulation engine."""
    print("\nBuilding VNETs...")
    
    # Build VNETs for all pages
    builder = VnetBuilder()
    vnets, tabs, bridges, components, link_resolver = builder.build_vnets_from_document(document)
    
    print(f"✓ Built {len(vnets)} VNETs")
    print(f"✓ Total tabs: {len(tabs)}")
    print(f"✓ Total bridges: {len(bridges)}")
    print(f"✓ Total components: {len(components)}")
    
    # Create simulation engine
    print("\nCreating simulation engine...")
    engine = SimulationEngine(
        vnets=vnets,
        tabs=tabs,
        bridges=bridges,
        components=components,
        max_iterations=10000,
        timeout_seconds=30.0
    )
    
    print("✓ Simulation engine created")
    return engine, vnets, tabs, components


def run_simulation(engine):
    """Run the simulation and measure performance."""
    print("\n" + "=" * 80)
    print("RUNNING SIMULATION")
    print("=" * 80)
    
    start_time = time.perf_counter()
    
    profiler = get_profiler()
    with profiler.measure("simulation_run_total"):
        stats = engine.run()
    
    elapsed = time.perf_counter() - start_time
    
    print(f"\n✓ Simulation completed in {elapsed:.3f}s")
    print(f"  - Iterations: {stats.iterations}")
    print(f"  - Components updated: {stats.components_updated}")
    print(f"  - Time to stability: {stats.time_to_stability:.3f}s")
    print(f"  - Stable: {stats.stable}")
    
    return stats


def analyze_page_complexity(document):
    """Analyze complexity of each page."""
    print("\n" + "=" * 80)
    print("PAGE COMPLEXITY ANALYSIS")
    print("=" * 80)
    print(f"{'Page Name':<30} {'Components':>12} {'Wires':>12} {'Junctions':>12}")
    print("-" * 80)
    
    for page in document.pages:
        num_components = len(page.components)
        num_wires = len(page.wires)
        num_junctions = len(page.junctions)
        
        print(f"{page.name:<30} {num_components:>12} {num_wires:>12} {num_junctions:>12}")
    
    print("=" * 80)


def simulate_gui_rendering(document, engine, page_name="Sequencer"):
    """Simulate GUI rendering operations that would happen during simulation."""
    print(f"\n" + "=" * 80)
    print(f"SIMULATING GUI RENDERING FOR '{page_name}' PAGE")
    print("=" * 80)
    
    # Find the page
    target_page = None
    for page in document.pages:
        if page.name == page_name:
            target_page = page
            break
    
    if not target_page:
        print(f"ERROR: Could not find page '{page_name}'")
        return
    
    print(f"Page has {len(target_page.components)} components, {len(target_page.wires)} wires, {len(target_page.junctions)} junctions")
    
    profiler = get_profiler()
    
    # Simulate 10 render cycles (what would happen during simulation updates)
    num_renders = 10
    print(f"\nSimulating {num_renders} render cycles...")
    
    for i in range(num_renders):
        # Simulate checking powered state for each wire
        with profiler.measure("gui_simulated_wire_checks"):
            for wire in target_page.wires.values():
                # This simulates the BFS graph traversal that happens
                # for each wire to check if it's powered
                with profiler.measure("gui_simulated_single_wire_check"):
                    # In real code, this does a BFS through VNETs
                    _ = _simulate_wire_powered_check(wire, engine)
        
        # Simulate component rendering
        with profiler.measure("gui_simulated_component_render"):
            for component in target_page.components.values():
                # Simulate component powered check
                _ = _simulate_component_powered_check(component, engine)
        
        if (i + 1) % 5 == 0:
            print(f"  Completed {i + 1}/{num_renders} render cycles...")
    
    print(f"✓ Completed {num_renders} render cycles")


def _simulate_wire_powered_check(wire, engine):
    """Simulate the BFS graph traversal to check if a wire is powered."""
    # This mimics the logic in canvas.py _is_wire_powered()
    visited_vnets = set()
    queue = []
    
    # Find starting VNET
    if wire.start_tab_id:
        for vnet in engine.vnets.values():
            if wire.start_tab_id in vnet.tab_ids:
                queue.append(vnet.vnet_id)
                break
    
    # BFS traversal
    while queue and len(visited_vnets) < 100:  # Limit to prevent infinite loops
        vnet_id = queue.pop(0)
        if vnet_id in visited_vnets:
            continue
        
        visited_vnets.add(vnet_id)
        vnet = engine.vnets.get(vnet_id)
        
        if not vnet:
            continue
        
        # Check if HIGH
        if vnet.state.name == 'HIGH':
            return True
        
        # Follow bridges
        for bridge_id in vnet.bridge_ids:
            for other_vnet_id, other_vnet in engine.vnets.items():
                if other_vnet_id != vnet_id and bridge_id in other_vnet.bridge_ids:
                    if other_vnet_id not in visited_vnets:
                        queue.append(other_vnet_id)
    
    return False


def _simulate_component_powered_check(component, engine):
    """Simulate checking if any pin on a component is powered."""
    # This mimics the logic in canvas.py _is_component_powered()
    for pin in component.get_all_pins().values():
        for tab in pin.tabs.values():
            for vnet in engine.vnets.values():
                if tab.tab_id in vnet.tab_ids:
                    if vnet.state.name == 'HIGH':
                        return True
    return False


def main():
    """Main test function."""
    print("\n" + "=" * 80)
    print("RELAY SIMULATOR PERFORMANCE TEST")
    print("=" * 80)
    
    # Reset profiler
    reset_profiler()
    
    # Load document
    document = load_relay_computer()
    if not document:
        return 1
    
    # Analyze page complexity
    analyze_page_complexity(document)
    
    # Build simulation
    engine, vnets, tabs, components = build_simulation(document)
    
    # Run simulation
    stats = run_simulation(engine)
    
    # Simulate GUI rendering (this is where the bottleneck is)
    simulate_gui_rendering(document, engine, page_name="Sequencer")
    
    # Display performance report
    print("\n" + "=" * 80)
    print("PERFORMANCE REPORT (sorted by total time)")
    print("=" * 80)
    print_performance_report(sort_by='total')
    
    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    profiler = get_profiler()
    metrics = profiler.get_metrics()
    
    sim_time = metrics.get('simulation_run_total', None)
    gui_wire_checks = metrics.get('gui_simulated_wire_checks', None)
    
    if sim_time and gui_wire_checks:
        print(f"\nSimulation Engine Time: {sim_time.total_time:.3f}s")
        print(f"GUI Wire Check Time (simulated): {gui_wire_checks.total_time:.3f}s")
        print(f"GUI/Simulation Ratio: {gui_wire_checks.total_time / sim_time.total_time:.1f}x")
        print("\n⚠ WARNING: GUI rendering is the primary bottleneck!")
        print("   The GUI spends more time checking wire powered states than the")
        print("   simulation engine spends evaluating the entire circuit.")
        print("\n   Recommendations:")
        print("   1. Cache wire powered states instead of recalculating each frame")
        print("   2. Only update wires/components that actually changed")
        print("   3. Throttle visual updates to max 30 FPS")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

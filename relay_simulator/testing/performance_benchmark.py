"""
Performance Benchmarking Suite (Phase 5.4)

Comprehensive performance testing for the relay simulator engine.
Tests single-threaded vs multi-threaded performance with varying
component counts and circuit complexities.

Author: Cascade AI
Date: 2025-12-10
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import statistics
from typing import Dict, List, Tuple
from dataclasses import dataclass

from core.vnet import VNET
from core.tab import Tab
from core.pin import Pin
from core.bridge import Bridge
from components.switch import Switch
from components.indicator import Indicator
from components.dpdt_relay import DPDTRelay
from components.vcc import VCC
from simulation.simulation_engine import SimulationEngine
from simulation.threaded_simulation_engine import ThreadedSimulationEngine


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    component_count: int
    vnet_count: int
    iterations: int
    time_to_stability: float
    total_time: float
    components_updated: int
    thread_count: int
    engine_type: str
    
    def throughput(self) -> float:
        """Calculate iterations per second."""
        return self.iterations / self.total_time if self.total_time > 0 else 0
    
    def updates_per_second(self) -> float:
        """Calculate component updates per second."""
        return self.components_updated / self.total_time if self.total_time > 0 else 0


class PerformanceBenchmark:
    """
    Performance benchmarking suite for simulation engines.
    
    Tests various circuit sizes and configurations to measure
    performance characteristics and compare single vs multi-threaded
    execution.
    """
    
    def __init__(self):
        """Initialize benchmark suite."""
        self.results: List[BenchmarkResult] = []
    
    def create_simple_chain(self, count: int) -> Tuple[Dict, Dict, Dict, Dict]:
        """
        Create a simple chain circuit: VCC → Switch → Indicator (repeated).
        
        Args:
            count: Number of switch-indicator pairs
            
        Returns:
            Tuple of (vnets, tabs, bridges, components)
        """
        components = {}
        vnets = {}
        tabs = {}
        bridges = {}
        
        # Create VCC source
        vcc = VCC(f"VCC_000", "PAGE1")
        vcc_pin = Pin("VCC_PIN", vcc)
        vcc.add_pin(vcc_pin)
        components["VCC_000"] = vcc
        
        # Create VCC VNET
        vcc_vnet = VNET("VNET_VCC")
        vcc_tab = Tab(f"VCC_TAB", vcc_pin, (0, 0))
        vcc_vnet.add_tab(vcc_tab.tab_id)
        tabs[vcc_tab.tab_id] = vcc_tab
        vnets["VNET_VCC"] = vcc_vnet
        
        # Create chain of switches and indicators
        for i in range(count):
            # Create switch
            switch = Switch(f"SW_{i:04d}", "PAGE1")
            sw_pin = Pin(f"SW_PIN_{i:04d}", switch)
            switch.add_pin(sw_pin)
            components[f"SW_{i:04d}"] = switch
            
            # Create indicator
            indicator = Indicator(f"IND_{i:04d}", "PAGE1")
            ind_pin = Pin(f"IND_PIN_{i:04d}", indicator)
            indicator.add_pin(ind_pin)
            components[f"IND_{i:04d}"] = indicator
            
            # Create VNETs
            sw_vnet = VNET(f"VNET_SW_{i:04d}")
            ind_vnet = VNET(f"VNET_IND_{i:04d}")
            
            # Add tabs
            sw_tab = Tab(f"SW_TAB_{i:04d}", sw_pin, (0, 0))
            ind_tab = Tab(f"IND_TAB_{i:04d}", ind_pin, (0, 0))
            
            sw_vnet.add_tab(sw_tab.tab_id)
            ind_vnet.add_tab(ind_tab.tab_id)
            
            tabs[sw_tab.tab_id] = sw_tab
            tabs[ind_tab.tab_id] = ind_tab
            
            vnets[f"VNET_SW_{i:04d}"] = sw_vnet
            vnets[f"VNET_IND_{i:04d}"] = ind_vnet
            
            # Connect VCC to each switch (parallel)
            vcc_vnet.add_tab(sw_tab.tab_id)
        
        return vnets, tabs, bridges, components
    
    def create_relay_ladder(self, count: int) -> Tuple[Dict, Dict, Dict, Dict]:
        """
        Create a relay ladder circuit with interlocking logic.
        
        Args:
            count: Number of relays in ladder
            
        Returns:
            Tuple of (vnets, tabs, bridges, components)
        """
        components = {}
        vnets = {}
        tabs = {}
        bridges = {}
        
        # Create VCC
        vcc = VCC("VCC_000", "PAGE1")
        vcc_pin = Pin("VCC_PIN", vcc)
        vcc.add_pin(vcc_pin)
        components["VCC_000"] = vcc
        
        vcc_vnet = VNET("VNET_VCC")
        vcc_tab = Tab("VCC_TAB", vcc_pin, (0, 0))
        vcc_vnet.add_tab(vcc_tab.tab_id)
        tabs[vcc_tab.tab_id] = vcc_tab
        vnets["VNET_VCC"] = vcc_vnet
        
        # Create master switch
        master_sw = Switch("SW_MASTER", "PAGE1")
        master_pin = Pin("SW_MASTER_PIN", master_sw)
        master_sw.add_pin(master_pin)
        components["SW_MASTER"] = master_sw
        
        master_vnet = VNET("VNET_MASTER")
        master_tab = Tab("SW_MASTER_TAB", master_pin, (0, 0))
        master_vnet.add_tab(master_tab.tab_id)
        tabs[master_tab.tab_id] = master_tab
        vnets["VNET_MASTER"] = master_vnet
        
        # Connect VCC to master switch
        vcc_vnet.add_tab(master_tab.tab_id)
        
        # Create relay ladder
        prev_vnet = master_vnet
        
        for i in range(count):
            # Create relay
            relay = DPDTRelay(f"RLY_{i:04d}", "PAGE1")
            
            # Create pins
            coil_pin = Pin(f"COIL_{i:04d}", relay)
            com1_pin = Pin(f"COM1_{i:04d}", relay)
            no1_pin = Pin(f"NO1_{i:04d}", relay)
            nc1_pin = Pin(f"NC1_{i:04d}", relay)
            com2_pin = Pin(f"COM2_{i:04d}", relay)
            no2_pin = Pin(f"NO2_{i:04d}", relay)
            nc2_pin = Pin(f"NC2_{i:04d}", relay)
            
            relay.add_pin(coil_pin)
            relay.add_pin(com1_pin)
            relay.add_pin(no1_pin)
            relay.add_pin(nc1_pin)
            relay.add_pin(com2_pin)
            relay.add_pin(no2_pin)
            relay.add_pin(nc2_pin)
            
            components[f"RLY_{i:04d}"] = relay
            
            # Create VNETs
            coil_vnet = VNET(f"VNET_COIL_{i:04d}")
            com1_vnet = VNET(f"VNET_COM1_{i:04d}")
            no1_vnet = VNET(f"VNET_NO1_{i:04d}")
            nc1_vnet = VNET(f"VNET_NC1_{i:04d}")
            com2_vnet = VNET(f"VNET_COM2_{i:04d}")
            no2_vnet = VNET(f"VNET_NO2_{i:04d}")
            nc2_vnet = VNET(f"VNET_NC2_{i:04d}")
            
            # Create tabs
            coil_tab = Tab(f"COIL_TAB_{i:04d}", coil_pin, (0, 0))
            com1_tab = Tab(f"COM1_TAB_{i:04d}", com1_pin, (0, 0))
            no1_tab = Tab(f"NO1_TAB_{i:04d}", no1_pin, (0, 0))
            nc1_tab = Tab(f"NC1_TAB_{i:04d}", nc1_pin, (0, 0))
            com2_tab = Tab(f"COM2_TAB_{i:04d}", com2_pin, (0, 0))
            no2_tab = Tab(f"NO2_TAB_{i:04d}", no2_pin, (0, 0))
            nc2_tab = Tab(f"NC2_TAB_{i:04d}", nc2_pin, (0, 0))
            
            # Add tabs to VNETs
            coil_vnet.add_tab(coil_tab.tab_id)
            com1_vnet.add_tab(com1_tab.tab_id)
            no1_vnet.add_tab(no1_tab.tab_id)
            nc1_vnet.add_tab(nc1_tab.tab_id)
            com2_vnet.add_tab(com2_tab.tab_id)
            no2_vnet.add_tab(no2_tab.tab_id)
            nc2_vnet.add_tab(nc2_tab.tab_id)
            
            # Store tabs
            tabs[coil_tab.tab_id] = coil_tab
            tabs[com1_tab.tab_id] = com1_tab
            tabs[no1_tab.tab_id] = no1_tab
            tabs[nc1_tab.tab_id] = nc1_tab
            tabs[com2_tab.tab_id] = com2_tab
            tabs[no2_tab.tab_id] = no2_tab
            tabs[nc2_tab.tab_id] = nc2_tab
            
            # Store VNETs
            vnets[f"VNET_COIL_{i:04d}"] = coil_vnet
            vnets[f"VNET_COM1_{i:04d}"] = com1_vnet
            vnets[f"VNET_NO1_{i:04d}"] = no1_vnet
            vnets[f"VNET_NC1_{i:04d}"] = nc1_vnet
            vnets[f"VNET_COM2_{i:04d}"] = com2_vnet
            vnets[f"VNET_NO2_{i:04d}"] = no2_vnet
            vnets[f"VNET_NC2_{i:04d}"] = nc2_vnet
            
            # Connect coil to previous stage
            prev_vnet.add_tab(coil_tab.tab_id)
            
            # Connect COM1 to VCC
            vcc_vnet.add_tab(com1_tab.tab_id)
            
            # Chain to next relay via NO1
            prev_vnet = no1_vnet
            
            # Create indicator for this relay
            indicator = Indicator(f"IND_{i:04d}", "PAGE1")
            ind_pin = Pin(f"IND_PIN_{i:04d}", indicator)
            indicator.add_pin(ind_pin)
            components[f"IND_{i:04d}"] = indicator
            
            ind_vnet = VNET(f"VNET_IND_{i:04d}")
            ind_tab = Tab(f"IND_TAB_{i:04d}", ind_pin, (0, 0))
            ind_vnet.add_tab(ind_tab.tab_id)
            tabs[ind_tab.tab_id] = ind_tab
            vnets[f"VNET_IND_{i:04d}"] = ind_vnet
            
            # Connect indicator to NO2
            no2_vnet.add_tab(ind_tab.tab_id)
        
        return vnets, tabs, bridges, components
    
    def run_benchmark(
        self,
        engine_type: str,
        component_count: int,
        circuit_type: str = "chain",
        thread_count: int = None,
        runs: int = 3
    ) -> BenchmarkResult:
        """
        Run a single benchmark scenario.
        
        Args:
            engine_type: "single" or "threaded"
            component_count: Number of components to create
            circuit_type: "chain" or "ladder"
            thread_count: Thread count (for threaded engine)
            runs: Number of runs to average
            
        Returns:
            BenchmarkResult with averaged metrics
        """
        times = []
        iterations_list = []
        components_updated_list = []
        
        for run in range(runs):
            # Create circuit
            if circuit_type == "chain":
                vnets, tabs, bridges, components = self.create_simple_chain(component_count)
            else:
                vnets, tabs, bridges, components = self.create_relay_ladder(component_count)
            
            # Create engine
            if engine_type == "single":
                engine = SimulationEngine(vnets, tabs, bridges, components)
            else:
                engine = ThreadedSimulationEngine(
                    vnets, tabs, bridges, components,
                    thread_count=thread_count
                )
            
            # Initialize and run
            engine.initialize()
            
            start_time = time.perf_counter()
            stats = engine.run()
            end_time = time.perf_counter()
            
            elapsed = end_time - start_time
            
            times.append(elapsed)
            iterations_list.append(stats.iterations)
            components_updated_list.append(stats.components_updated)
            
            # Shutdown
            engine.shutdown()
        
        # Calculate averages
        avg_time = statistics.mean(times)
        avg_iterations = statistics.mean(iterations_list)
        avg_updates = statistics.mean(components_updated_list)
        
        return BenchmarkResult(
            component_count=len(components),
            vnet_count=len(vnets),
            iterations=int(avg_iterations),
            time_to_stability=avg_time,
            total_time=avg_time,
            components_updated=int(avg_updates),
            thread_count=thread_count if engine_type == "threaded" else 1,
            engine_type=engine_type
        )
    
    def run_scaling_test(self):
        """Test performance scaling with different component counts."""
        print("\n" + "="*70)
        print("PERFORMANCE SCALING TEST")
        print("="*70)
        print("\nTesting component counts: 10, 50, 100, 500")
        print("Circuit type: Simple chain (VCC → Switch → Indicator)")
        print("Runs per test: 3 (averaged)\n")
        
        counts = [10, 50, 100, 500]
        
        for count in counts:
            print(f"\n--- Testing {count} components ---")
            
            # Single-threaded
            print("Running single-threaded... ", end="", flush=True)
            result_single = self.run_benchmark("single", count, "chain")
            self.results.append(result_single)
            print(f"✓ {result_single.total_time:.4f}s")
            
            # Multi-threaded (4 threads)
            print("Running multi-threaded (4 threads)... ", end="", flush=True)
            result_multi = self.run_benchmark("threaded", count, "chain", thread_count=4)
            self.results.append(result_multi)
            print(f"✓ {result_multi.total_time:.4f}s")
            
            # Calculate speedup
            speedup = result_single.total_time / result_multi.total_time
            print(f"Speedup: {speedup:.2f}x")
    
    def run_thread_scaling_test(self):
        """Test performance with different thread counts."""
        print("\n" + "="*70)
        print("THREAD SCALING TEST")
        print("="*70)
        print("\nTesting thread counts: 1, 2, 4, 8, 16")
        print("Components: 100")
        print("Circuit type: Simple chain\n")
        
        thread_counts = [1, 2, 4, 8, 16]
        
        for threads in thread_counts:
            print(f"Testing {threads} thread(s)... ", end="", flush=True)
            result = self.run_benchmark("threaded", 100, "chain", thread_count=threads)
            self.results.append(result)
            print(f"✓ {result.total_time:.4f}s ({result.throughput():.1f} iter/s)")
    
    def run_circuit_complexity_test(self):
        """Test performance with different circuit complexities."""
        print("\n" + "="*70)
        print("CIRCUIT COMPLEXITY TEST")
        print("="*70)
        print("\nComparing simple chain vs relay ladder")
        print("Components: 50\n")
        
        # Chain circuit
        print("Simple chain (single-threaded)... ", end="", flush=True)
        result_chain_single = self.run_benchmark("single", 50, "chain")
        self.results.append(result_chain_single)
        print(f"✓ {result_chain_single.total_time:.4f}s")
        
        print("Simple chain (multi-threaded, 4 threads)... ", end="", flush=True)
        result_chain_multi = self.run_benchmark("threaded", 50, "chain", thread_count=4)
        self.results.append(result_chain_multi)
        print(f"✓ {result_chain_multi.total_time:.4f}s")
        
        # Ladder circuit
        print("\nRelay ladder (single-threaded)... ", end="", flush=True)
        result_ladder_single = self.run_benchmark("single", 10, "ladder")
        self.results.append(result_ladder_single)
        print(f"✓ {result_ladder_single.total_time:.4f}s")
        
        print("Relay ladder (multi-threaded, 4 threads)... ", end="", flush=True)
        result_ladder_multi = self.run_benchmark("threaded", 10, "ladder", thread_count=4)
        self.results.append(result_ladder_multi)
        print(f"✓ {result_ladder_multi.total_time:.4f}s")
    
    def print_summary(self):
        """Print comprehensive summary of all results."""
        print("\n" + "="*70)
        print("BENCHMARK SUMMARY")
        print("="*70)
        
        print("\n{:<15} {:<10} {:<10} {:<12} {:<15} {:<12}".format(
            "Engine", "Components", "Threads", "Time (s)", "Iterations", "Iter/s"
        ))
        print("-" * 70)
        
        for result in self.results:
            print("{:<15} {:<10} {:<10} {:<12.4f} {:<15} {:<12.1f}".format(
                result.engine_type,
                result.component_count,
                result.thread_count,
                result.total_time,
                result.iterations,
                result.throughput()
            ))
        
        # Find best performance
        print("\n" + "="*70)
        print("KEY FINDINGS")
        print("="*70)
        
        # Best single-threaded
        single_results = [r for r in self.results if r.engine_type == "single"]
        if single_results:
            best_single = min(single_results, key=lambda r: r.total_time)
            print(f"\nBest single-threaded: {best_single.component_count} components")
            print(f"  Time: {best_single.total_time:.4f}s")
            print(f"  Throughput: {best_single.throughput():.1f} iterations/s")
        
        # Best multi-threaded
        multi_results = [r for r in self.results if r.engine_type == "threaded"]
        if multi_results:
            best_multi = min(multi_results, key=lambda r: r.total_time)
            print(f"\nBest multi-threaded: {best_multi.component_count} components, {best_multi.thread_count} threads")
            print(f"  Time: {best_multi.total_time:.4f}s")
            print(f"  Throughput: {best_multi.throughput():.1f} iterations/s")
        
        # Calculate average speedup
        if single_results and multi_results:
            # Match by component count
            speedups = []
            for sr in single_results:
                matching = [mr for mr in multi_results if mr.component_count == sr.component_count]
                if matching:
                    best_match = min(matching, key=lambda r: r.total_time)
                    speedup = sr.total_time / best_match.total_time
                    speedups.append(speedup)
            
            if speedups:
                avg_speedup = statistics.mean(speedups)
                max_speedup = max(speedups)
                print(f"\nAverage speedup: {avg_speedup:.2f}x")
                print(f"Maximum speedup: {max_speedup:.2f}x")


def main():
    """Run complete benchmark suite."""
    print("\n" + "="*70)
    print("RELAY SIMULATOR PERFORMANCE BENCHMARK SUITE")
    print("Phase 5.4: Performance Optimization")
    print("="*70)
    
    benchmark = PerformanceBenchmark()
    
    # Run all tests
    benchmark.run_scaling_test()
    benchmark.run_thread_scaling_test()
    benchmark.run_circuit_complexity_test()
    
    # Print summary
    benchmark.print_summary()
    
    print("\n" + "="*70)
    print("BENCHMARK COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

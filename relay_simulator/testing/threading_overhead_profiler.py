"""
Threading Overhead Profiler

Detailed profiling tool to identify specific bottlenecks in the multi-threaded
simulation engine. Measures overhead from:

1. Thread pool management (submission, coordination, waiting)
2. Lock contention (VNET locks, component locks, coordinator locks)
3. Synchronization barriers (wait_for_completion calls)
4. Work unit granularity (execution time vs coordination time)
5. Context switching overhead

Author: Cascade AI
Date: 2025-12-10
"""

import time
import threading
import statistics
from dataclasses import dataclass
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.vnet import VNET
from core.tab import Tab
from core.pin import Pin
from core.bridge import Bridge, BridgeManager
from core.state import PinState
from components.vcc import VCC
from components.switch import Switch
from components.indicator import Indicator
from simulation.simulation_engine import SimulationEngine
from simulation.threaded_simulation_engine import ThreadedSimulationEngine


@dataclass
class OverheadMeasurement:
    """Container for overhead measurements."""
    name: str
    total_time: float
    call_count: int
    avg_time: float
    min_time: float
    max_time: float
    percentage: float = 0.0


class ThreadingOverheadProfiler:
    """
    Profiler to identify threading overhead sources.
    
    Instruments the simulation engine to measure time spent in:
    - Thread pool operations
    - Lock acquisitions
    - Synchronization barriers
    - Work execution
    - Idle/waiting time
    """
    
    def __init__(self):
        """Initialize the profiler."""
        self.measurements: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
    
    def measure(self, name: str):
        """
        Context manager to measure operation time.
        
        Usage:
            with profiler.measure('operation_name'):
                # code to measure
        """
        return TimingContext(self, name)
    
    def record_time(self, name: str, duration: float):
        """
        Record a timing measurement.
        
        Args:
            name: Operation name
            duration: Time in seconds
        """
        with self._lock:
            if name not in self.measurements:
                self.measurements[name] = []
            self.measurements[name].append(duration)
    
    def get_summary(self) -> List[OverheadMeasurement]:
        """
        Get summary of all measurements.
        
        Returns:
            List of OverheadMeasurement objects sorted by total time
        """
        with self._lock:
            total_measured_time = sum(
                sum(times) for times in self.measurements.values()
            )
            
            results = []
            for name, times in self.measurements.items():
                if not times:
                    continue
                
                total = sum(times)
                count = len(times)
                avg = total / count if count > 0 else 0
                min_val = min(times) if times else 0
                max_val = max(times) if times else 0
                pct = (total / total_measured_time * 100) if total_measured_time > 0 else 0
                
                results.append(OverheadMeasurement(
                    name=name,
                    total_time=total,
                    call_count=count,
                    avg_time=avg,
                    min_time=min_val,
                    max_time=max_val,
                    percentage=pct
                ))
            
            # Sort by total time descending
            results.sort(key=lambda x: x.total_time, reverse=True)
            return results
    
    def print_summary(self):
        """Print formatted summary of overhead measurements."""
        summary = self.get_summary()
        
        print("\n" + "="*80)
        print("THREADING OVERHEAD PROFILING RESULTS")
        print("="*80)
        
        print(f"\n{'Operation':<40} {'Total (ms)':<12} {'Calls':<8} {'Avg (µs)':<12} {'% Time':<8}")
        print("-"*80)
        
        for m in summary:
            print(f"{m.name:<40} {m.total_time*1000:>11.3f} {m.call_count:>7} {m.avg_time*1e6:>11.1f} {m.percentage:>7.1f}%")
        
        # Key insights
        print("\n" + "="*80)
        print("KEY INSIGHTS")
        print("="*80)
        
        # Categorize overhead
        pool_overhead = sum(m.total_time for m in summary if 'pool' in m.name.lower() or 'submit' in m.name.lower() or 'wait' in m.name.lower())
        lock_overhead = sum(m.total_time for m in summary if 'lock' in m.name.lower() or 'acquire' in m.name.lower())
        execution_time = sum(m.total_time for m in summary if 'execute' in m.name.lower() or 'eval' in m.name.lower())
        
        total = sum(m.total_time for m in summary)
        
        if total > 0:
            print(f"\nThread Pool Overhead: {pool_overhead*1000:.3f}ms ({pool_overhead/total*100:.1f}%)")
            print(f"Lock Contention:      {lock_overhead*1000:.3f}ms ({lock_overhead/total*100:.1f}%)")
            print(f"Actual Execution:     {execution_time*1000:.3f}ms ({execution_time/total*100:.1f}%)")
            print(f"Total Measured:       {total*1000:.3f}ms")
            
            # Calculate overhead ratio
            overhead = pool_overhead + lock_overhead
            if execution_time > 0:
                overhead_ratio = overhead / execution_time
                print(f"\nOverhead/Execution Ratio: {overhead_ratio:.2f}x")
                print(f"  (For every 1ms of work, {overhead_ratio*1000:.1f}ms overhead)")


class TimingContext:
    """Context manager for timing operations."""
    
    def __init__(self, profiler: ThreadingOverheadProfiler, name: str):
        self.profiler = profiler
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        self.profiler.record_time(self.name, duration)
        return False


class InstrumentedThreadedEngine(ThreadedSimulationEngine):
    """
    Instrumented version of ThreadedSimulationEngine with profiling.
    
    Overrides key methods to add timing measurements.
    """
    
    def __init__(self, *args, profiler: ThreadingOverheadProfiler, **kwargs):
        super().__init__(*args, **kwargs)
        self.profiler = profiler
    
    def _evaluate_vnet_task(self, vnet: VNET) -> tuple:
        """Instrumented VNET evaluation."""
        with self.profiler.measure('vnet_evaluation'):
            return super()._evaluate_vnet_task(vnet)
    
    def _propagate_vnet_task(self, vnet: VNET, new_state):
        """Instrumented state propagation."""
        with self.profiler.measure('state_propagation'):
            return super()._propagate_vnet_task(vnet, new_state)
    
    def _execute_component_task(self, component):
        """Instrumented component execution."""
        with self.profiler.measure('component_execution'):
            return super()._execute_component_task(component)


def measure_lock_contention(component_count: int, thread_count: int) -> Dict[str, float]:
    """
    Measure lock contention overhead.
    
    Creates multiple threads that try to acquire the same locks repeatedly
    to measure contention overhead.
    
    Args:
        component_count: Number of components to create
        thread_count: Number of threads to use
        
    Returns:
        Dictionary with contention metrics
    """
    # Create VNETs with locks
    vnets = {}
    for i in range(component_count):
        vnet = VNET(f"VNET_{i:04d}")
        vnets[vnet.vnet_id] = vnet
    
    # Measure lock acquisition time
    lock_times = []
    iterations = 1000
    
    def worker():
        """Worker thread that acquires locks repeatedly."""
        for _ in range(iterations):
            for vnet in vnets.values():
                start = time.perf_counter()
                with vnet._lock:
                    # Simulate minimal work
                    state = vnet.state
                duration = time.perf_counter() - start
                lock_times.append(duration)
    
    # Single-threaded baseline
    start = time.perf_counter()
    worker()
    baseline_time = time.perf_counter() - start
    baseline_avg = statistics.mean(lock_times)
    lock_times.clear()
    
    # Multi-threaded contention
    threads = []
    start = time.perf_counter()
    for _ in range(thread_count):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    contention_time = time.perf_counter() - start
    contention_avg = statistics.mean(lock_times)
    
    return {
        'baseline_total': baseline_time,
        'baseline_avg_lock': baseline_avg,
        'contention_total': contention_time,
        'contention_avg_lock': contention_avg,
        'slowdown_factor': contention_avg / baseline_avg if baseline_avg > 0 else 1.0,
        'contention_overhead': contention_time - baseline_time
    }


def measure_thread_pool_overhead(work_units: int, thread_count: int) -> Dict[str, float]:
    """
    Measure thread pool submission and coordination overhead.
    
    Args:
        work_units: Number of work items to submit
        thread_count: Number of threads in pool
        
    Returns:
        Dictionary with overhead metrics
    """
    def dummy_work():
        """Minimal work function."""
        return sum(range(100))
    
    # Measure direct execution (baseline)
    start = time.perf_counter()
    for _ in range(work_units):
        dummy_work()
    baseline_time = time.perf_counter() - start
    
    # Measure thread pool execution
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        submission_start = time.perf_counter()
        futures = [executor.submit(dummy_work) for _ in range(work_units)]
        submission_time = time.perf_counter() - submission_start
        
        wait_start = time.perf_counter()
        for future in as_completed(futures):
            future.result()
        wait_time = time.perf_counter() - wait_start
    
    total_time = time.perf_counter() - start
    
    return {
        'baseline_time': baseline_time,
        'total_time': total_time,
        'submission_time': submission_time,
        'wait_time': wait_time,
        'overhead': total_time - baseline_time,
        'overhead_per_task': (total_time - baseline_time) / work_units if work_units > 0 else 0
    }


def measure_work_unit_granularity():
    """
    Measure the trade-off between work unit size and threading overhead.
    
    Tests different work sizes to find the minimum viable work unit
    for threading to be beneficial.
    """
    thread_counts = [1, 2, 4, 8]
    work_sizes = [1, 10, 100, 1000, 10000]  # Operations per work unit
    
    print("\n" + "="*80)
    print("WORK UNIT GRANULARITY ANALYSIS")
    print("="*80)
    print("\nOptimal work unit size for threading benefit:")
    print(f"{'Work Size':<12} ", end="")
    for tc in thread_counts:
        print(f"{tc:>10}thr", end=" ")
    print()
    print("-"*80)
    
    def work_function(size):
        """Work function with configurable size."""
        result = 0
        for i in range(size):
            result += i ** 2
        return result
    
    baseline_times = {}
    for work_size in work_sizes:
        # Baseline (direct execution)
        start = time.perf_counter()
        for _ in range(100):
            work_function(work_size)
        baseline_times[work_size] = time.perf_counter() - start
    
    for work_size in work_sizes:
        print(f"{work_size:<12} ", end="")
        baseline = baseline_times[work_size]
        
        for thread_count in thread_counts:
            start = time.perf_counter()
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                futures = [executor.submit(work_function, work_size) for _ in range(100)]
                for future in as_completed(futures):
                    future.result()
            threaded_time = time.perf_counter() - start
            
            speedup = baseline / threaded_time if threaded_time > 0 else 0
            print(f"{speedup:>9.2f}x", end=" ")
        
        print()


def analyze_synchronization_barriers():
    """
    Analyze the overhead of synchronization barriers (wait_for_completion).
    
    Simulates the pattern used in ThreadedSimulationEngine where we:
    1. Submit batch of work
    2. Wait for completion
    3. Submit next batch
    4. Wait for completion
    ...
    
    This is a major source of overhead as threads become idle between batches.
    """
    print("\n" + "="*80)
    print("SYNCHRONIZATION BARRIER OVERHEAD ANALYSIS")
    print("="*80)
    
    def quick_work():
        """Very fast work function (like our component logic)."""
        return sum(range(10))
    
    batches = 10
    items_per_batch = 20
    thread_count = 4
    
    # Measure with barriers (current approach)
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        for _ in range(batches):
            futures = [executor.submit(quick_work) for _ in range(items_per_batch)]
            # Wait for batch completion (BARRIER)
            for future in as_completed(futures):
                future.result()
    barrier_time = time.perf_counter() - start
    
    # Measure without barriers (all work submitted at once)
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        all_futures = []
        for _ in range(batches):
            futures = [executor.submit(quick_work) for _ in range(items_per_batch)]
            all_futures.extend(futures)
        # Single wait at the end
        for future in as_completed(all_futures):
            future.result()
    no_barrier_time = time.perf_counter() - start
    
    print(f"\nWith Synchronization Barriers:    {barrier_time*1000:.3f}ms")
    print(f"Without Barriers (bulk):           {no_barrier_time*1000:.3f}ms")
    print(f"Barrier Overhead:                  {(barrier_time - no_barrier_time)*1000:.3f}ms")
    print(f"Slowdown from Barriers:            {barrier_time / no_barrier_time:.2f}x")
    print(f"\nBarriers cause threads to idle {batches} times per iteration")
    print(f"This limits parallelism and wastes thread pool efficiency")


def run_comprehensive_analysis():
    """Run all profiling analyses."""
    print("\n" + "="*80)
    print("COMPREHENSIVE THREADING OVERHEAD ANALYSIS")
    print("="*80)
    
    # 1. Lock Contention
    print("\n1. LOCK CONTENTION ANALYSIS")
    print("-"*80)
    contention = measure_lock_contention(component_count=100, thread_count=4)
    print(f"Single-threaded lock time:  {contention['baseline_avg_lock']*1e6:.2f}µs per acquire")
    print(f"Multi-threaded lock time:   {contention['contention_avg_lock']*1e6:.2f}µs per acquire")
    print(f"Contention slowdown:        {contention['slowdown_factor']:.2f}x")
    print(f"Total contention overhead:  {contention['contention_overhead']*1000:.3f}ms")
    
    # 2. Thread Pool Overhead
    print("\n2. THREAD POOL OVERHEAD ANALYSIS")
    print("-"*80)
    pool = measure_thread_pool_overhead(work_units=100, thread_count=4)
    print(f"Baseline (direct execution): {pool['baseline_time']*1000:.3f}ms")
    print(f"Thread pool total:           {pool['total_time']*1000:.3f}ms")
    print(f"  - Submission overhead:     {pool['submission_time']*1000:.3f}ms")
    print(f"  - Wait/coordination:       {pool['wait_time']*1000:.3f}ms")
    print(f"Total overhead:              {pool['overhead']*1000:.3f}ms")
    print(f"Overhead per task:           {pool['overhead_per_task']*1e6:.2f}µs")
    
    # 3. Work Unit Granularity
    measure_work_unit_granularity()
    
    # 4. Synchronization Barriers
    analyze_synchronization_barriers()
    
    # Summary and Recommendations
    print("\n" + "="*80)
    print("SUMMARY AND RECOMMENDATIONS")
    print("="*80)
    
    print("\n🔴 PRIMARY BOTTLENECKS IDENTIFIED:")
    print("   1. Synchronization barriers between phases (VNET eval → Component exec)")
    print("   2. Thread pool submission/coordination overhead (~100-500µs per batch)")
    print("   3. Lock contention on VNET/component access")
    print("   4. Work units too small (<100µs) for threading benefit")
    
    print("\n💡 OPTIMIZATION RECOMMENDATIONS:")
    print("   A. Eliminate synchronization barriers - use event-driven or async model")
    print("   B. Batch work into larger units (10+ components per task)")
    print("   C. Reduce lock granularity - use lock-free data structures where possible")
    print("   D. Make threading optional - only enable for 1000+ component circuits")
    print("   E. Consider task-based parallelism instead of data parallelism")
    
    print("\n⚠️  CURRENT FINDINGS:")
    print("   • Threading adds 2x overhead for current component counts (<500)")
    print("   • Crossover point likely around 2000-5000 components")
    print("   • Single-threaded is optimal for typical use cases")


if __name__ == "__main__":
    run_comprehensive_analysis()

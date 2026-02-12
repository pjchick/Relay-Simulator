"""
Performance Profiler for Relay Simulator

Provides detailed performance metrics for simulation engine and GUI rendering.
Helps identify bottlenecks in large simulations.

Author: AI Assistant
Date: 2026-02-12
"""

import time
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import statistics


@dataclass
class PerformanceMetrics:
    """Performance metrics for a specific operation."""
    name: str
    count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    samples: List[float] = field(default_factory=list)
    
    def record(self, duration: float):
        """Record a timing sample."""
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.samples.append(duration)
        
        # Keep only last 100 samples to avoid unbounded memory growth
        if len(self.samples) > 100:
            self.samples.pop(0)
    
    @property
    def avg_time(self) -> float:
        """Average time per operation."""
        return self.total_time / self.count if self.count > 0 else 0.0
    
    @property
    def median_time(self) -> float:
        """Median time per operation."""
        return statistics.median(self.samples) if self.samples else 0.0
    
    @property
    def p95_time(self) -> float:
        """95th percentile time."""
        if not self.samples:
            return 0.0
        sorted_samples = sorted(self.samples)
        idx = int(len(sorted_samples) * 0.95)
        return sorted_samples[min(idx, len(sorted_samples) - 1)]


class PerformanceProfiler:
    """
    Performance profiler for tracking timing of operations.
    
    Thread-safe: Uses locks for concurrent access.
    
    Usage:
        profiler = PerformanceProfiler()
        
        with profiler.measure("my_operation"):
            # ... do work ...
            pass
        
        # Get report
        report = profiler.get_report()
        print(report)
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize profiler.
        
        Args:
            enabled: Whether profiling is enabled (can disable for production)
        """
        self.enabled = enabled
        self._metrics: Dict[str, PerformanceMetrics] = {}
        self._lock = threading.RLock()
        self._start_times: Dict[int, Tuple[str, float]] = {}  # thread_id -> (name, start_time)
    
    def measure(self, operation_name: str):
        """
        Context manager for measuring operation duration.
        
        Args:
            operation_name: Name of operation being measured
            
        Returns:
            Context manager
        
        Example:
            with profiler.measure("render_components"):
                render_all_components()
        """
        return _MeasureContext(self, operation_name)
    
    def start_measure(self, operation_name: str):
        """
        Start measuring an operation (manual timing).
        
        Args:
            operation_name: Name of operation being measured
            
        Must call end_measure() with same name to complete measurement.
        """
        if not self.enabled:
            return
        
        thread_id = threading.get_ident()
        with self._lock:
            self._start_times[thread_id] = (operation_name, time.perf_counter())
    
    def end_measure(self, operation_name: str):
        """
        End measuring an operation (manual timing).
        
        Args:
            operation_name: Name of operation being measured
        """
        if not self.enabled:
            return
        
        end_time = time.perf_counter()
        thread_id = threading.get_ident()
        
        with self._lock:
            if thread_id not in self._start_times:
                return
            
            stored_name, start_time = self._start_times.pop(thread_id)
            
            # Verify names match
            if stored_name != operation_name:
                print(f"Warning: Mismatched operation names: {stored_name} != {operation_name}")
                return
            
            duration = end_time - start_time
            self._record_metric(operation_name, duration)
    
    def _record_metric(self, operation_name: str, duration: float):
        """
        Record a metric (internal).
        
        Args:
            operation_name: Name of operation
            duration: Duration in seconds
        """
        with self._lock:
            if operation_name not in self._metrics:
                self._metrics[operation_name] = PerformanceMetrics(operation_name)
            
            self._metrics[operation_name].record(duration)
    
    def get_metrics(self) -> Dict[str, PerformanceMetrics]:
        """
        Get all performance metrics.
        
        Returns:
            Dictionary of operation name to PerformanceMetrics
        """
        with self._lock:
            return dict(self._metrics)
    
    def get_report(self, sort_by: str = 'total') -> str:
        """
        Get formatted performance report.
        
        Args:
            sort_by: Sort key ('total', 'avg', 'max', 'count')
            
        Returns:
            Formatted report string
        """
        with self._lock:
            if not self._metrics:
                return "No performance data collected."
            
            # Sort metrics
            metrics_list = list(self._metrics.values())
            
            if sort_by == 'total':
                metrics_list.sort(key=lambda m: m.total_time, reverse=True)
            elif sort_by == 'avg':
                metrics_list.sort(key=lambda m: m.avg_time, reverse=True)
            elif sort_by == 'max':
                metrics_list.sort(key=lambda m: m.max_time, reverse=True)
            elif sort_by == 'count':
                metrics_list.sort(key=lambda m: m.count, reverse=True)
            
            # Build report
            lines = []
            lines.append("=" * 100)
            lines.append("PERFORMANCE PROFILE")
            lines.append("=" * 100)
            lines.append(f"{'Operation':<40} {'Count':>8} {'Total':>10} {'Avg':>10} {'Median':>10} {'P95':>10} {'Min':>10} {'Max':>10}")
            lines.append("-" * 100)
            
            for metric in metrics_list:
                lines.append(
                    f"{metric.name:<40} "
                    f"{metric.count:>8} "
                    f"{metric.total_time:>9.3f}s "
                    f"{metric.avg_time * 1000:>9.1f}ms "
                    f"{metric.median_time * 1000:>9.1f}ms "
                    f"{metric.p95_time * 1000:>9.1f}ms "
                    f"{metric.min_time * 1000:>9.1f}ms "
                    f"{metric.max_time * 1000:>9.1f}ms"
                )
            
            lines.append("=" * 100)
            
            return "\n".join(lines)
    
    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()
            self._start_times.clear()
    
    def enable(self):
        """Enable profiling."""
        self.enabled = True
    
    def disable(self):
        """Disable profiling."""
        self.enabled = False


class _MeasureContext:
    """Context manager for measuring operation duration."""
    
    def __init__(self, profiler: PerformanceProfiler, operation_name: str):
        self.profiler = profiler
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        if self.profiler.enabled:
            self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.profiler.enabled and self.start_time is not None:
            duration = time.perf_counter() - self.start_time
            self.profiler._record_metric(self.operation_name, duration)
        return False


# Global profiler instance
_global_profiler: Optional[PerformanceProfiler] = None


def get_profiler() -> PerformanceProfiler:
    """
    Get the global performance profiler instance.
    
    Returns:
        Global PerformanceProfiler instance
    """
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = PerformanceProfiler(enabled=True)
    return _global_profiler


def print_performance_report(sort_by: str = 'total'):
    """
    Print performance report to console.
    
    Args:
        sort_by: Sort key ('total', 'avg', 'max', 'count')
    """
    profiler = get_profiler()
    print(profiler.get_report(sort_by=sort_by))


def reset_profiler():
    """Reset the global profiler."""
    profiler = get_profiler()
    profiler.reset()

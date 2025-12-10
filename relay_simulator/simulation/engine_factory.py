"""
Simulation Engine Factory

Factory for creating the appropriate simulation engine based on configuration.
Implements single-threaded by default with optional multi-threading for large circuits.

Based on performance analysis (THREADING_BOTTLENECK_ANALYSIS.md):
- Single-threaded is 2x faster for circuits <500 components
- Multi-threading only beneficial for circuits >2000 components
- Default: Single-threaded
- Option: Force multi-threaded or auto-detect based on component count

Author: Cascade AI
Date: 2025-12-10
"""

from typing import Dict, Optional, Union
from enum import Enum

from core.vnet import VNET
from core.tab import Tab
from core.bridge import Bridge
from components.base import Component
from simulation.simulation_engine import SimulationEngine
from simulation.threaded_simulation_engine import ThreadedSimulationEngine


class EngineMode(Enum):
    """Simulation engine execution mode."""
    SINGLE_THREADED = "single"
    MULTI_THREADED = "multi"
    AUTO = "auto"


class EngineConfig:
    """
    Configuration for simulation engine selection.
    
    Attributes:
        mode: Execution mode (single, multi, or auto)
        thread_count: Number of worker threads (for multi-threaded mode)
        auto_threshold: Component count threshold for auto mode (default: 2000)
        max_iterations: Maximum iterations before oscillation detection
        timeout_seconds: Maximum time before timeout
    """
    
    def __init__(
        self,
        mode: Union[EngineMode, str] = EngineMode.AUTO,
        thread_count: Optional[int] = None,
        auto_threshold: int = 2000,
        max_iterations: int = 10000,
        timeout_seconds: float = 30.0
    ):
        """
        Initialize engine configuration.
        
        Args:
            mode: Execution mode - 'single', 'multi', or 'auto' (default: auto)
            thread_count: Number of threads for multi-threaded mode (None = CPU count)
            auto_threshold: Component count for auto mode to switch to multi-threaded
            max_iterations: Maximum simulation iterations
            timeout_seconds: Maximum simulation time
        """
        # Convert string to enum if needed
        if isinstance(mode, str):
            mode_map = {
                'single': EngineMode.SINGLE_THREADED,
                'multi': EngineMode.MULTI_THREADED,
                'auto': EngineMode.AUTO
            }
            mode = mode_map.get(mode.lower(), EngineMode.AUTO)
        
        self.mode = mode
        self.thread_count = thread_count
        self.auto_threshold = auto_threshold
        self.max_iterations = max_iterations
        self.timeout_seconds = timeout_seconds
    
    def __repr__(self):
        return (f"EngineConfig(mode={self.mode.value}, "
                f"thread_count={self.thread_count}, "
                f"auto_threshold={self.auto_threshold})")


class SimulationEngineFactory:
    """
    Factory for creating simulation engines.
    
    Selects the appropriate engine type based on configuration and circuit size.
    
    Performance analysis shows:
    - Single-threaded optimal for <2000 components (2x faster)
    - Multi-threaded beneficial for >2000 components
    - Threading overhead dominates for small circuits
    
    Default: AUTO mode
    - <2000 components: Single-threaded
    - ≥2000 components: Multi-threaded (4 threads)
    """
    
    # Default configuration
    DEFAULT_CONFIG = EngineConfig(
        mode=EngineMode.AUTO,
        auto_threshold=2000,
        max_iterations=10000,
        timeout_seconds=30.0
    )
    
    @staticmethod
    def create_engine(
        vnets: Dict[str, VNET],
        tabs: Dict[str, Tab],
        bridges: Dict[str, Bridge],
        components: Dict[str, Component],
        config: Optional[EngineConfig] = None
    ) -> Union[SimulationEngine, ThreadedSimulationEngine]:
        """
        Create appropriate simulation engine based on configuration.
        
        Args:
            vnets: Dictionary of all VNETs by ID
            tabs: Dictionary of all tabs by ID
            bridges: Dictionary of all bridges by ID
            components: Dictionary of all components by ID
            config: Engine configuration (None = use defaults)
            
        Returns:
            SimulationEngine or ThreadedSimulationEngine instance
        """
        if config is None:
            config = SimulationEngineFactory.DEFAULT_CONFIG
        
        # Determine which engine to use
        component_count = len(components)
        use_threaded = False
        
        if config.mode == EngineMode.SINGLE_THREADED:
            use_threaded = False
        elif config.mode == EngineMode.MULTI_THREADED:
            use_threaded = True
        elif config.mode == EngineMode.AUTO:
            # Auto-detect based on component count
            use_threaded = component_count >= config.auto_threshold
        
        # Create the appropriate engine
        if use_threaded:
            return ThreadedSimulationEngine(
                vnets=vnets,
                tabs=tabs,
                bridges=bridges,
                components=components,
                max_iterations=config.max_iterations,
                timeout_seconds=config.timeout_seconds,
                thread_count=config.thread_count
            )
        else:
            return SimulationEngine(
                vnets=vnets,
                tabs=tabs,
                bridges=bridges,
                components=components,
                max_iterations=config.max_iterations,
                timeout_seconds=config.timeout_seconds
            )
    
    @staticmethod
    def create_single_threaded(
        vnets: Dict[str, VNET],
        tabs: Dict[str, Tab],
        bridges: Dict[str, Bridge],
        components: Dict[str, Component],
        max_iterations: int = 10000,
        timeout_seconds: float = 30.0
    ) -> SimulationEngine:
        """
        Create a single-threaded simulation engine.
        
        Convenience method for explicitly creating single-threaded engine.
        
        Args:
            vnets: Dictionary of all VNETs by ID
            tabs: Dictionary of all tabs by ID
            bridges: Dictionary of all bridges by ID
            components: Dictionary of all components by ID
            max_iterations: Maximum iterations before oscillation detection
            timeout_seconds: Maximum time before timeout
            
        Returns:
            SimulationEngine instance
        """
        config = EngineConfig(
            mode=EngineMode.SINGLE_THREADED,
            max_iterations=max_iterations,
            timeout_seconds=timeout_seconds
        )
        
        return SimulationEngineFactory.create_engine(
            vnets, tabs, bridges, components, config
        )
    
    @staticmethod
    def create_multi_threaded(
        vnets: Dict[str, VNET],
        tabs: Dict[str, Tab],
        bridges: Dict[str, Bridge],
        components: Dict[str, Component],
        thread_count: Optional[int] = None,
        max_iterations: int = 10000,
        timeout_seconds: float = 30.0
    ) -> ThreadedSimulationEngine:
        """
        Create a multi-threaded simulation engine.
        
        Convenience method for explicitly creating multi-threaded engine.
        
        Args:
            vnets: Dictionary of all VNETs by ID
            tabs: Dictionary of all tabs by ID
            bridges: Dictionary of all bridges by ID
            components: Dictionary of all components by ID
            thread_count: Number of worker threads (None = CPU count)
            max_iterations: Maximum iterations before oscillation detection
            timeout_seconds: Maximum time before timeout
            
        Returns:
            ThreadedSimulationEngine instance
        """
        config = EngineConfig(
            mode=EngineMode.MULTI_THREADED,
            thread_count=thread_count,
            max_iterations=max_iterations,
            timeout_seconds=timeout_seconds
        )
        
        return SimulationEngineFactory.create_engine(
            vnets, tabs, bridges, components, config
        )
    
    @staticmethod
    def get_recommended_mode(component_count: int) -> EngineMode:
        """
        Get recommended engine mode for given component count.
        
        Based on performance analysis:
        - <2000 components: Single-threaded (2x faster)
        - ≥2000 components: Multi-threaded
        
        Args:
            component_count: Number of components in circuit
            
        Returns:
            Recommended EngineMode
        """
        threshold = SimulationEngineFactory.DEFAULT_CONFIG.auto_threshold
        
        if component_count < threshold:
            return EngineMode.SINGLE_THREADED
        else:
            return EngineMode.MULTI_THREADED
    
    @staticmethod
    def print_recommendation(component_count: int):
        """
        Print performance recommendation for given component count.
        
        Args:
            component_count: Number of components in circuit
        """
        mode = SimulationEngineFactory.get_recommended_mode(component_count)
        threshold = SimulationEngineFactory.DEFAULT_CONFIG.auto_threshold
        
        print(f"\n{'='*60}")
        print(f"ENGINE PERFORMANCE RECOMMENDATION")
        print(f"{'='*60}")
        print(f"Component count: {component_count}")
        print(f"Recommended mode: {mode.value.upper()}")
        
        if component_count < threshold:
            print(f"\nRationale:")
            print(f"  • Circuit has <{threshold} components")
            print(f"  • Single-threaded is ~2x faster for this size")
            print(f"  • Threading overhead exceeds parallelism benefit")
        else:
            print(f"\nRationale:")
            print(f"  • Circuit has ≥{threshold} components")
            print(f"  • Multi-threading provides performance benefit")
            print(f"  • Parallelism outweighs threading overhead")
        
        print(f"\nTo override, use:")
        if mode == EngineMode.SINGLE_THREADED:
            print(f"  config = EngineConfig(mode='multi')  # Force multi-threaded")
        else:
            print(f"  config = EngineConfig(mode='single')  # Force single-threaded")
        
        print(f"{'='*60}\n")


# Convenience function for quick engine creation
def create_engine(
    vnets: Dict[str, VNET],
    tabs: Dict[str, Tab],
    bridges: Dict[str, Bridge],
    components: Dict[str, Component],
    mode: str = "auto",
    **kwargs
) -> Union[SimulationEngine, ThreadedSimulationEngine]:
    """
    Convenience function to create simulation engine.
    
    Args:
        vnets: Dictionary of all VNETs by ID
        tabs: Dictionary of all tabs by ID
        bridges: Dictionary of all bridges by ID
        components: Dictionary of all components by ID
        mode: 'single', 'multi', or 'auto' (default: auto)
        **kwargs: Additional EngineConfig parameters
        
    Returns:
        SimulationEngine or ThreadedSimulationEngine instance
        
    Example:
        # Auto mode (recommended)
        engine = create_engine(vnets, tabs, bridges, components)
        
        # Force single-threaded
        engine = create_engine(vnets, tabs, bridges, components, mode='single')
        
        # Force multi-threaded with 8 threads
        engine = create_engine(vnets, tabs, bridges, components, 
                             mode='multi', thread_count=8)
    """
    config = EngineConfig(mode=mode, **kwargs)
    return SimulationEngineFactory.create_engine(vnets, tabs, bridges, components, config)

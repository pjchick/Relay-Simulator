"""
Simulator Commands for Terminal Interface

This module implements all terminal commands for controlling the relay logic simulator.
It integrates the command parser with the simulation engine to provide interactive control.

Commands are organized into categories:
- File commands: load
- Simulation commands: start, stop, status, stats
- Component commands: list, show, toggle
- VNET commands: list vnets, show vnet, list dirty
- Debug commands: debug, trace
- Utility commands: help, quit, clear
"""

import os
from typing import Any, Dict, List, Optional
from core.document import Document
from simulation.simulation_engine import SimulationEngine
from simulation.engine_factory import create_engine
from networking.command_parser import (
    Command,
    CommandRegistry,
    ArgumentSpec,
    OptionSpec,
    ArgumentType
)


class SimulatorContext:
    """
    Context object passed to all command handlers.
    
    Contains references to the current state of the simulator:
    - Document being edited/simulated
    - Simulation engine instance
    - Debug flags
    - Client information
    """
    
    def __init__(self):
        """Initialize empty context."""
        self.document: Optional[Document] = None
        self.engine: Optional[SimulationEngine] = None
        self.debug_enabled: bool = False
        self.trace_vnets: set = set()
        self.trace_components: set = set()
        self.client_info: Dict[str, Any] = {}
    
    def has_document(self) -> bool:
        """Check if a document is loaded."""
        return self.document is not None
    
    def is_simulating(self) -> bool:
        """Check if simulation is running."""
        return self.engine is not None and self.engine.is_running()


class SimulatorCommands:
    """
    Collection of command handler functions for the simulator.
    
    Each method is a command handler that takes (args, options, context)
    and returns a string response.
    """
    
    # ========== FILE COMMANDS ==========
    
    @staticmethod
    def cmd_load(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Load a .rsim file into the simulator.
        
        Args:
            args: [filename]
            options: {}
            context: SimulatorContext
            
        Returns:
            Success/failure message
        """
        ctx: SimulatorContext = context.get('simulator')
        filename = args[0]
        
        # Stop any running simulation
        if ctx.is_simulating():
            ctx.engine.stop()
            ctx.engine = None
        
        # Check if file exists
        if not os.path.exists(filename):
            return f"Error: File not found: {filename}"
        
        # Load document
        try:
            import json
            with open(filename, 'r') as f:
                data = json.load(f)
            ctx.document = Document.from_dict(data)
            return f"Loaded {filename}\n" \
                   f"Pages: {len(ctx.document.pages)}\n" \
                   f"Components: {len(ctx.document.get_all_components())}"
        except Exception as e:
            return f"Error loading file: {e}"
    
    # ========== SIMULATION COMMANDS ==========
    
    @staticmethod
    def cmd_start(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Start the simulation.
        
        Args:
            args: []
            options: {mode: 'single'|'multi'|'auto'}
            context: SimulatorContext
            
        Returns:
            Simulation results
        """
        ctx: SimulatorContext = context.get('simulator')
        
        if not ctx.has_document():
            return "Error: No document loaded. Use 'load <filename>' first."
        
        if ctx.is_simulating():
            return "Error: Simulation already running. Use 'stop' first."
        
        # Get mode option (default: auto)
        mode = options.get('mode', 'auto')
        
        # Create and run engine directly (simpler approach)
        try:
            from simulation.simulation_engine import SimulationEngine
            
            ctx.engine = SimulationEngine(ctx.document)
            ctx.engine.initialize()
            
            # Run simulation
            stats = ctx.engine.run()
            
            # Format results
            result = f"Simulation complete\n"
            result += f"Mode: single-threaded\n"
            result += f"Iterations: {stats.iterations}\n"
            result += f"Time: {stats.elapsed_time:.3f}s\n"
            result += f"Components updated: {stats.components_updated}\n"
            result += f"VNETs processed: {stats.vnets_processed}\n"
            
            if stats.stable:
                result += "Status: STABLE"
            else:
                result += f"Status: OSCILLATING (max iterations reached)"
            
            return result
            
        except Exception as e:
            ctx.engine = None
            return f"Error starting simulation: {e}"
    
    @staticmethod
    def cmd_stop(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Stop the simulation.
        
        Args:
            args: []
            options: {}
            context: SimulatorContext
            
        Returns:
            Status message
        """
        ctx: SimulatorContext = context.get('simulator')
        
        if not ctx.is_simulating():
            return "Simulation not running"
        
        ctx.engine.stop()
        ctx.engine = None
        
        return "Simulation stopped"
    
    @staticmethod
    def cmd_status(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Get current simulator status.
        
        Args:
            args: []
            options: {}
            context: SimulatorContext
            
        Returns:
            Status information
        """
        ctx: SimulatorContext = context.get('simulator')
        
        result = "=== Simulator Status ===\n"
        
        # Document status
        if ctx.has_document():
            result += f"Document: Loaded\n"
            result += f"  Pages: {len(ctx.document.pages)}\n"
            result += f"  Components: {len(ctx.document.get_all_components())}\n"
        else:
            result += "Document: None\n"
        
        # Simulation status
        if ctx.is_simulating():
            result += "Simulation: RUNNING\n"
            stats = ctx.engine.get_stats()
            result += f"  Iterations: {stats.iterations}\n"
            result += f"  Time: {stats.elapsed_time:.3f}s\n"
        else:
            result += "Simulation: STOPPED\n"
        
        # Debug status
        result += f"Debug: {'ON' if ctx.debug_enabled else 'OFF'}\n"
        
        if ctx.trace_vnets:
            result += f"Traced VNETs: {', '.join(ctx.trace_vnets)}\n"
        
        if ctx.trace_components:
            result += f"Traced Components: {', '.join(ctx.trace_components)}\n"
        
        return result
    
    @staticmethod
    def cmd_stats(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Show detailed simulation statistics.
        
        Args:
            args: []
            options: {}
            context: SimulatorContext
            
        Returns:
            Detailed statistics
        """
        ctx: SimulatorContext = context.get('simulator')
        
        if not ctx.is_simulating():
            return "Error: No active simulation. Use 'start' first."
        
        stats = ctx.engine.get_stats()
        
        result = "=== Simulation Statistics ===\n"
        result += f"Iterations: {stats.iterations}\n"
        result += f"Elapsed time: {stats.elapsed_time:.3f}s\n"
        result += f"Iterations/sec: {stats.iterations / stats.elapsed_time if stats.elapsed_time > 0 else 0:.1f}\n"
        result += f"Components updated: {stats.components_updated}\n"
        result += f"VNETs processed: {stats.vnets_processed}\n"
        result += f"Stable: {stats.stable}\n"
        
        return result
    
    # ========== COMPONENT COMMANDS ==========
    
    @staticmethod
    def cmd_list_components(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        List all components in the document.
        
        Args:
            args: []
            options: {verbose: bool}
            context: SimulatorContext
            
        Returns:
            Component list
        """
        ctx: SimulatorContext = context.get('simulator')
        
        if not ctx.has_document():
            return "Error: No document loaded"
        
        components = ctx.document.get_all_components()
        verbose = options.get('verbose', False)
        
        if not components:
            return "No components in document"
        
        result = f"=== Components ({len(components)}) ===\n"
        
        for comp in components:
            if verbose:
                result += f"{comp.component_id:20s} {comp.component_type:15s} "
                result += f"Pins: {len(comp.pins):2d} "
                if comp.link_name:
                    result += f"Link: {comp.link_name}"
                result += "\n"
            else:
                result += f"{comp.component_id} ({comp.component_type})\n"
        
        return result
    
    @staticmethod
    def cmd_show_component(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Show detailed information about a component.
        
        Args:
            args: [component_id]
            options: {}
            context: SimulatorContext
            
        Returns:
            Component details
        """
        ctx: SimulatorContext = context.get('simulator')
        
        if not ctx.has_document():
            return "Error: No document loaded"
        
        component_id = args[0]
        
        # Find component
        component = None
        for comp in ctx.document.get_all_components():
            if comp.component_id == component_id:
                component = comp
                break
        
        if not component:
            return f"Error: Component not found: {component_id}"
        
        # Build detailed info
        result = f"=== Component: {component_id} ===\n"
        result += f"Type: {component.component_type}\n"
        result += f"Position: {component.position}\n"
        result += f"Page: {component.page_id}\n"
        
        if component.link_name:
            result += f"Link name: {component.link_name}\n"
        
        # Pins (pins is a dict: pin_id -> Pin)
        result += f"\nPins ({len(component.pins)}):\n"
        for pin_id, pin in component.pins.items():
            result += f"  {pin_id}: {pin.state.name} ({len(pin.tabs)} tabs)\n"
        
        # Properties
        if component.properties:
            result += f"\nProperties:\n"
            for key, value in component.properties.items():
                result += f"  {key}: {value}\n"
        
        return result
    
    @staticmethod
    def cmd_toggle(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Toggle a switch component.
        
        Args:
            args: [component_id]
            options: {}
            context: SimulatorContext
            
        Returns:
            Result message
        """
        ctx: SimulatorContext = context.get('simulator')
        
        if not ctx.has_document():
            return "Error: No document loaded"
        
        component_id = args[0]
        
        # Find component
        component = None
        for comp in ctx.document.get_all_components():
            if comp.component_id == component_id:
                component = comp
                break
        
        if not component:
            return f"Error: Component not found: {component_id}"
        
        # Check if it's a switch
        if component.component_type != "Switch":
            return f"Error: Component is not a switch: {component.component_type}"
        
        # Toggle it
        try:
            component.interact("toggle")
            
            # Get new state
            state = component.get_state()
            
            return f"Toggled {component_id} to {'ON' if state else 'OFF'}"
            
        except Exception as e:
            return f"Error toggling switch: {e}"
    
    # ========== VNET COMMANDS ==========
    
    @staticmethod
    def cmd_list_vnets(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        List all VNETs in the simulation.
        
        Args:
            args: []
            options: {verbose: bool}
            context: SimulatorContext
            
        Returns:
            VNET list
        """
        ctx: SimulatorContext = context.get('simulator')
        
        if not ctx.is_simulating():
            return "Error: No active simulation. Use 'start' first."
        
        vnets = ctx.engine.vnets
        verbose = options.get('verbose', False)
        
        if not vnets:
            return "No VNETs in simulation"
        
        result = f"=== VNETs ({len(vnets)}) ===\n"
        
        for vnet in vnets:
            if verbose:
                result += f"{vnet.vnet_id:20s} State: {vnet.state.name:5s} "
                result += f"Tabs: {len(vnet.tab_ids):3d} "
                result += f"Dirty: {'YES' if vnet.is_dirty else 'NO':3s} "
                if vnet.link_names:
                    result += f"Links: {', '.join(vnet.link_names)}"
                result += "\n"
            else:
                result += f"{vnet.vnet_id} ({vnet.state.name})\n"
        
        return result
    
    @staticmethod
    def cmd_show_vnet(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Show detailed information about a VNET.
        
        Args:
            args: [vnet_id]
            options: {}
            context: SimulatorContext
            
        Returns:
            VNET details
        """
        ctx: SimulatorContext = context.get('simulator')
        
        if not ctx.is_simulating():
            return "Error: No active simulation. Use 'start' first."
        
        vnet_id = args[0]
        
        # Find VNET
        vnet = None
        for v in ctx.engine.vnets:
            if v.vnet_id == vnet_id:
                vnet = v
                break
        
        if not vnet:
            return f"Error: VNET not found: {vnet_id}"
        
        # Build detailed info
        result = f"=== VNET: {vnet_id} ===\n"
        result += f"State: {vnet.state.name}\n"
        result += f"Dirty: {vnet.is_dirty}\n"
        result += f"Tabs: {len(vnet.tab_ids)}\n"
        
        if vnet.link_names:
            result += f"Link names: {', '.join(vnet.link_names)}\n"
        
        if vnet.bridge_ids:
            result += f"Bridges: {len(vnet.bridge_ids)}\n"
        
        # List tabs (limited)
        if len(vnet.tab_ids) <= 20:
            result += f"\nTabs:\n"
            for tab_id in vnet.tab_ids:
                result += f"  {tab_id}\n"
        else:
            result += f"\nTabs: {len(vnet.tab_ids)} (too many to list)\n"
        
        return result
    
    @staticmethod
    def cmd_list_dirty(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        List all dirty VNETs.
        
        Args:
            args: []
            options: {}
            context: SimulatorContext
            
        Returns:
            Dirty VNET list
        """
        ctx: SimulatorContext = context.get('simulator')
        
        if not ctx.is_simulating():
            return "Error: No active simulation. Use 'start' first."
        
        dirty_vnets = [v for v in ctx.engine.vnets if v.is_dirty]
        
        if not dirty_vnets:
            return "No dirty VNETs (simulation stable)"
        
        result = f"=== Dirty VNETs ({len(dirty_vnets)}) ===\n"
        
        for vnet in dirty_vnets:
            result += f"{vnet.vnet_id} ({vnet.state.name})\n"
        
        return result
    
    # ========== DEBUG COMMANDS ==========
    
    @staticmethod
    def cmd_debug(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Toggle debug mode.
        
        Args:
            args: [on|off]
            options: {}
            context: SimulatorContext
            
        Returns:
            Status message
        """
        ctx: SimulatorContext = context.get('simulator')
        
        setting = args[0].lower()
        
        if setting == 'on':
            ctx.debug_enabled = True
            return "Debug mode enabled"
        elif setting == 'off':
            ctx.debug_enabled = False
            return "Debug mode disabled"
        else:
            return f"Error: Invalid setting: {setting}. Use 'on' or 'off'"
    
    @staticmethod
    def cmd_trace_vnet(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Enable tracing for a VNET.
        
        Args:
            args: [vnet_id]
            options: {}
            context: SimulatorContext
            
        Returns:
            Status message
        """
        ctx: SimulatorContext = context.get('simulator')
        
        vnet_id = args[0]
        
        ctx.trace_vnets.add(vnet_id)
        
        return f"Tracing enabled for VNET: {vnet_id}"
    
    @staticmethod
    def cmd_trace_component(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Enable tracing for a component.
        
        Args:
            args: [component_id]
            options: {}
            context: SimulatorContext
            
        Returns:
            Status message
        """
        ctx: SimulatorContext = context.get('simulator')
        
        component_id = args[0]
        
        ctx.trace_components.add(component_id)
        
        return f"Tracing enabled for component: {component_id}"
    
    # ========== UTILITY COMMANDS ==========
    
    @staticmethod
    def cmd_help(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Show help information.
        
        Args:
            args: [command_name] (optional)
            options: {}
            context: SimulatorContext (contains registry)
            
        Returns:
            Help text
        """
        registry: CommandRegistry = context.get('registry')
        
        if args:
            # Help for specific command
            command_name = args[0]
            return registry.get_help(command_name, verbose=True)
        else:
            # General help
            return registry.get_help(verbose=False)
    
    @staticmethod
    def cmd_clear(args: List[Any], options: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Clear the terminal screen.
        
        Args:
            args: []
            options: {}
            context: SimulatorContext
            
        Returns:
            ANSI clear screen sequence
        """
        # ANSI escape sequence to clear screen
        return "\033[2J\033[H"


def register_all_commands(registry: CommandRegistry) -> None:
    """
    Register all simulator commands with the registry.
    
    Args:
        registry: CommandRegistry to register commands with
    """
    
    # File commands
    registry.register(Command(
        name="load",
        handler=SimulatorCommands.cmd_load,
        help_text="Load a .rsim circuit file",
        long_help="Loads a circuit file into the simulator. Stops any running simulation first.",
        arg_specs=[
            ArgumentSpec("filename", ArgumentType.FILENAME, required=True,
                        help_text="Path to .rsim file")
        ]
    ))
    
    # Simulation commands
    registry.register(Command(
        name="start",
        handler=SimulatorCommands.cmd_start,
        help_text="Start the simulation",
        long_help="Initializes and runs the simulation engine. Returns statistics when complete.",
        option_specs=[
            OptionSpec(long="mode", has_value=True, default="auto",
                      arg_type=ArgumentType.STRING,
                      help_text="Engine mode: 'single', 'multi', or 'auto'")
        ]
    ))
    
    registry.register(Command(
        name="stop",
        handler=SimulatorCommands.cmd_stop,
        help_text="Stop the simulation",
        long_help="Stops the currently running simulation."
    ))
    
    registry.register(Command(
        name="status",
        handler=SimulatorCommands.cmd_status,
        help_text="Show simulator status",
        long_help="Displays current document, simulation state, and debug settings."
    ))
    
    registry.register(Command(
        name="stats",
        handler=SimulatorCommands.cmd_stats,
        help_text="Show simulation statistics",
        long_help="Displays detailed statistics from the current simulation.",
        aliases=["statistics"]
    ))
    
    # Component commands
    registry.register(Command(
        name="list",
        handler=SimulatorCommands.cmd_list_components,
        help_text="List all components",
        long_help="Lists all components in the loaded document.",
        option_specs=[
            OptionSpec(short="v", long="verbose",
                      help_text="Show detailed information")
        ],
        aliases=["ls"]
    ))
    
    registry.register(Command(
        name="show",
        handler=SimulatorCommands.cmd_show_component,
        help_text="Show component details",
        long_help="Displays detailed information about a specific component.",
        arg_specs=[
            ArgumentSpec("component_id", ArgumentType.COMPONENT_ID, required=True,
                        help_text="Component ID to show")
        ]
    ))
    
    registry.register(Command(
        name="toggle",
        handler=SimulatorCommands.cmd_toggle,
        help_text="Toggle a switch component",
        long_help="Toggles the state of a switch component (ON/OFF).",
        arg_specs=[
            ArgumentSpec("component_id", ArgumentType.COMPONENT_ID, required=True,
                        help_text="Switch component ID")
        ]
    ))
    
    # VNET commands
    registry.register(Command(
        name="vnets",
        handler=SimulatorCommands.cmd_list_vnets,
        help_text="List all VNETs",
        long_help="Lists all VNETs in the current simulation.",
        option_specs=[
            OptionSpec(short="v", long="verbose",
                      help_text="Show detailed information")
        ]
    ))
    
    registry.register(Command(
        name="vnet",
        handler=SimulatorCommands.cmd_show_vnet,
        help_text="Show VNET details",
        long_help="Displays detailed information about a specific VNET.",
        arg_specs=[
            ArgumentSpec("vnet_id", ArgumentType.VNET_ID, required=True,
                        help_text="VNET ID to show")
        ]
    ))
    
    registry.register(Command(
        name="dirty",
        handler=SimulatorCommands.cmd_list_dirty,
        help_text="List dirty VNETs",
        long_help="Lists all VNETs that are currently marked as dirty (unstable)."
    ))
    
    # Debug commands
    registry.register(Command(
        name="debug",
        handler=SimulatorCommands.cmd_debug,
        help_text="Toggle debug mode",
        long_help="Enables or disables debug output.",
        arg_specs=[
            ArgumentSpec("setting", ArgumentType.STRING, required=True,
                        choices=["on", "off"],
                        help_text="'on' or 'off'")
        ]
    ))
    
    registry.register(Command(
        name="trace",
        handler=SimulatorCommands.cmd_trace_vnet,
        help_text="Trace a VNET",
        long_help="Enables detailed tracing for a specific VNET.",
        arg_specs=[
            ArgumentSpec("vnet_id", ArgumentType.VNET_ID, required=True,
                        help_text="VNET ID to trace")
        ]
    ))
    
    # Utility commands
    registry.register(Command(
        name="help",
        handler=SimulatorCommands.cmd_help,
        help_text="Show help information",
        long_help="Shows help for all commands or a specific command.",
        arg_specs=[
            ArgumentSpec("command", ArgumentType.STRING, required=False,
                        help_text="Command to get help for")
        ],
        aliases=["?"]
    ))
    
    registry.register(Command(
        name="clear",
        handler=SimulatorCommands.cmd_clear,
        help_text="Clear the screen",
        long_help="Clears the terminal screen.",
        aliases=["cls"]
    ))


def create_simulator_context() -> Dict[str, Any]:
    """
    Create a new simulator context for command execution.
    
    Returns:
        Context dictionary with SimulatorContext and CommandRegistry
    """
    ctx = SimulatorContext()
    registry = CommandRegistry()
    
    # Register all commands
    register_all_commands(registry)
    
    # Create context dict
    context = {
        'simulator': ctx,
        'registry': registry
    }
    
    return context

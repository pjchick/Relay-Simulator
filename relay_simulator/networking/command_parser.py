"""
Command Parser for Relay Logic Simulator Terminal Interface

This module provides command parsing, validation, and dispatch functionality
for the terminal server. It parses command lines into structured commands,
validates arguments, and dispatches to registered command handlers.

Architecture:
- CommandParser: Parses command lines into structured data
- Command: Defines a command with name, handler, help text, and argument specs
- CommandRegistry: Registers and dispatches commands
- ParsedCommand: Result of parsing (command name, arguments, options)

Example usage:
    # Create registry
    registry = CommandRegistry()
    
    # Define a command handler
    def handle_load(args, options, context):
        filename = args[0]
        return f"Loading {filename}..."
    
    # Register command
    registry.register(
        Command(
            name="load",
            handler=handle_load,
            help_text="Load a .rsim file",
            arg_spec=[ArgumentSpec("filename", str, required=True)]
        )
    )
    
    # Parse and execute
    result = registry.parse_and_execute("load circuit.rsim", context={})
    print(result)
"""

import shlex
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ArgumentType(Enum):
    """Supported argument types for command validation."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    COMPONENT_ID = "component_id"
    VNET_ID = "vnet_id"
    FILENAME = "filename"


@dataclass
class ArgumentSpec:
    """
    Specification for a command argument.
    
    Attributes:
        name: Argument name (for help text and error messages)
        arg_type: Type of argument (ArgumentType enum)
        required: Whether argument is required
        default: Default value if not provided
        choices: Valid values (if limited set)
        help_text: Help text for this argument
    """
    name: str
    arg_type: ArgumentType
    required: bool = True
    default: Any = None
    choices: Optional[List[Any]] = None
    help_text: str = ""


@dataclass
class OptionSpec:
    """
    Specification for a command option/flag.
    
    Attributes:
        short: Short form (e.g., 'v' for -v)
        long: Long form (e.g., 'verbose' for --verbose)
        arg_type: Type if option takes a value
        has_value: Whether option takes a value
        default: Default value
        help_text: Help text for this option
    """
    short: Optional[str] = None
    long: Optional[str] = None
    arg_type: ArgumentType = ArgumentType.BOOLEAN
    has_value: bool = False
    default: Any = False
    help_text: str = ""
    
    def matches(self, token: str) -> bool:
        """Check if token matches this option."""
        if self.short and token == f"-{self.short}":
            return True
        if self.long and token == f"--{self.long}":
            return True
        return False


@dataclass
class ParsedCommand:
    """
    Result of parsing a command line.
    
    Attributes:
        command_name: Name of the command
        args: List of positional arguments
        options: Dictionary of options (flag -> value)
        raw_line: Original command line
    """
    command_name: str
    args: List[Any] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)
    raw_line: str = ""


@dataclass
class Command:
    """
    Command definition with handler and metadata.
    
    Attributes:
        name: Command name
        handler: Callable that executes the command
        help_text: Short help description
        long_help: Detailed help text
        arg_specs: List of argument specifications
        option_specs: List of option specifications
        aliases: Alternative names for this command
    """
    name: str
    handler: Callable[[List[Any], Dict[str, Any], Dict[str, Any]], str]
    help_text: str = ""
    long_help: str = ""
    arg_specs: List[ArgumentSpec] = field(default_factory=list)
    option_specs: List[OptionSpec] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    
    def get_usage(self) -> str:
        """Generate usage string for this command."""
        parts = [self.name]
        
        # Add options
        for opt in self.option_specs:
            if opt.short and opt.long:
                opt_str = f"[-{opt.short}|--{opt.long}]"
            elif opt.short:
                opt_str = f"[-{opt.short}]"
            else:
                opt_str = f"[--{opt.long}]"
            
            if opt.has_value:
                opt_str = f"{opt_str} <value>"
            parts.append(opt_str)
        
        # Add arguments
        for arg in self.arg_specs:
            if arg.required:
                parts.append(f"<{arg.name}>")
            else:
                parts.append(f"[{arg.name}]")
        
        return " ".join(parts)
    
    def get_help(self, verbose: bool = False) -> str:
        """Generate help text for this command."""
        lines = [f"{self.name}: {self.help_text}"]
        
        if verbose:
            lines.append(f"Usage: {self.get_usage()}")
            
            if self.long_help:
                lines.append("")
                lines.append(self.long_help)
            
            if self.arg_specs:
                lines.append("")
                lines.append("Arguments:")
                for arg in self.arg_specs:
                    req = "required" if arg.required else "optional"
                    line = f"  {arg.name} ({arg.arg_type.value}, {req})"
                    if arg.help_text:
                        line += f" - {arg.help_text}"
                    if arg.choices:
                        line += f" [choices: {', '.join(str(c) for c in arg.choices)}]"
                    lines.append(line)
            
            if self.option_specs:
                lines.append("")
                lines.append("Options:")
                for opt in self.option_specs:
                    flags = []
                    if opt.short:
                        flags.append(f"-{opt.short}")
                    if opt.long:
                        flags.append(f"--{opt.long}")
                    line = f"  {', '.join(flags)}"
                    if opt.help_text:
                        line += f" - {opt.help_text}"
                    lines.append(line)
            
            if self.aliases:
                lines.append("")
                lines.append(f"Aliases: {', '.join(self.aliases)}")
        
        return "\n".join(lines)


class CommandParser:
    """
    Parses command lines into structured ParsedCommand objects.
    
    Handles:
    - Quoted arguments (single and double quotes)
    - Escaped characters
    - Options/flags (-v, --verbose)
    - Positional arguments
    """
    
    @staticmethod
    def parse(command_line: str) -> ParsedCommand:
        """
        Parse a command line into a ParsedCommand.
        
        Args:
            command_line: Raw command line string
            
        Returns:
            ParsedCommand object with parsed data
            
        Raises:
            ValueError: If command line is empty or invalid
        """
        # Strip whitespace
        command_line = command_line.strip()
        
        if not command_line:
            raise ValueError("Empty command line")
        
        # Use shlex to handle quotes and escapes
        try:
            tokens = shlex.split(command_line)
        except ValueError as e:
            raise ValueError(f"Invalid command line: {e}")
        
        if not tokens:
            raise ValueError("Empty command line")
        
        # First token is command name
        command_name = tokens[0].lower()
        
        # Parse remaining tokens
        args = []
        options = {}
        i = 1
        
        while i < len(tokens):
            token = tokens[i]
            
            # Check if it's an option
            if token.startswith("-"):
                # Handle long option with =
                if "=" in token and token.startswith("--"):
                    key, value = token.split("=", 1)
                    option_name = key[2:]  # Remove --
                    options[option_name] = value
                    i += 1
                # Handle short option
                elif token.startswith("-") and not token.startswith("--"):
                    option_name = token[1:]
                    # Peek at next token - if it doesn't start with -, it's the option value
                    # BUT only consume it if it looks like a value, not a positional arg
                    # For simplicity: boolean flags don't consume next token
                    options[option_name] = True
                    i += 1
                # Handle long option
                else:
                    option_name = token[2:]  # Remove --
                    # Boolean flag - don't consume next token
                    options[option_name] = True
                    i += 1
            else:
                # Regular argument
                args.append(token)
                i += 1
        
        return ParsedCommand(
            command_name=command_name,
            args=args,
            options=options,
            raw_line=command_line
        )
    
    @staticmethod
    def validate_and_convert(
        parsed: ParsedCommand,
        arg_specs: List[ArgumentSpec],
        option_specs: List[OptionSpec]
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Validate and convert arguments according to specifications.
        
        Args:
            parsed: Parsed command
            arg_specs: Argument specifications
            option_specs: Option specifications
            
        Returns:
            Tuple of (converted_args, converted_options)
            
        Raises:
            ValueError: If validation fails
        """
        # Validate argument count
        required_args = sum(1 for spec in arg_specs if spec.required)
        if len(parsed.args) < required_args:
            # Get name of first missing required argument
            missing_arg = None
            for i, spec in enumerate(arg_specs):
                if spec.required and i >= len(parsed.args):
                    missing_arg = spec.name
                    break
            
            if missing_arg:
                raise ValueError(f"Missing required argument: {missing_arg}")
            else:
                raise ValueError(
                    f"Not enough arguments: expected at least {required_args}, "
                    f"got {len(parsed.args)}"
                )
        
        if len(parsed.args) > len(arg_specs):
            raise ValueError(
                f"Too many arguments: expected at most {len(arg_specs)}, "
                f"got {len(parsed.args)}"
            )
        
        # Convert and validate arguments
        converted_args = []
        for i, spec in enumerate(arg_specs):
            if i < len(parsed.args):
                value = parsed.args[i]
                converted_value = CommandParser._convert_value(value, spec.arg_type, spec.name)
                
                # Check choices
                if spec.choices and converted_value not in spec.choices:
                    raise ValueError(
                        f"Invalid value for {spec.name}: {converted_value}. "
                        f"Valid choices: {', '.join(str(c) for c in spec.choices)}"
                    )
                
                converted_args.append(converted_value)
            elif spec.required:
                raise ValueError(f"Missing required argument: {spec.name}")
            else:
                converted_args.append(spec.default)
        
        # Convert and validate options
        converted_options = {}
        
        # Set defaults
        for spec in option_specs:
            key = spec.long if spec.long else spec.short
            converted_options[key] = spec.default
        
        # Process provided options
        for opt_key, opt_value in parsed.options.items():
            # Find matching option spec
            spec = None
            for s in option_specs:
                if s.short == opt_key or s.long == opt_key:
                    spec = s
                    break
            
            if not spec:
                raise ValueError(f"Unknown option: {opt_key}")
            
            # Convert value
            if spec.has_value:
                converted_value = CommandParser._convert_value(
                    opt_value, spec.arg_type, opt_key
                )
            else:
                converted_value = opt_value
            
            # Store with canonical name (prefer long form)
            key = spec.long if spec.long else spec.short
            converted_options[key] = converted_value
        
        return converted_args, converted_options
    
    @staticmethod
    def _convert_value(value: str, arg_type: ArgumentType, name: str) -> Any:
        """
        Convert string value to specified type.
        
        Args:
            value: String value to convert
            arg_type: Target type
            name: Argument name (for error messages)
            
        Returns:
            Converted value
            
        Raises:
            ValueError: If conversion fails
        """
        try:
            if arg_type == ArgumentType.STRING:
                return str(value)
            elif arg_type == ArgumentType.INTEGER:
                return int(value)
            elif arg_type == ArgumentType.FLOAT:
                return float(value)
            elif arg_type == ArgumentType.BOOLEAN:
                lower = value.lower()
                if lower in ("true", "yes", "1", "on"):
                    return True
                elif lower in ("false", "no", "0", "off"):
                    return False
                else:
                    raise ValueError(f"Invalid boolean value: {value}")
            elif arg_type == ArgumentType.COMPONENT_ID:
                # Basic validation: should be non-empty string
                if not value:
                    raise ValueError("Component ID cannot be empty")
                return str(value)
            elif arg_type == ArgumentType.VNET_ID:
                # Basic validation: should be non-empty string
                if not value:
                    raise ValueError("VNET ID cannot be empty")
                return str(value)
            elif arg_type == ArgumentType.FILENAME:
                # Basic validation: should be non-empty string
                if not value:
                    raise ValueError("Filename cannot be empty")
                return str(value)
            else:
                return str(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert {name} to {arg_type.value}: {e}")


class CommandRegistry:
    """
    Registry for commands with dispatch functionality.
    
    Manages command registration, lookup, and execution.
    """
    
    def __init__(self):
        """Initialize empty command registry."""
        self._commands: Dict[str, Command] = {}
        self._aliases: Dict[str, str] = {}
    
    def register(self, command: Command) -> None:
        """
        Register a command.
        
        Args:
            command: Command to register
            
        Raises:
            ValueError: If command name or alias is already registered
        """
        # Check for duplicate name
        if command.name in self._commands:
            raise ValueError(f"Command already registered: {command.name}")
        
        # Check for duplicate aliases
        for alias in command.aliases:
            if alias in self._aliases:
                raise ValueError(f"Alias already registered: {alias}")
        
        # Register command
        self._commands[command.name] = command
        
        # Register aliases
        for alias in command.aliases:
            self._aliases[alias] = command.name
    
    def unregister(self, name: str) -> None:
        """
        Unregister a command.
        
        Args:
            name: Command name to unregister
        """
        if name in self._commands:
            cmd = self._commands[name]
            # Remove aliases
            for alias in cmd.aliases:
                if alias in self._aliases:
                    del self._aliases[alias]
            # Remove command
            del self._commands[name]
    
    def get_command(self, name: str) -> Optional[Command]:
        """
        Get command by name or alias.
        
        Args:
            name: Command name or alias
            
        Returns:
            Command object or None if not found
        """
        # Check direct name
        if name in self._commands:
            return self._commands[name]
        
        # Check alias
        if name in self._aliases:
            real_name = self._aliases[name]
            return self._commands.get(real_name)
        
        return None
    
    def list_commands(self) -> List[str]:
        """Get list of all registered command names."""
        return sorted(self._commands.keys())
    
    def parse_and_execute(
        self,
        command_line: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Parse command line and execute command.
        
        Args:
            command_line: Raw command line
            context: Context dictionary passed to handler
            
        Returns:
            Command result string
            
        Raises:
            ValueError: If parsing or validation fails
        """
        # Parse command line
        parsed = CommandParser.parse(command_line)
        
        # Get command
        command = self.get_command(parsed.command_name)
        if not command:
            raise ValueError(f"Unknown command: {parsed.command_name}")
        
        # Validate and convert arguments
        args, options = CommandParser.validate_and_convert(
            parsed,
            command.arg_specs,
            command.option_specs
        )
        
        # Execute handler
        try:
            result = command.handler(args, options, context)
            return result if result is not None else ""
        except Exception as e:
            raise ValueError(f"Command execution failed: {e}")
    
    def get_help(self, command_name: Optional[str] = None, verbose: bool = False) -> str:
        """
        Get help text for command(s).
        
        Args:
            command_name: Specific command name, or None for all commands
            verbose: Include detailed help
            
        Returns:
            Help text string
        """
        if command_name:
            command = self.get_command(command_name)
            if not command:
                return f"Unknown command: {command_name}"
            return command.get_help(verbose=verbose)
        else:
            # List all commands
            lines = ["Available commands:"]
            for name in self.list_commands():
                command = self._commands[name]
                lines.append(f"  {name:15s} - {command.help_text}")
            lines.append("")
            lines.append("Type 'help <command>' for detailed help on a specific command.")
            return "\n".join(lines)


def create_command_registry() -> CommandRegistry:
    """
    Create and return a new CommandRegistry.
    
    Convenience function for creating a registry.
    
    Returns:
        New CommandRegistry instance
    """
    return CommandRegistry()

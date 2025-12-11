"""
Unit tests for Command Parser module

Tests command parsing, validation, and dispatch functionality.
"""

import unittest
from networking.command_parser import (
    CommandParser,
    Command,
    CommandRegistry,
    ParsedCommand,
    ArgumentSpec,
    OptionSpec,
    ArgumentType,
    create_command_registry
)


class TestCommandParser(unittest.TestCase):
    """Test CommandParser class."""
    
    def test_parse_simple_command(self):
        """Test parsing a simple command with no arguments."""
        parsed = CommandParser.parse("help")
        
        self.assertEqual(parsed.command_name, "help")
        self.assertEqual(parsed.args, [])
        self.assertEqual(parsed.options, {})
        self.assertEqual(parsed.raw_line, "help")
    
    def test_parse_command_with_arguments(self):
        """Test parsing command with positional arguments."""
        parsed = CommandParser.parse("load circuit.rsim")
        
        self.assertEqual(parsed.command_name, "load")
        self.assertEqual(parsed.args, ["circuit.rsim"])
        self.assertEqual(parsed.options, {})
    
    def test_parse_multiple_arguments(self):
        """Test parsing command with multiple arguments."""
        parsed = CommandParser.parse("set component SW1 state HIGH")
        
        self.assertEqual(parsed.command_name, "set")
        self.assertEqual(parsed.args, ["component", "SW1", "state", "HIGH"])
        self.assertEqual(parsed.options, {})
    
    def test_parse_quoted_arguments(self):
        """Test parsing quoted arguments with spaces."""
        parsed = CommandParser.parse('load "my circuit.rsim"')
        
        self.assertEqual(parsed.command_name, "load")
        self.assertEqual(parsed.args, ["my circuit.rsim"])
    
    def test_parse_single_quoted_arguments(self):
        """Test parsing single-quoted arguments."""
        parsed = CommandParser.parse("echo 'hello world'")
        
        self.assertEqual(parsed.command_name, "echo")
        self.assertEqual(parsed.args, ["hello world"])
    
    def test_parse_short_option(self):
        """Test parsing short option (-v)."""
        parsed = CommandParser.parse("list -v")
        
        self.assertEqual(parsed.command_name, "list")
        self.assertEqual(parsed.args, [])
        self.assertEqual(parsed.options, {"v": True})
    
    def test_parse_long_option(self):
        """Test parsing long option (--verbose)."""
        parsed = CommandParser.parse("list --verbose")
        
        self.assertEqual(parsed.command_name, "list")
        self.assertEqual(parsed.args, [])
        self.assertEqual(parsed.options, {"verbose": True})
    
    def test_parse_option_with_value(self):
        """Test parsing option with value using = syntax."""
        parsed = CommandParser.parse("load --format=json circuit.rsim")
        
        self.assertEqual(parsed.command_name, "load")
        self.assertEqual(parsed.args, ["circuit.rsim"])
        self.assertEqual(parsed.options, {"format": "json"})
    
    def test_parse_option_with_equals(self):
        """Test parsing option with = syntax."""
        parsed = CommandParser.parse("load --format=json circuit.rsim")
        
        self.assertEqual(parsed.command_name, "load")
        self.assertEqual(parsed.args, ["circuit.rsim"])
        self.assertEqual(parsed.options, {"format": "json"})
    
    def test_parse_mixed_args_and_options(self):
        """Test parsing command with both arguments and options."""
        parsed = CommandParser.parse("list components --verbose --type=relay")
        
        self.assertEqual(parsed.command_name, "list")
        self.assertEqual(parsed.args, ["components"])
        self.assertEqual(parsed.options, {"verbose": True, "type": "relay"})
    
    def test_parse_empty_command(self):
        """Test parsing empty command raises error."""
        with self.assertRaises(ValueError):
            CommandParser.parse("")
    
    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only command raises error."""
        with self.assertRaises(ValueError):
            CommandParser.parse("   ")
    
    def test_parse_case_insensitive_command(self):
        """Test command names are converted to lowercase."""
        parsed = CommandParser.parse("HELP")
        
        self.assertEqual(parsed.command_name, "help")
    
    def test_parse_escaped_quotes(self):
        """Test parsing escaped quotes in arguments."""
        parsed = CommandParser.parse(r'echo "say \"hello\""')
        
        self.assertEqual(parsed.command_name, "echo")
        self.assertEqual(parsed.args, ['say "hello"'])


class TestArgumentValidation(unittest.TestCase):
    """Test argument validation and conversion."""
    
    def test_validate_string_argument(self):
        """Test validating string argument."""
        parsed = ParsedCommand("load", args=["circuit.rsim"])
        specs = [ArgumentSpec("filename", ArgumentType.STRING)]
        
        args, _ = CommandParser.validate_and_convert(parsed, specs, [])
        
        self.assertEqual(args, ["circuit.rsim"])
    
    def test_validate_integer_argument(self):
        """Test validating integer argument."""
        parsed = ParsedCommand("repeat", args=["5"])
        specs = [ArgumentSpec("count", ArgumentType.INTEGER)]
        
        args, _ = CommandParser.validate_and_convert(parsed, specs, [])
        
        self.assertEqual(args, [5])
        self.assertIsInstance(args[0], int)
    
    def test_validate_float_argument(self):
        """Test validating float argument."""
        parsed = ParsedCommand("delay", args=["1.5"])
        specs = [ArgumentSpec("seconds", ArgumentType.FLOAT)]
        
        args, _ = CommandParser.validate_and_convert(parsed, specs, [])
        
        self.assertEqual(args, [1.5])
        self.assertIsInstance(args[0], float)
    
    def test_validate_boolean_argument(self):
        """Test validating boolean argument."""
        for true_val in ["true", "yes", "1", "on", "True", "YES"]:
            parsed = ParsedCommand("set", args=[true_val])
            specs = [ArgumentSpec("enabled", ArgumentType.BOOLEAN)]
            
            args, _ = CommandParser.validate_and_convert(parsed, specs, [])
            
            self.assertEqual(args, [True])
        
        for false_val in ["false", "no", "0", "off", "False", "NO"]:
            parsed = ParsedCommand("set", args=[false_val])
            specs = [ArgumentSpec("enabled", ArgumentType.BOOLEAN)]
            
            args, _ = CommandParser.validate_and_convert(parsed, specs, [])
            
            self.assertEqual(args, [False])
    
    def test_validate_component_id(self):
        """Test validating component ID argument."""
        parsed = ParsedCommand("show", args=["SW1"])
        specs = [ArgumentSpec("component_id", ArgumentType.COMPONENT_ID)]
        
        args, _ = CommandParser.validate_and_convert(parsed, specs, [])
        
        self.assertEqual(args, ["SW1"])
    
    def test_validate_required_argument_missing(self):
        """Test missing required argument raises error."""
        parsed = ParsedCommand("load", args=[])
        specs = [ArgumentSpec("filename", ArgumentType.STRING, required=True)]
        
        with self.assertRaises(ValueError) as cm:
            CommandParser.validate_and_convert(parsed, specs, [])
        
        self.assertIn("Missing required argument", str(cm.exception))
    
    def test_validate_optional_argument_default(self):
        """Test optional argument uses default value."""
        parsed = ParsedCommand("list", args=[])
        specs = [ArgumentSpec("type", ArgumentType.STRING, required=False, default="all")]
        
        args, _ = CommandParser.validate_and_convert(parsed, specs, [])
        
        self.assertEqual(args, ["all"])
    
    def test_validate_too_many_arguments(self):
        """Test too many arguments raises error."""
        parsed = ParsedCommand("help", args=["command", "extra"])
        specs = [ArgumentSpec("command", ArgumentType.STRING)]
        
        with self.assertRaises(ValueError) as cm:
            CommandParser.validate_and_convert(parsed, specs, [])
        
        self.assertIn("Too many arguments", str(cm.exception))
    
    def test_validate_invalid_integer(self):
        """Test invalid integer raises error."""
        parsed = ParsedCommand("repeat", args=["abc"])
        specs = [ArgumentSpec("count", ArgumentType.INTEGER)]
        
        with self.assertRaises(ValueError) as cm:
            CommandParser.validate_and_convert(parsed, specs, [])
        
        self.assertIn("Cannot convert", str(cm.exception))
    
    def test_validate_choices(self):
        """Test argument with limited choices."""
        parsed = ParsedCommand("set", args=["HIGH"])
        specs = [
            ArgumentSpec(
                "state",
                ArgumentType.STRING,
                choices=["HIGH", "FLOAT"]
            )
        ]
        
        args, _ = CommandParser.validate_and_convert(parsed, specs, [])
        
        self.assertEqual(args, ["HIGH"])
    
    def test_validate_invalid_choice(self):
        """Test invalid choice raises error."""
        parsed = ParsedCommand("set", args=["INVALID"])
        specs = [
            ArgumentSpec(
                "state",
                ArgumentType.STRING,
                choices=["HIGH", "FLOAT"]
            )
        ]
        
        with self.assertRaises(ValueError) as cm:
            CommandParser.validate_and_convert(parsed, specs, [])
        
        self.assertIn("Invalid value", str(cm.exception))
        self.assertIn("Valid choices", str(cm.exception))


class TestOptionValidation(unittest.TestCase):
    """Test option validation and conversion."""
    
    def test_validate_boolean_option(self):
        """Test validating boolean option."""
        parsed = ParsedCommand("list", options={"verbose": True})
        specs = [OptionSpec(short="v", long="verbose")]
        
        _, options = CommandParser.validate_and_convert(parsed, [], specs)
        
        self.assertEqual(options, {"verbose": True})
    
    def test_validate_option_with_value(self):
        """Test validating option with value."""
        parsed = ParsedCommand("load", options={"format": "json"})
        specs = [
            OptionSpec(
                long="format",
                arg_type=ArgumentType.STRING,
                has_value=True,
                default="rsim"
            )
        ]
        
        _, options = CommandParser.validate_and_convert(parsed, [], specs)
        
        self.assertEqual(options, {"format": "json"})
    
    def test_validate_option_default_value(self):
        """Test option uses default value when not provided."""
        parsed = ParsedCommand("list", options={})
        specs = [
            OptionSpec(
                long="verbose",
                default=False
            )
        ]
        
        _, options = CommandParser.validate_and_convert(parsed, [], specs)
        
        self.assertEqual(options, {"verbose": False})
    
    def test_validate_unknown_option(self):
        """Test unknown option raises error."""
        parsed = ParsedCommand("list", options={"unknown": True})
        specs = []
        
        with self.assertRaises(ValueError) as cm:
            CommandParser.validate_and_convert(parsed, [], specs)
        
        self.assertIn("Unknown option", str(cm.exception))
    
    def test_option_short_name_lookup(self):
        """Test option lookup by short name."""
        parsed = ParsedCommand("list", options={"v": True})
        specs = [OptionSpec(short="v", long="verbose")]
        
        _, options = CommandParser.validate_and_convert(parsed, [], specs)
        
        # Should use long name in result
        self.assertEqual(options, {"verbose": True})
    
    def test_option_matches(self):
        """Test OptionSpec.matches method."""
        spec = OptionSpec(short="v", long="verbose")
        
        self.assertTrue(spec.matches("-v"))
        self.assertTrue(spec.matches("--verbose"))
        self.assertFalse(spec.matches("-x"))
        self.assertFalse(spec.matches("--other"))


class TestCommand(unittest.TestCase):
    """Test Command class."""
    
    def test_command_creation(self):
        """Test creating a command."""
        def handler(args, options, context):
            return "result"
        
        cmd = Command(
            name="test",
            handler=handler,
            help_text="Test command"
        )
        
        self.assertEqual(cmd.name, "test")
        self.assertEqual(cmd.handler, handler)
        self.assertEqual(cmd.help_text, "Test command")
    
    def test_command_get_usage_simple(self):
        """Test usage string for simple command."""
        cmd = Command(name="help", handler=lambda a, o, c: "")
        
        usage = cmd.get_usage()
        
        self.assertEqual(usage, "help")
    
    def test_command_get_usage_with_args(self):
        """Test usage string with arguments."""
        cmd = Command(
            name="load",
            handler=lambda a, o, c: "",
            arg_specs=[
                ArgumentSpec("filename", ArgumentType.STRING, required=True)
            ]
        )
        
        usage = cmd.get_usage()
        
        self.assertEqual(usage, "load <filename>")
    
    def test_command_get_usage_with_optional_arg(self):
        """Test usage string with optional argument."""
        cmd = Command(
            name="list",
            handler=lambda a, o, c: "",
            arg_specs=[
                ArgumentSpec("type", ArgumentType.STRING, required=False)
            ]
        )
        
        usage = cmd.get_usage()
        
        self.assertEqual(usage, "list [type]")
    
    def test_command_get_usage_with_options(self):
        """Test usage string with options."""
        cmd = Command(
            name="list",
            handler=lambda a, o, c: "",
            option_specs=[
                OptionSpec(short="v", long="verbose")
            ]
        )
        
        usage = cmd.get_usage()
        
        self.assertIn("[-v|--verbose]", usage)
    
    def test_command_get_help_brief(self):
        """Test brief help text."""
        cmd = Command(
            name="help",
            handler=lambda a, o, c: "",
            help_text="Display help information"
        )
        
        help_text = cmd.get_help(verbose=False)
        
        self.assertIn("help", help_text)
        self.assertIn("Display help information", help_text)
    
    def test_command_get_help_verbose(self):
        """Test verbose help text."""
        cmd = Command(
            name="load",
            handler=lambda a, o, c: "",
            help_text="Load a circuit file",
            long_help="Loads a .rsim circuit file into the simulator.",
            arg_specs=[
                ArgumentSpec(
                    "filename",
                    ArgumentType.FILENAME,
                    required=True,
                    help_text="Path to .rsim file"
                )
            ],
            option_specs=[
                OptionSpec(
                    short="v",
                    long="verbose",
                    help_text="Show detailed loading information"
                )
            ]
        )
        
        help_text = cmd.get_help(verbose=True)
        
        self.assertIn("load", help_text)
        self.assertIn("Load a circuit file", help_text)
        self.assertIn("Usage:", help_text)
        self.assertIn("Arguments:", help_text)
        self.assertIn("filename", help_text)
        self.assertIn("Options:", help_text)
        self.assertIn("-v", help_text)
        self.assertIn("--verbose", help_text)


class TestCommandRegistry(unittest.TestCase):
    """Test CommandRegistry class."""
    
    def test_registry_creation(self):
        """Test creating a registry."""
        registry = CommandRegistry()
        
        self.assertEqual(registry.list_commands(), [])
    
    def test_register_command(self):
        """Test registering a command."""
        registry = CommandRegistry()
        
        cmd = Command(
            name="help",
            handler=lambda a, o, c: "help text"
        )
        
        registry.register(cmd)
        
        self.assertEqual(registry.list_commands(), ["help"])
    
    def test_register_duplicate_command(self):
        """Test registering duplicate command raises error."""
        registry = CommandRegistry()
        
        cmd1 = Command(name="help", handler=lambda a, o, c: "")
        cmd2 = Command(name="help", handler=lambda a, o, c: "")
        
        registry.register(cmd1)
        
        with self.assertRaises(ValueError) as cm:
            registry.register(cmd2)
        
        self.assertIn("already registered", str(cm.exception))
    
    def test_register_with_alias(self):
        """Test registering command with alias."""
        registry = CommandRegistry()
        
        cmd = Command(
            name="help",
            handler=lambda a, o, c: "help",
            aliases=["?", "h"]
        )
        
        registry.register(cmd)
        
        # Should be able to get by name or alias
        self.assertEqual(registry.get_command("help").name, "help")
        self.assertEqual(registry.get_command("?").name, "help")
        self.assertEqual(registry.get_command("h").name, "help")
    
    def test_register_duplicate_alias(self):
        """Test registering duplicate alias raises error."""
        registry = CommandRegistry()
        
        cmd1 = Command(name="help", handler=lambda a, o, c: "", aliases=["?"])
        cmd2 = Command(name="info", handler=lambda a, o, c: "", aliases=["?"])
        
        registry.register(cmd1)
        
        with self.assertRaises(ValueError) as cm:
            registry.register(cmd2)
        
        self.assertIn("Alias already registered", str(cm.exception))
    
    def test_unregister_command(self):
        """Test unregistering a command."""
        registry = CommandRegistry()
        
        cmd = Command(name="help", handler=lambda a, o, c: "", aliases=["?"])
        registry.register(cmd)
        
        registry.unregister("help")
        
        self.assertEqual(registry.list_commands(), [])
        self.assertIsNone(registry.get_command("help"))
        self.assertIsNone(registry.get_command("?"))
    
    def test_get_command_not_found(self):
        """Test getting non-existent command returns None."""
        registry = CommandRegistry()
        
        self.assertIsNone(registry.get_command("unknown"))
    
    def test_list_commands_sorted(self):
        """Test list_commands returns sorted list."""
        registry = CommandRegistry()
        
        registry.register(Command(name="zebra", handler=lambda a, o, c: ""))
        registry.register(Command(name="apple", handler=lambda a, o, c: ""))
        registry.register(Command(name="monkey", handler=lambda a, o, c: ""))
        
        self.assertEqual(registry.list_commands(), ["apple", "monkey", "zebra"])
    
    def test_parse_and_execute(self):
        """Test parsing and executing a command."""
        registry = CommandRegistry()
        
        def handler(args, options, context):
            return f"Hello {args[0]}"
        
        cmd = Command(
            name="greet",
            handler=handler,
            arg_specs=[ArgumentSpec("name", ArgumentType.STRING)]
        )
        
        registry.register(cmd)
        
        result = registry.parse_and_execute("greet World", {})
        
        self.assertEqual(result, "Hello World")
    
    def test_parse_and_execute_with_context(self):
        """Test command receives context."""
        registry = CommandRegistry()
        
        def handler(args, options, context):
            return f"User: {context['user']}"
        
        cmd = Command(name="whoami", handler=handler)
        registry.register(cmd)
        
        result = registry.parse_and_execute("whoami", {"user": "admin"})
        
        self.assertEqual(result, "User: admin")
    
    def test_parse_and_execute_unknown_command(self):
        """Test executing unknown command raises error."""
        registry = CommandRegistry()
        
        with self.assertRaises(ValueError) as cm:
            registry.parse_and_execute("unknown", {})
        
        self.assertIn("Unknown command", str(cm.exception))
    
    def test_parse_and_execute_validation_error(self):
        """Test validation error is raised."""
        registry = CommandRegistry()
        
        cmd = Command(
            name="load",
            handler=lambda a, o, c: "",
            arg_specs=[ArgumentSpec("filename", ArgumentType.STRING, required=True)]
        )
        
        registry.register(cmd)
        
        with self.assertRaises(ValueError) as cm:
            registry.parse_and_execute("load", {})
        
        self.assertIn("Missing required argument", str(cm.exception))
    
    def test_parse_and_execute_handler_error(self):
        """Test handler exception is wrapped."""
        registry = CommandRegistry()
        
        def failing_handler(args, options, context):
            raise RuntimeError("Handler failed")
        
        cmd = Command(name="fail", handler=failing_handler)
        registry.register(cmd)
        
        with self.assertRaises(ValueError) as cm:
            registry.parse_and_execute("fail", {})
        
        self.assertIn("Command execution failed", str(cm.exception))
    
    def test_get_help_all_commands(self):
        """Test getting help for all commands."""
        registry = CommandRegistry()
        
        registry.register(Command(
            name="help",
            handler=lambda a, o, c: "",
            help_text="Display help"
        ))
        registry.register(Command(
            name="quit",
            handler=lambda a, o, c: "",
            help_text="Exit program"
        ))
        
        help_text = registry.get_help()
        
        self.assertIn("Available commands", help_text)
        self.assertIn("help", help_text)
        self.assertIn("quit", help_text)
        self.assertIn("Display help", help_text)
        self.assertIn("Exit program", help_text)
    
    def test_get_help_specific_command(self):
        """Test getting help for specific command."""
        registry = CommandRegistry()
        
        cmd = Command(
            name="load",
            handler=lambda a, o, c: "",
            help_text="Load a file",
            long_help="Detailed loading instructions"
        )
        
        registry.register(cmd)
        
        help_text = registry.get_help("load", verbose=True)
        
        self.assertIn("load", help_text)
        self.assertIn("Load a file", help_text)
        self.assertIn("Detailed loading instructions", help_text)
    
    def test_get_help_unknown_command(self):
        """Test getting help for unknown command."""
        registry = CommandRegistry()
        
        help_text = registry.get_help("unknown")
        
        self.assertIn("Unknown command", help_text)


class TestConvenienceFunction(unittest.TestCase):
    """Test convenience functions."""
    
    def test_create_command_registry(self):
        """Test create_command_registry function."""
        registry = create_command_registry()
        
        self.assertIsInstance(registry, CommandRegistry)
        self.assertEqual(registry.list_commands(), [])


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components."""
    
    def test_full_command_flow(self):
        """Test complete command flow from parse to execute."""
        # Create registry
        registry = CommandRegistry()
        
        # Define handler
        def load_handler(args, options, context):
            filename = args[0]
            verbose = options.get("verbose", False)
            
            if verbose:
                return f"Loading {filename} with verbose output..."
            else:
                return f"Loading {filename}..."
        
        # Register command
        registry.register(Command(
            name="load",
            handler=load_handler,
            help_text="Load a circuit file",
            arg_specs=[
                ArgumentSpec("filename", ArgumentType.FILENAME, required=True)
            ],
            option_specs=[
                OptionSpec(short="v", long="verbose")
            ]
        ))
        
        # Execute without verbose
        result1 = registry.parse_and_execute("load circuit.rsim", {})
        self.assertEqual(result1, "Loading circuit.rsim...")
        
        # Execute with verbose
        result2 = registry.parse_and_execute("load --verbose circuit.rsim", {})
        self.assertEqual(result2, "Loading circuit.rsim with verbose output...")
    
    def test_multiple_commands(self):
        """Test registry with multiple commands."""
        registry = CommandRegistry()
        
        # Register several commands
        registry.register(Command(
            name="help",
            handler=lambda a, o, c: "Help text",
            help_text="Show help"
        ))
        
        registry.register(Command(
            name="quit",
            handler=lambda a, o, c: "Goodbye",
            help_text="Exit program",
            aliases=["exit", "bye"]
        ))
        
        registry.register(Command(
            name="echo",
            handler=lambda a, o, c: " ".join(a),
            help_text="Echo arguments",
            arg_specs=[
                ArgumentSpec("text", ArgumentType.STRING, required=True)
            ]
        ))
        
        # Test each command
        self.assertEqual(registry.parse_and_execute("help", {}), "Help text")
        self.assertEqual(registry.parse_and_execute("quit", {}), "Goodbye")
        self.assertEqual(registry.parse_and_execute("exit", {}), "Goodbye")
        self.assertEqual(registry.parse_and_execute("echo hello", {}), "hello")
        
        # Test listing
        commands = registry.list_commands()
        self.assertEqual(commands, ["echo", "help", "quit"])


if __name__ == "__main__":
    unittest.main()

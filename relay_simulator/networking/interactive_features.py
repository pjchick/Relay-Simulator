"""
Interactive terminal features: command history, tab completion, enhanced prompts.

Provides readline-like functionality for the terminal interface.
"""

from typing import List, Optional, Callable, Dict, Any, Tuple
from collections import deque


class CommandHistory:
    """
    Manage command history with navigation.
    
    Supports:
    - Up/down arrow navigation
    - History buffer with configurable max size
    - History search
    - Persistence (optional)
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize command history.
        
        Args:
            max_size: Maximum number of commands to store (default: 100)
        """
        self.max_size = max_size
        self.history: deque = deque(maxlen=max_size)
        self.current_index: int = -1  # -1 = not navigating
        self.temp_command: str = ""  # Store current input when navigating
    
    def add(self, command: str):
        """
        Add command to history.
        
        Args:
            command: Command to add
        """
        if not command or not command.strip():
            return
        
        # Don't add duplicate consecutive commands
        if self.history and self.history[-1] == command:
            return
        
        self.history.append(command)
        self.current_index = -1  # Reset navigation
    
    def navigate_up(self, current_input: str = "") -> Optional[str]:
        """
        Navigate to previous command in history (up arrow).
        
        Args:
            current_input: Current command line input
            
        Returns:
            Previous command or None if at end
        """
        if not self.history:
            return None
        
        # First time navigating - save current input
        if self.current_index == -1:
            self.temp_command = current_input
            self.current_index = len(self.history) - 1
        elif self.current_index > 0:
            self.current_index -= 1
        else:
            # Already at oldest
            return None
        
        return self.history[self.current_index]
    
    def navigate_down(self) -> Optional[str]:
        """
        Navigate to next command in history (down arrow).
        
        Returns:
            Next command, temp command, or None
        """
        if self.current_index == -1:
            return None
        
        self.current_index += 1
        
        if self.current_index >= len(self.history):
            # Back to current input
            self.current_index = -1
            return self.temp_command
        
        return self.history[self.current_index]
    
    def reset_navigation(self):
        """Reset navigation state."""
        self.current_index = -1
        self.temp_command = ""
    
    def search(self, query: str) -> List[str]:
        """
        Search history for commands containing query.
        
        Args:
            query: Search string
            
        Returns:
            List of matching commands
        """
        query_lower = query.lower()
        return [cmd for cmd in self.history if query_lower in cmd.lower()]
    
    def get_all(self) -> List[str]:
        """Get all commands in history."""
        return list(self.history)
    
    def clear(self):
        """Clear all history."""
        self.history.clear()
        self.current_index = -1
        self.temp_command = ""


class TabCompleter:
    """
    Tab completion for commands and arguments.
    
    Supports:
    - Command name completion
    - Argument completion (IDs, filenames, etc.)
    - Multiple completion candidates
    - Custom completion providers
    """
    
    def __init__(self):
        """Initialize tab completer."""
        self.commands: List[str] = []
        self.completion_providers: Dict[str, Callable] = {}
    
    def set_commands(self, commands: List[str]):
        """
        Set available command names for completion.
        
        Args:
            commands: List of command names
        """
        self.commands = sorted(commands)
    
    def register_provider(self, command: str, provider: Callable[[str, int], List[str]]):
        """
        Register argument completion provider for a command.
        
        Args:
            command: Command name
            provider: Function(text, arg_index) -> List[completions]
        """
        self.completion_providers[command] = provider
    
    def complete(self, text: str, cursor_pos: Optional[int] = None) -> Tuple[List[str], str]:
        """
        Get completion candidates for current input.
        
        Args:
            text: Current input text
            cursor_pos: Cursor position (default: end of text)
            
        Returns:
            Tuple of (candidates, common_prefix)
        """
        if cursor_pos is None:
            cursor_pos = len(text)
        
        # Get text up to cursor
        text = text[:cursor_pos]
        
        # Split into parts
        parts = text.split()
        
        if not parts or (len(parts) == 1 and not text.endswith(' ')):
            # Complete command name
            prefix = parts[0] if parts else ""
            candidates = self._complete_command(prefix)
        else:
            # Complete argument
            command = parts[0]
            arg_index = len(parts) - 1
            current_arg = parts[-1] if parts and not text.endswith(' ') else ""
            
            candidates = self._complete_argument(command, current_arg, arg_index)
        
        # Find common prefix
        if candidates:
            common_prefix = self._find_common_prefix(candidates)
        else:
            common_prefix = ""
        
        return candidates, common_prefix
    
    def _complete_command(self, prefix: str) -> List[str]:
        """
        Complete command name.
        
        Args:
            prefix: Command prefix
            
        Returns:
            List of matching commands
        """
        prefix_lower = prefix.lower()
        return [cmd for cmd in self.commands if cmd.lower().startswith(prefix_lower)]
    
    def _complete_argument(self, command: str, current_arg: str, arg_index: int) -> List[str]:
        """
        Complete command argument.
        
        Args:
            command: Command name
            current_arg: Current argument text
            arg_index: Argument index (0-based)
            
        Returns:
            List of completion candidates
        """
        # Check if we have a provider for this command
        provider = self.completion_providers.get(command)
        if provider:
            try:
                return provider(current_arg, arg_index)
            except Exception:
                return []
        
        return []
    
    def _find_common_prefix(self, strings: List[str]) -> str:
        """
        Find common prefix of strings.
        
        Args:
            strings: List of strings
            
        Returns:
            Common prefix
        """
        if not strings:
            return ""
        
        if len(strings) == 1:
            return strings[0]
        
        # Find shortest string length
        min_len = min(len(s) for s in strings)
        
        # Find common prefix
        for i in range(min_len):
            char = strings[0][i]
            if not all(s[i] == char for s in strings):
                return strings[0][:i]
        
        return strings[0][:min_len]


class PromptFormatter:
    """
    Format dynamic terminal prompts with status information.
    
    Supports:
    - Custom prompt templates
    - Status placeholders (document, simulation, etc.)
    - Color support
    """
    
    def __init__(self, template: str = "relay> "):
        """
        Initialize prompt formatter.
        
        Args:
            template: Prompt template with placeholders
        """
        self.template = template
        self.context: Dict[str, Any] = {}
    
    def set_context(self, context: Dict[str, Any]):
        """
        Update prompt context.
        
        Args:
            context: Context dictionary with status info
        """
        self.context = context
    
    def format(self) -> str:
        """
        Format prompt with current context.
        
        Returns:
            Formatted prompt string
        """
        # Simple template replacement
        prompt = self.template
        
        # Replace placeholders
        for key, value in self.context.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))
        
        return prompt


class KeyHandler:
    """
    Handle special key sequences (arrows, Ctrl+C, etc.).
    
    Manages ANSI escape sequence parsing for terminal control.
    """
    
    # ANSI escape sequences
    ESC = '\x1b'
    ARROW_UP = '\x1b[A'
    ARROW_DOWN = '\x1b[B'
    ARROW_LEFT = '\x1b[D'
    ARROW_RIGHT = '\x1b[C'
    HOME = '\x1b[H'
    END = '\x1b[F'
    DELETE = '\x1b[3~'
    
    # Control characters
    CTRL_C = '\x03'
    CTRL_D = '\x04'
    CTRL_L = '\x0c'
    TAB = '\t'
    BACKSPACE = '\x7f'
    DELETE_CHAR = '\x08'
    
    def __init__(self):
        """Initialize key handler."""
        self.escape_buffer = ""
        self.in_escape = False
    
    def process(self, char: str) -> Optional[str]:
        """
        Process incoming character and detect key sequences.
        
        Args:
            char: Input character
            
        Returns:
            Key name if sequence complete, None otherwise
        """
        # Handle escape sequences
        if char == self.ESC:
            self.in_escape = True
            self.escape_buffer = char
            return None
        
        if self.in_escape:
            self.escape_buffer += char
            
            # Check for complete sequences
            if self.escape_buffer == self.ARROW_UP:
                self.in_escape = False
                self.escape_buffer = ""
                return 'ARROW_UP'
            elif self.escape_buffer == self.ARROW_DOWN:
                self.in_escape = False
                self.escape_buffer = ""
                return 'ARROW_DOWN'
            elif self.escape_buffer == self.ARROW_LEFT:
                self.in_escape = False
                self.escape_buffer = ""
                return 'ARROW_LEFT'
            elif self.escape_buffer == self.ARROW_RIGHT:
                self.in_escape = False
                self.escape_buffer = ""
                return 'ARROW_RIGHT'
            elif self.escape_buffer == self.HOME:
                self.in_escape = False
                self.escape_buffer = ""
                return 'HOME'
            elif self.escape_buffer == self.END:
                self.in_escape = False
                self.escape_buffer = ""
                return 'END'
            elif self.escape_buffer == self.DELETE:
                self.in_escape = False
                self.escape_buffer = ""
                return 'DELETE'
            
            # Incomplete sequence - wait for more chars
            return None
        
        # Handle control characters
        if char == self.CTRL_C:
            return 'CTRL_C'
        elif char == self.CTRL_D:
            return 'CTRL_D'
        elif char == self.CTRL_L:
            return 'CTRL_L'
        elif char == self.TAB:
            return 'TAB'
        elif char in (self.BACKSPACE, self.DELETE_CHAR):
            return 'BACKSPACE'
        
        # Regular character
        return 'CHAR'
    
    def reset(self):
        """Reset escape sequence state."""
        self.escape_buffer = ""
        self.in_escape = False


class InteractiveLineEditor:
    """
    Interactive line editor with history and completion.
    
    Combines CommandHistory, TabCompleter, and KeyHandler for
    full readline-like functionality.
    """
    
    def __init__(self, 
                 history: Optional[CommandHistory] = None,
                 completer: Optional[TabCompleter] = None):
        """
        Initialize line editor.
        
        Args:
            history: CommandHistory instance (default: create new)
            completer: TabCompleter instance (default: create new)
        """
        self.history = history or CommandHistory()
        self.completer = completer or TabCompleter()
        self.key_handler = KeyHandler()
        
        self.line = ""
        self.cursor = 0
    
    def handle_key(self, key_name: str, char: str = "") -> Tuple[str, bool]:
        """
        Handle key press.
        
        Args:
            key_name: Key name from KeyHandler
            char: Character (for CHAR keys)
            
        Returns:
            Tuple of (updated_line, is_complete)
        """
        if key_name == 'CHAR':
            # Insert character at cursor
            self.line = self.line[:self.cursor] + char + self.line[self.cursor:]
            self.cursor += 1
            return self.line, False
        
        elif key_name == 'BACKSPACE':
            if self.cursor > 0:
                self.line = self.line[:self.cursor-1] + self.line[self.cursor:]
                self.cursor -= 1
            return self.line, False
        
        elif key_name == 'DELETE':
            if self.cursor < len(self.line):
                self.line = self.line[:self.cursor] + self.line[self.cursor+1:]
            return self.line, False
        
        elif key_name == 'ARROW_LEFT':
            if self.cursor > 0:
                self.cursor -= 1
            return self.line, False
        
        elif key_name == 'ARROW_RIGHT':
            if self.cursor < len(self.line):
                self.cursor += 1
            return self.line, False
        
        elif key_name == 'HOME':
            self.cursor = 0
            return self.line, False
        
        elif key_name == 'END':
            self.cursor = len(self.line)
            return self.line, False
        
        elif key_name == 'ARROW_UP':
            # Navigate history up
            prev = self.history.navigate_up(self.line)
            if prev is not None:
                self.line = prev
                self.cursor = len(self.line)
            return self.line, False
        
        elif key_name == 'ARROW_DOWN':
            # Navigate history down
            next_cmd = self.history.navigate_down()
            if next_cmd is not None:
                self.line = next_cmd
                self.cursor = len(self.line)
            return self.line, False
        
        elif key_name == 'TAB':
            # Tab completion
            candidates, common_prefix = self.completer.complete(self.line, self.cursor)
            if common_prefix and len(common_prefix) > len(self.line.split()[-1] if self.line.split() else ""):
                # Auto-complete with common prefix
                # Find what to replace
                parts = self.line[:self.cursor].split()
                if parts:
                    # Replace last part
                    prefix_len = len(parts[-1])
                    self.line = self.line[:self.cursor-prefix_len] + common_prefix + self.line[self.cursor:]
                    self.cursor = self.cursor - prefix_len + len(common_prefix)
                else:
                    # Insert at beginning
                    self.line = common_prefix + self.line[self.cursor:]
                    self.cursor = len(common_prefix)
            return self.line, False
        
        elif key_name == 'CTRL_C':
            # Cancel current line
            self.line = ""
            self.cursor = 0
            self.history.reset_navigation()
            return "", False
        
        elif key_name == 'CTRL_D':
            # EOF - return special marker
            return "", True
        
        elif key_name == 'CTRL_L':
            # Clear screen (handled externally)
            return self.line, False
        
        return self.line, False
    
    def reset(self):
        """Reset line editor state."""
        self.line = ""
        self.cursor = 0
        self.history.reset_navigation()
        self.key_handler.reset()
    
    def submit(self) -> str:
        """
        Submit current line.
        
        Returns:
            The completed line
        """
        result = self.line
        self.history.add(result)
        self.reset()
        return result

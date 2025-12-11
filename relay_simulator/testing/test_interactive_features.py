"""
Unit tests for interactive terminal features.
"""

import unittest
from networking.interactive_features import (
    CommandHistory,
    TabCompleter,
    PromptFormatter,
    KeyHandler,
    InteractiveLineEditor
)


class TestCommandHistory(unittest.TestCase):
    """Test command history functionality."""
    
    def setUp(self):
        self.history = CommandHistory(max_size=5)
    
    def test_add_command(self):
        """Test adding commands to history."""
        self.history.add("command1")
        self.history.add("command2")
        
        all_commands = self.history.get_all()
        self.assertEqual(len(all_commands), 2)
        self.assertEqual(all_commands[0], "command1")
        self.assertEqual(all_commands[1], "command2")
    
    def test_ignore_empty_commands(self):
        """Test that empty commands are not added."""
        self.history.add("")
        self.history.add("   ")
        
        self.assertEqual(len(self.history.get_all()), 0)
    
    def test_ignore_duplicate_consecutive(self):
        """Test that consecutive duplicates are ignored."""
        self.history.add("command1")
        self.history.add("command1")
        self.history.add("command2")
        
        all_commands = self.history.get_all()
        self.assertEqual(len(all_commands), 2)
    
    def test_max_size_limit(self):
        """Test that history respects max size."""
        for i in range(10):
            self.history.add(f"command{i}")
        
        all_commands = self.history.get_all()
        self.assertEqual(len(all_commands), 5)
        # Should keep most recent
        self.assertEqual(all_commands[-1], "command9")
    
    def test_navigate_up(self):
        """Test navigating up through history."""
        self.history.add("cmd1")
        self.history.add("cmd2")
        self.history.add("cmd3")
        
        # Navigate up once
        result = self.history.navigate_up("")
        self.assertEqual(result, "cmd3")
        
        # Navigate up again
        result = self.history.navigate_up("")
        self.assertEqual(result, "cmd2")
        
        # Navigate up again
        result = self.history.navigate_up("")
        self.assertEqual(result, "cmd1")
        
        # Try to navigate past beginning
        result = self.history.navigate_up("")
        self.assertIsNone(result)
    
    def test_navigate_down(self):
        """Test navigating down through history."""
        self.history.add("cmd1")
        self.history.add("cmd2")
        
        # Navigate up
        self.history.navigate_up("")
        self.history.navigate_up("")
        
        # Navigate down
        result = self.history.navigate_down()
        self.assertEqual(result, "cmd2")
        
        # Navigate down to current
        result = self.history.navigate_down()
        self.assertEqual(result, "")  # Returns temp command
    
    def test_save_current_input(self):
        """Test that current input is saved when navigating."""
        self.history.add("cmd1")
        
        # Start typing new command
        current = "partial command"
        
        # Navigate up
        self.history.navigate_up(current)
        
        # Navigate back down to current
        result = self.history.navigate_down()
        
        # Should get back the partial command
        self.assertEqual(result, current)
    
    def test_search(self):
        """Test history search."""
        self.history.add("list components")
        self.history.add("show SW1")
        self.history.add("list vnets")
        
        results = self.history.search("list")
        self.assertEqual(len(results), 2)
        self.assertIn("list components", results)
        self.assertIn("list vnets", results)
    
    def test_clear(self):
        """Test clearing history."""
        self.history.add("cmd1")
        self.history.add("cmd2")
        
        self.history.clear()
        
        self.assertEqual(len(self.history.get_all()), 0)
        self.assertEqual(self.history.current_index, -1)
    
    def test_reset_navigation(self):
        """Test resetting navigation state."""
        self.history.add("cmd1")
        self.history.navigate_up("")
        
        self.history.reset_navigation()
        
        self.assertEqual(self.history.current_index, -1)
        self.assertEqual(self.history.temp_command, "")


class TestTabCompleter(unittest.TestCase):
    """Test tab completion functionality."""
    
    def setUp(self):
        self.completer = TabCompleter()
        self.completer.set_commands(['help', 'list', 'load', 'show', 'start'])
    
    def test_complete_command_prefix(self):
        """Test completing command prefix."""
        candidates, prefix = self.completer.complete("li")
        
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0], "list")
        self.assertEqual(prefix, "list")
    
    def test_complete_multiple_candidates(self):
        """Test completion with multiple candidates."""
        candidates, prefix = self.completer.complete("s")
        
        self.assertEqual(len(candidates), 2)
        self.assertIn("show", candidates)
        self.assertIn("start", candidates)
        self.assertEqual(prefix, "s")  # Common prefix
    
    def test_complete_full_command(self):
        """Test completing when command is already complete."""
        candidates, prefix = self.completer.complete("list")
        
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0], "list")
    
    def test_complete_no_match(self):
        """Test completion with no matches."""
        candidates, prefix = self.completer.complete("xyz")
        
        self.assertEqual(len(candidates), 0)
        self.assertEqual(prefix, "")
    
    def test_complete_argument_with_provider(self):
        """Test argument completion with custom provider."""
        def id_provider(text, arg_index):
            ids = ['SW1', 'SW2', 'LED1']
            return [id for id in ids if id.startswith(text.upper())]
        
        self.completer.register_provider('show', id_provider)
        
        candidates, prefix = self.completer.complete("show SW")
        
        self.assertEqual(len(candidates), 2)
        self.assertIn('SW1', candidates)
        self.assertIn('SW2', candidates)
    
    def test_complete_argument_no_provider(self):
        """Test argument completion without provider."""
        candidates, prefix = self.completer.complete("list --ver")
        
        # No provider registered - should return empty
        self.assertEqual(len(candidates), 0)
    
    def test_common_prefix_multiple(self):
        """Test finding common prefix."""
        # Set commands with common prefix
        self.completer.set_commands(['start', 'stop', 'status', 'stats'])
        
        candidates, prefix = self.completer.complete("st")
        
        self.assertEqual(len(candidates), 4)
        self.assertEqual(prefix, "st")  # All start with 'st'
    
    def test_case_insensitive(self):
        """Test case-insensitive completion."""
        candidates, prefix = self.completer.complete("HELP")
        
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0], "help")


class TestPromptFormatter(unittest.TestCase):
    """Test prompt formatting."""
    
    def test_simple_prompt(self):
        """Test simple static prompt."""
        formatter = PromptFormatter("relay> ")
        
        prompt = formatter.format()
        self.assertEqual(prompt, "relay> ")
    
    def test_prompt_with_placeholders(self):
        """Test prompt with context placeholders."""
        formatter = PromptFormatter("[{status}] relay> ")
        formatter.set_context({'status': 'RUNNING'})
        
        prompt = formatter.format()
        self.assertEqual(prompt, "[RUNNING] relay> ")
    
    def test_multiple_placeholders(self):
        """Test prompt with multiple placeholders."""
        formatter = PromptFormatter("{doc}:{sim}> ")
        formatter.set_context({
            'doc': 'test.rsim',
            'sim': 'RUNNING'
        })
        
        prompt = formatter.format()
        self.assertEqual(prompt, "test.rsim:RUNNING> ")
    
    def test_missing_placeholder(self):
        """Test prompt with undefined placeholder."""
        formatter = PromptFormatter("[{status}] relay> ")
        # Don't set context
        
        prompt = formatter.format()
        # Placeholder remains unchanged
        self.assertEqual(prompt, "[{status}] relay> ")


class TestKeyHandler(unittest.TestCase):
    """Test special key handling."""
    
    def setUp(self):
        self.handler = KeyHandler()
    
    def test_regular_character(self):
        """Test processing regular character."""
        result = self.handler.process('a')
        self.assertEqual(result, 'CHAR')
    
    def test_backspace(self):
        """Test backspace key."""
        result = self.handler.process('\x7f')
        self.assertEqual(result, 'BACKSPACE')
    
    def test_ctrl_c(self):
        """Test Ctrl+C."""
        result = self.handler.process('\x03')
        self.assertEqual(result, 'CTRL_C')
    
    def test_ctrl_d(self):
        """Test Ctrl+D."""
        result = self.handler.process('\x04')
        self.assertEqual(result, 'CTRL_D')
    
    def test_tab(self):
        """Test Tab key."""
        result = self.handler.process('\t')
        self.assertEqual(result, 'TAB')
    
    def test_arrow_up_sequence(self):
        """Test up arrow escape sequence."""
        # Arrow up is ESC[A
        result1 = self.handler.process('\x1b')
        self.assertIsNone(result1)  # Incomplete
        
        result2 = self.handler.process('[')
        self.assertIsNone(result2)  # Incomplete
        
        result3 = self.handler.process('A')
        self.assertEqual(result3, 'ARROW_UP')  # Complete
    
    def test_arrow_down_sequence(self):
        """Test down arrow escape sequence."""
        self.handler.process('\x1b')
        self.handler.process('[')
        result = self.handler.process('B')
        
        self.assertEqual(result, 'ARROW_DOWN')
    
    def test_arrow_left_sequence(self):
        """Test left arrow escape sequence."""
        self.handler.process('\x1b')
        self.handler.process('[')
        result = self.handler.process('D')
        
        self.assertEqual(result, 'ARROW_LEFT')
    
    def test_arrow_right_sequence(self):
        """Test right arrow escape sequence."""
        self.handler.process('\x1b')
        self.handler.process('[')
        result = self.handler.process('C')
        
        self.assertEqual(result, 'ARROW_RIGHT')
    
    def test_reset(self):
        """Test resetting escape sequence state."""
        self.handler.process('\x1b')
        self.handler.process('[')
        
        self.handler.reset()
        
        # Should be able to start new sequence
        result = self.handler.process('a')
        self.assertEqual(result, 'CHAR')


class TestInteractiveLineEditor(unittest.TestCase):
    """Test interactive line editor."""
    
    def setUp(self):
        self.history = CommandHistory()
        self.completer = TabCompleter()
        self.completer.set_commands(['help', 'list', 'load'])
        self.editor = InteractiveLineEditor(self.history, self.completer)
    
    def test_insert_character(self):
        """Test inserting characters."""
        line, complete = self.editor.handle_key('CHAR', 't')
        self.assertEqual(line, 't')
        self.assertFalse(complete)
        
        line, complete = self.editor.handle_key('CHAR', 'e')
        self.assertEqual(line, 'te')
    
    def test_backspace(self):
        """Test backspace."""
        self.editor.handle_key('CHAR', 't')
        self.editor.handle_key('CHAR', 'e')
        self.editor.handle_key('CHAR', 's')
        
        line, complete = self.editor.handle_key('BACKSPACE')
        self.assertEqual(line, 'te')
    
    def test_arrow_left_right(self):
        """Test cursor movement."""
        self.editor.handle_key('CHAR', 'a')
        self.editor.handle_key('CHAR', 'b')
        
        # Move left
        self.editor.handle_key('ARROW_LEFT')
        
        # Insert character
        line, _ = self.editor.handle_key('CHAR', 'X')
        self.assertEqual(line, 'aXb')
    
    def test_home_end(self):
        """Test Home and End keys."""
        self.editor.handle_key('CHAR', 'a')
        self.editor.handle_key('CHAR', 'b')
        self.editor.handle_key('CHAR', 'c')
        
        # Home
        self.editor.handle_key('HOME')
        self.assertEqual(self.editor.cursor, 0)
        
        # End
        self.editor.handle_key('END')
        self.assertEqual(self.editor.cursor, 3)
    
    def test_history_navigation(self):
        """Test history navigation."""
        self.history.add("cmd1")
        self.history.add("cmd2")
        
        # Up arrow
        line, _ = self.editor.handle_key('ARROW_UP')
        self.assertEqual(line, 'cmd2')
        
        # Up again
        line, _ = self.editor.handle_key('ARROW_UP')
        self.assertEqual(line, 'cmd1')
        
        # Down
        line, _ = self.editor.handle_key('ARROW_DOWN')
        self.assertEqual(line, 'cmd2')
    
    def test_ctrl_c_cancel(self):
        """Test Ctrl+C cancels current line."""
        self.editor.handle_key('CHAR', 't')
        self.editor.handle_key('CHAR', 'e')
        
        line, complete = self.editor.handle_key('CTRL_C')
        
        self.assertEqual(line, "")
        self.assertFalse(complete)
        self.assertEqual(self.editor.line, "")
    
    def test_ctrl_d_eof(self):
        """Test Ctrl+D signals EOF."""
        line, complete = self.editor.handle_key('CTRL_D')
        
        self.assertTrue(complete)
    
    def test_submit(self):
        """Test submitting line."""
        self.editor.handle_key('CHAR', 'c')
        self.editor.handle_key('CHAR', 'm')
        self.editor.handle_key('CHAR', 'd')
        
        result = self.editor.submit()
        
        self.assertEqual(result, 'cmd')
        # Should be added to history
        self.assertIn('cmd', self.history.get_all())
        # Editor should be reset
        self.assertEqual(self.editor.line, "")
        self.assertEqual(self.editor.cursor, 0)
    
    def test_reset(self):
        """Test resetting editor."""
        self.editor.handle_key('CHAR', 't')
        self.editor.handle_key('CHAR', 'e')
        
        self.editor.reset()
        
        self.assertEqual(self.editor.line, "")
        self.assertEqual(self.editor.cursor, 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for interactive features."""
    
    def test_complete_workflow(self):
        """Test complete interactive workflow."""
        history = CommandHistory()
        completer = TabCompleter()
        completer.set_commands(['help', 'list', 'show'])
        editor = InteractiveLineEditor(history, completer)
        
        # Type a command
        editor.handle_key('CHAR', 'l')
        editor.handle_key('CHAR', 'i')
        editor.handle_key('CHAR', 's')
        editor.handle_key('CHAR', 't')
        
        # Submit
        cmd = editor.submit()
        self.assertEqual(cmd, 'list')
        
        # Start new command
        editor.handle_key('CHAR', 'h')
        
        # Navigate up to previous
        line, _ = editor.handle_key('ARROW_UP')
        self.assertEqual(line, 'list')
        
        # Navigate down
        line, _ = editor.handle_key('ARROW_DOWN')
        self.assertEqual(line, 'h')  # Back to current input
    
    def test_history_with_editing(self):
        """Test history navigation with line editing."""
        history = CommandHistory()
        history.add("original command")
        
        editor = InteractiveLineEditor(history)
        
        # Navigate to history
        editor.handle_key('ARROW_UP')
        
        # Edit the line
        editor.handle_key('END')
        editor.handle_key('CHAR', '!')
        
        line = editor.line
        self.assertEqual(line, 'original command!')
        
        # Submit modified version
        cmd = editor.submit()
        self.assertEqual(cmd, 'original command!')
        
        # Both should be in history
        all_history = history.get_all()
        self.assertIn('original command', all_history)
        self.assertIn('original command!', all_history)


if __name__ == '__main__':
    unittest.main()

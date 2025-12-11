"""
Demo of interactive terminal features.

This is a simple demonstration - full integration with terminal server
would handle the actual character-by-character I/O.
"""

from networking.interactive_features import (
    CommandHistory,
    TabCompleter,
    PromptFormatter,
    KeyHandler,
    InteractiveLineEditor
)


def demo_command_history():
    """Demonstrate command history functionality."""
    print("=== COMMAND HISTORY DEMO ===\n")
    
    history = CommandHistory(max_size=10)
    
    # Add some commands
    history.add("list components")
    history.add("show SW1")
    history.add("toggle SW1")
    history.add("status")
    
    print("Added commands to history:")
    for cmd in history.get_all():
        print(f"  - {cmd}")
    print()
    
    # Navigate up
    print("Navigating up (like pressing ↑):")
    cmd = history.navigate_up("")
    print(f"  Current: {cmd}")
    cmd = history.navigate_up("")
    print(f"  Current: {cmd}")
    cmd = history.navigate_up("")
    print(f"  Current: {cmd}")
    print()
    
    # Navigate down
    print("Navigating down (like pressing ↓):")
    cmd = history.navigate_down()
    print(f"  Current: {cmd}")
    cmd = history.navigate_down()
    print(f"  Current: {cmd}")
    print()
    
    # Search
    print("Searching for 'show':")
    results = history.search("show")
    for result in results:
        print(f"  - {result}")
    print()


def demo_tab_completion():
    """Demonstrate tab completion."""
    print("=== TAB COMPLETION DEMO ===\n")
    
    completer = TabCompleter()
    completer.set_commands(['help', 'list', 'load', 'show', 'start', 'stop', 'status', 'stats'])
    
    # Complete command prefix
    print("Completing 'st':")
    candidates, prefix = completer.complete("st")
    print(f"  Candidates: {candidates}")
    print(f"  Common prefix: '{prefix}'")
    print()
    
    print("Completing 'sta':")
    candidates, prefix = completer.complete("sta")
    print(f"  Candidates: {candidates}")
    print(f"  Common prefix: '{prefix}'")
    print()
    
    # Register custom provider
    def id_provider(text, arg_index):
        ids = ['SW1', 'SW2', 'LED1', 'LED2', 'RLY1']
        return [id for id in ids if id.startswith(text.upper())]
    
    completer.register_provider('show', id_provider)
    
    print("Completing 'show SW' (with custom provider):")
    candidates, prefix = completer.complete("show SW")
    print(f"  Candidates: {candidates}")
    print(f"  Common prefix: '{prefix}'")
    print()


def demo_prompt_formatter():
    """Demonstrate dynamic prompts."""
    print("=== PROMPT FORMATTER DEMO ===\n")
    
    # Simple static prompt
    formatter = PromptFormatter("relay> ")
    print(f"Static prompt: '{formatter.format()}'")
    print()
    
    # Dynamic prompt with status
    formatter = PromptFormatter("[{status}] relay> ")
    
    formatter.set_context({'status': 'IDLE'})
    print(f"Idle: '{formatter.format()}'")
    
    formatter.set_context({'status': 'RUNNING'})
    print(f"Running: '{formatter.format()}'")
    
    formatter.set_context({'status': 'STOPPED'})
    print(f"Stopped: '{formatter.format()}'")
    print()
    
    # Complex prompt
    formatter = PromptFormatter("{doc}:{sim}> ")
    formatter.set_context({
        'doc': 'test.rsim',
        'sim': 'RUNNING'
    })
    print(f"Complex: '{formatter.format()}'")
    print()


def demo_key_handler():
    """Demonstrate special key handling."""
    print("=== KEY HANDLER DEMO ===\n")
    
    handler = KeyHandler()
    
    print("Processing regular character 'a':")
    result = handler.process('a')
    print(f"  Result: {result}")
    print()
    
    print("Processing Ctrl+C (\\x03):")
    result = handler.process('\x03')
    print(f"  Result: {result}")
    print()
    
    print("Processing Tab (\\t):")
    result = handler.process('\t')
    print(f"  Result: {result}")
    print()
    
    print("Processing arrow up sequence (ESC[A):")
    result1 = handler.process('\x1b')
    print(f"  After ESC: {result1}")
    result2 = handler.process('[')
    print(f"  After [: {result2}")
    result3 = handler.process('A')
    print(f"  After A: {result3}")
    print()


def demo_line_editor():
    """Demonstrate interactive line editor."""
    print("=== LINE EDITOR DEMO ===\n")
    
    history = CommandHistory()
    history.add("list components")
    history.add("show SW1")
    
    completer = TabCompleter()
    completer.set_commands(['help', 'list', 'load', 'show'])
    
    editor = InteractiveLineEditor(history, completer)
    
    print("Simulating typing 'help':")
    for char in "help":
        line, complete = editor.handle_key('CHAR', char)
        print(f"  Line: '{line}', Cursor: {editor.cursor}")
    print()
    
    print("Simulating backspace:")
    line, complete = editor.handle_key('BACKSPACE')
    print(f"  Line: '{line}'")
    print()
    
    print("Simulating arrow left:")
    editor.handle_key('ARROW_LEFT')
    print(f"  Cursor: {editor.cursor}")
    print()
    
    print("Inserting 'X' at cursor:")
    line, complete = editor.handle_key('CHAR', 'X')
    print(f"  Line: '{line}'")
    print()
    
    print("Navigating to history (↑):")
    line, complete = editor.handle_key('ARROW_UP')
    print(f"  Line: '{line}'")
    line, complete = editor.handle_key('ARROW_UP')
    print(f"  Line: '{line}'")
    print()


def demo_complete_workflow():
    """Demonstrate complete interactive workflow."""
    print("=== COMPLETE WORKFLOW DEMO ===\n")
    
    # Setup
    history = CommandHistory()
    completer = TabCompleter()
    completer.set_commands(['help', 'list', 'load', 'show', 'start', 'stop'])
    editor = InteractiveLineEditor(history, completer)
    prompt_formatter = PromptFormatter("[{status}] relay> ")
    
    # Simulate session
    prompt_formatter.set_context({'status': 'IDLE'})
    
    print(f"{prompt_formatter.format()}", end="")
    print("(user types 'list')")
    for char in "list":
        editor.handle_key('CHAR', char)
    cmd = editor.submit()
    print(f"  → Executed: {cmd}")
    print()
    
    # Update status
    prompt_formatter.set_context({'status': 'RUNNING'})
    
    print(f"{prompt_formatter.format()}", end="")
    print("(user types 'sta' then TAB)")
    for char in "sta":
        editor.handle_key('CHAR', char)
    candidates, prefix = completer.complete(editor.line)
    print(f"  → Completions: {candidates}")
    print()
    
    print(f"{prompt_formatter.format()}", end="")
    print("(user presses ↑ for history)")
    line, _ = editor.handle_key('ARROW_UP')
    print(f"  → Recalled: {line}")
    print()
    
    print(f"{prompt_formatter.format()}", end="")
    print("(user presses Ctrl+C to cancel)")
    editor.handle_key('CTRL_C')
    print(f"  → Line cleared")
    print()
    
    print("History now contains:")
    for cmd in history.get_all():
        print(f"  - {cmd}")
    print()


if __name__ == '__main__':
    demo_command_history()
    print("\n" + "="*60 + "\n")
    
    demo_tab_completion()
    print("\n" + "="*60 + "\n")
    
    demo_prompt_formatter()
    print("\n" + "="*60 + "\n")
    
    demo_key_handler()
    print("\n" + "="*60 + "\n")
    
    demo_line_editor()
    print("\n" + "="*60 + "\n")
    
    demo_complete_workflow()

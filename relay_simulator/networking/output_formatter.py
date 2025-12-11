"""
Output formatting utilities for terminal interface.

Provides table formatting, list formatting, and text alignment
for displaying simulation data in the terminal.
"""

from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class Alignment(Enum):
    """Text alignment options."""
    LEFT = 'left'
    RIGHT = 'right'
    CENTER = 'center'


class ANSIColor:
    """ANSI color codes for terminal output."""
    # Reset
    RESET = '\033[0m'
    
    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright text colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Text styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    @staticmethod
    def colorize(text: str, color: str) -> str:
        """Wrap text in color codes."""
        return f"{color}{text}{ANSIColor.RESET}"


class BoxChars:
    """Box drawing characters for tables."""
    # Simple ASCII box
    ASCII_TOP_LEFT = '+'
    ASCII_TOP_RIGHT = '+'
    ASCII_BOTTOM_LEFT = '+'
    ASCII_BOTTOM_RIGHT = '+'
    ASCII_HORIZONTAL = '-'
    ASCII_VERTICAL = '|'
    ASCII_T_DOWN = '+'
    ASCII_T_UP = '+'
    ASCII_T_RIGHT = '+'
    ASCII_T_LEFT = '+'
    ASCII_CROSS = '+'
    
    # Unicode box drawing (optional - cleaner look)
    UNICODE_TOP_LEFT = '┌'
    UNICODE_TOP_RIGHT = '┐'
    UNICODE_BOTTOM_LEFT = '└'
    UNICODE_BOTTOM_RIGHT = '┘'
    UNICODE_HORIZONTAL = '─'
    UNICODE_VERTICAL = '│'
    UNICODE_T_DOWN = '┬'
    UNICODE_T_UP = '┴'
    UNICODE_T_RIGHT = '├'
    UNICODE_T_LEFT = '┤'
    UNICODE_CROSS = '┼'


class OutputFormatter:
    """
    Format text output for terminal display.
    
    Supports:
    - Table formatting with column alignment
    - List formatting
    - Text truncation
    - ANSI colors (optional)
    - Box drawing characters
    """
    
    def __init__(self, 
                 terminal_width: int = 80,
                 use_colors: bool = True,
                 use_unicode: bool = False):
        """
        Initialize formatter.
        
        Args:
            terminal_width: Maximum width for output (default: 80)
            use_colors: Enable ANSI color codes (default: True)
            use_unicode: Use Unicode box chars instead of ASCII (default: False)
        """
        self.terminal_width = terminal_width
        self.use_colors = use_colors
        self.use_unicode = use_unicode
        
        # Select box characters based on unicode setting
        if use_unicode:
            self.box = BoxChars
            self.h = BoxChars.UNICODE_HORIZONTAL
            self.v = BoxChars.UNICODE_VERTICAL
            self.tl = BoxChars.UNICODE_TOP_LEFT
            self.tr = BoxChars.UNICODE_TOP_RIGHT
            self.bl = BoxChars.UNICODE_BOTTOM_LEFT
            self.br = BoxChars.UNICODE_BOTTOM_RIGHT
            self.td = BoxChars.UNICODE_T_DOWN
            self.tu = BoxChars.UNICODE_T_UP
            self.tr_char = BoxChars.UNICODE_T_RIGHT
            self.tl_char = BoxChars.UNICODE_T_LEFT
            self.cross = BoxChars.UNICODE_CROSS
        else:
            self.box = BoxChars
            self.h = BoxChars.ASCII_HORIZONTAL
            self.v = BoxChars.ASCII_VERTICAL
            self.tl = BoxChars.ASCII_TOP_LEFT
            self.tr = BoxChars.ASCII_TOP_RIGHT
            self.bl = BoxChars.ASCII_BOTTOM_LEFT
            self.br = BoxChars.ASCII_BOTTOM_RIGHT
            self.td = BoxChars.ASCII_T_DOWN
            self.tu = BoxChars.ASCII_T_UP
            self.tr_char = BoxChars.ASCII_T_RIGHT
            self.tl_char = BoxChars.ASCII_T_LEFT
            self.cross = BoxChars.ASCII_CROSS
    
    def colorize(self, text: str, color: str) -> str:
        """
        Apply color to text if colors enabled.
        
        Args:
            text: Text to colorize
            color: ANSI color code
            
        Returns:
            Colorized text or plain text if colors disabled
        """
        if self.use_colors:
            return ANSIColor.colorize(text, color)
        return text
    
    def truncate(self, text: str, max_width: int, suffix: str = '...') -> str:
        """
        Truncate text to maximum width.
        
        Args:
            text: Text to truncate
            max_width: Maximum width
            suffix: Suffix to add if truncated (default: '...')
            
        Returns:
            Truncated text
        """
        text = str(text)
        if len(text) <= max_width:
            return text
        
        if max_width <= len(suffix):
            return suffix[:max_width]
        
        return text[:max_width - len(suffix)] + suffix
    
    def align(self, text: str, width: int, alignment: Alignment = Alignment.LEFT) -> str:
        """
        Align text within a field of given width.
        
        Args:
            text: Text to align
            width: Field width
            alignment: Alignment option (LEFT, RIGHT, CENTER)
            
        Returns:
            Aligned text
        """
        text = str(text)
        if len(text) >= width:
            return text[:width]
        
        padding = width - len(text)
        
        if alignment == Alignment.LEFT:
            return text + ' ' * padding
        elif alignment == Alignment.RIGHT:
            return ' ' * padding + text
        elif alignment == Alignment.CENTER:
            left_pad = padding // 2
            right_pad = padding - left_pad
            return ' ' * left_pad + text + ' ' * right_pad
        
        return text
    
    def format_table(self,
                     headers: List[str],
                     rows: List[List[Any]],
                     alignments: Optional[List[Alignment]] = None,
                     column_widths: Optional[List[int]] = None) -> str:
        """
        Format data as a table.
        
        Args:
            headers: Column headers
            rows: Data rows (each row is a list of values)
            alignments: Column alignments (default: all LEFT)
            column_widths: Fixed column widths (default: auto-calculate)
            
        Returns:
            Formatted table as string
        """
        if not headers:
            return ""
        
        num_cols = len(headers)
        
        # Default alignments
        if alignments is None:
            alignments = [Alignment.LEFT] * num_cols
        
        # Calculate column widths if not provided
        if column_widths is None:
            column_widths = []
            for i in range(num_cols):
                # Start with header width
                max_width = len(headers[i])
                
                # Check all row values
                for row in rows:
                    if i < len(row):
                        max_width = max(max_width, len(str(row[i])))
                
                column_widths.append(max_width)
        
        # Ensure we don't exceed terminal width
        total_width = sum(column_widths) + (num_cols - 1) * 3 + 4  # 3 chars per separator, 4 for edges
        if total_width > self.terminal_width:
            # Proportionally reduce column widths
            scale = (self.terminal_width - (num_cols - 1) * 3 - 4) / sum(column_widths)
            column_widths = [max(3, int(w * scale)) for w in column_widths]
        
        result = []
        
        # Top border
        border_parts = [self.tl]
        for i, width in enumerate(column_widths):
            border_parts.append(self.h * (width + 2))
            if i < num_cols - 1:
                border_parts.append(self.td)
        border_parts.append(self.tr)
        result.append(''.join(border_parts))
        
        # Header row
        header_parts = [self.v]
        for i, (header, width, align) in enumerate(zip(headers, column_widths, alignments)):
            header_text = self.truncate(header, width)
            header_text = self.align(header_text, width, align)
            if self.use_colors:
                header_text = self.colorize(header_text, ANSIColor.BOLD)
            header_parts.append(f" {header_text} ")
            if i < num_cols - 1:
                header_parts.append(self.v)
        header_parts.append(self.v)
        result.append(''.join(header_parts))
        
        # Header separator
        sep_parts = [self.tr_char]
        for i, width in enumerate(column_widths):
            sep_parts.append(self.h * (width + 2))
            if i < num_cols - 1:
                sep_parts.append(self.cross)
        sep_parts.append(self.tl_char)
        result.append(''.join(sep_parts))
        
        # Data rows
        for row in rows:
            row_parts = [self.v]
            for i, (width, align) in enumerate(zip(column_widths, alignments)):
                value = row[i] if i < len(row) else ""
                cell_text = self.truncate(str(value), width)
                cell_text = self.align(cell_text, width, align)
                row_parts.append(f" {cell_text} ")
                if i < num_cols - 1:
                    row_parts.append(self.v)
            row_parts.append(self.v)
            result.append(''.join(row_parts))
        
        # Bottom border
        bottom_parts = [self.bl]
        for i, width in enumerate(column_widths):
            bottom_parts.append(self.h * (width + 2))
            if i < num_cols - 1:
                bottom_parts.append(self.tu)
        bottom_parts.append(self.br)
        result.append(''.join(bottom_parts))
        
        return '\n'.join(result)
    
    def format_list(self,
                    items: List[str],
                    numbered: bool = False,
                    bullet: str = '•') -> str:
        """
        Format items as a list.
        
        Args:
            items: List items
            numbered: Use numbers instead of bullets (default: False)
            bullet: Bullet character (default: '•')
            
        Returns:
            Formatted list as string
        """
        if not items:
            return ""
        
        result = []
        for i, item in enumerate(items):
            if numbered:
                prefix = f"{i + 1}. "
            else:
                prefix = f"{bullet} "
            
            result.append(f"{prefix}{item}")
        
        return '\n'.join(result)
    
    def format_key_value(self,
                         data: Dict[str, Any],
                         indent: int = 0,
                         separator: str = ': ') -> str:
        """
        Format dictionary as key-value pairs.
        
        Args:
            data: Dictionary to format
            indent: Indentation level (default: 0)
            separator: Separator between key and value (default: ': ')
            
        Returns:
            Formatted key-value pairs as string
        """
        if not data:
            return ""
        
        # Calculate max key width for alignment
        max_key_width = max(len(str(key)) for key in data.keys())
        
        result = []
        indent_str = ' ' * indent
        
        for key, value in data.items():
            key_str = self.align(str(key), max_key_width, Alignment.LEFT)
            if self.use_colors:
                key_str = self.colorize(key_str, ANSIColor.CYAN)
            result.append(f"{indent_str}{key_str}{separator}{value}")
        
        return '\n'.join(result)
    
    def format_section(self,
                       title: str,
                       content: str,
                       title_color: Optional[str] = None) -> str:
        """
        Format a section with title and content.
        
        Args:
            title: Section title
            content: Section content
            title_color: Color for title (default: BOLD)
            
        Returns:
            Formatted section as string
        """
        if title_color is None:
            title_color = ANSIColor.BOLD
        
        # Format title
        title_line = f"=== {title} ==="
        if self.use_colors:
            title_line = self.colorize(title_line, title_color)
        
        return f"{title_line}\n{content}"
    
    def word_wrap(self, text: str, width: Optional[int] = None) -> str:
        """
        Wrap text to fit within width.
        
        Args:
            text: Text to wrap
            width: Maximum width (default: terminal_width)
            
        Returns:
            Wrapped text
        """
        if width is None:
            width = self.terminal_width
        
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            
            # Add space if not first word on line
            space_length = 1 if current_line else 0
            
            if current_length + space_length + word_length <= width:
                current_line.append(word)
                current_length += space_length + word_length
            else:
                # Start new line
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length
        
        # Add last line
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)


# Convenience functions for common formatting patterns

def format_component_table(formatter: OutputFormatter,
                           components: List[Dict[str, Any]]) -> str:
    """
    Format component list as a table.
    
    Args:
        formatter: OutputFormatter instance
        components: List of component dicts with keys: id, type, page, state
        
    Returns:
        Formatted table
    """
    headers = ['ID', 'Type', 'Page', 'State']
    rows = []
    
    for comp in components:
        rows.append([
            comp.get('id', ''),
            comp.get('type', ''),
            comp.get('page', ''),
            comp.get('state', '')
        ])
    
    alignments = [Alignment.LEFT, Alignment.LEFT, Alignment.LEFT, Alignment.CENTER]
    return formatter.format_table(headers, rows, alignments)


def format_vnet_table(formatter: OutputFormatter,
                      vnets: List[Dict[str, Any]]) -> str:
    """
    Format VNET list as a table.
    
    Args:
        formatter: OutputFormatter instance
        vnets: List of VNET dicts with keys: id, state, tabs, dirty
        
    Returns:
        Formatted table
    """
    headers = ['VNET ID', 'State', 'Tabs', 'Dirty']
    rows = []
    
    for vnet in vnets:
        rows.append([
            vnet.get('id', ''),
            vnet.get('state', ''),
            vnet.get('tabs', 0),
            vnet.get('dirty', False)
        ])
    
    alignments = [Alignment.LEFT, Alignment.CENTER, Alignment.RIGHT, Alignment.CENTER]
    return formatter.format_table(headers, rows, alignments)

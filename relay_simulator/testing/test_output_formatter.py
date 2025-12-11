"""
Unit tests for output formatting utilities.
"""

import unittest
from networking.output_formatter import (
    OutputFormatter,
    Alignment,
    ANSIColor,
    BoxChars,
    format_component_table,
    format_vnet_table
)


class TestAlignment(unittest.TestCase):
    """Test text alignment functionality."""
    
    def setUp(self):
        self.formatter = OutputFormatter(use_colors=False, use_unicode=False)
    
    def test_align_left(self):
        """Test left alignment."""
        result = self.formatter.align("test", 10, Alignment.LEFT)
        self.assertEqual(result, "test      ")
        self.assertEqual(len(result), 10)
    
    def test_align_right(self):
        """Test right alignment."""
        result = self.formatter.align("test", 10, Alignment.RIGHT)
        self.assertEqual(result, "      test")
        self.assertEqual(len(result), 10)
    
    def test_align_center(self):
        """Test center alignment."""
        result = self.formatter.align("test", 10, Alignment.CENTER)
        self.assertEqual(result, "   test   ")
        self.assertEqual(len(result), 10)
    
    def test_align_center_odd(self):
        """Test center alignment with odd padding."""
        result = self.formatter.align("test", 9, Alignment.CENTER)
        self.assertEqual(len(result), 9)
        # Should have 2 spaces on left, 3 on right (or vice versa)
        self.assertTrue(result.strip() == "test")
    
    def test_align_exact_width(self):
        """Test alignment when text exactly fits."""
        result = self.formatter.align("test", 4, Alignment.LEFT)
        self.assertEqual(result, "test")
    
    def test_align_too_long(self):
        """Test alignment when text is too long."""
        result = self.formatter.align("testing", 4, Alignment.LEFT)
        self.assertEqual(result, "test")


class TestTruncation(unittest.TestCase):
    """Test text truncation functionality."""
    
    def setUp(self):
        self.formatter = OutputFormatter(use_colors=False)
    
    def test_truncate_long_text(self):
        """Test truncating text that exceeds max width."""
        result = self.formatter.truncate("this is a long string", 10)
        self.assertEqual(result, "this is...")
        self.assertEqual(len(result), 10)
    
    def test_truncate_short_text(self):
        """Test truncating text shorter than max width."""
        result = self.formatter.truncate("short", 10)
        self.assertEqual(result, "short")
    
    def test_truncate_exact_width(self):
        """Test truncating text at exact max width."""
        result = self.formatter.truncate("exactly10!", 10)
        self.assertEqual(result, "exactly10!")
    
    def test_truncate_custom_suffix(self):
        """Test truncation with custom suffix."""
        result = self.formatter.truncate("this is a long string", 10, suffix=">>")
        self.assertEqual(result, "this is >>")
        self.assertEqual(len(result), 10)
    
    def test_truncate_very_short(self):
        """Test truncation with width shorter than suffix."""
        result = self.formatter.truncate("testing", 2)
        self.assertEqual(result, "..")
        self.assertEqual(len(result), 2)


class TestColorization(unittest.TestCase):
    """Test ANSI color support."""
    
    def test_colorize_with_colors_enabled(self):
        """Test colorization when colors enabled."""
        formatter = OutputFormatter(use_colors=True)
        result = formatter.colorize("test", ANSIColor.RED)
        self.assertIn(ANSIColor.RED, result)
        self.assertIn(ANSIColor.RESET, result)
        self.assertIn("test", result)
    
    def test_colorize_with_colors_disabled(self):
        """Test colorization when colors disabled."""
        formatter = OutputFormatter(use_colors=False)
        result = formatter.colorize("test", ANSIColor.RED)
        self.assertEqual(result, "test")
        self.assertNotIn(ANSIColor.RED, result)
    
    def test_ansi_color_static_method(self):
        """Test ANSIColor.colorize static method."""
        result = ANSIColor.colorize("test", ANSIColor.GREEN)
        self.assertIn(ANSIColor.GREEN, result)
        self.assertIn(ANSIColor.RESET, result)
        self.assertIn("test", result)


class TestTableFormatting(unittest.TestCase):
    """Test table formatting functionality."""
    
    def setUp(self):
        self.formatter = OutputFormatter(use_colors=False, use_unicode=False)
    
    def test_simple_table(self):
        """Test basic table formatting."""
        headers = ['Name', 'Age', 'City']
        rows = [
            ['Alice', '30', 'NYC'],
            ['Bob', '25', 'LA']
        ]
        
        result = self.formatter.format_table(headers, rows)
        
        # Check structure
        self.assertIn('Name', result)
        self.assertIn('Alice', result)
        self.assertIn('Bob', result)
        
        # Check borders present
        self.assertIn('+', result)
        self.assertIn('-', result)
        self.assertIn('|', result)
        
        # Should have 5 lines: top, header, separator, 2 data rows, bottom
        lines = result.split('\n')
        self.assertEqual(len(lines), 6)
    
    def test_table_with_alignments(self):
        """Test table with custom alignments."""
        headers = ['ID', 'Name', 'Count']
        rows = [
            ['1', 'Item', '100'],
            ['2', 'Thing', '50']
        ]
        alignments = [Alignment.LEFT, Alignment.LEFT, Alignment.RIGHT]
        
        result = self.formatter.format_table(headers, rows, alignments)
        
        # Check that numbers are right-aligned (trailing spaces before |)
        lines = result.split('\n')
        # Find data row
        for line in lines:
            if 'Item' in line:
                # Count should be right-aligned
                self.assertTrue('100 ' in line or ' 100 |' in line)
    
    def test_table_with_fixed_widths(self):
        """Test table with fixed column widths."""
        headers = ['A', 'B']
        rows = [['1', '2']]
        widths = [10, 10]
        
        result = self.formatter.format_table(headers, rows, column_widths=widths)
        
        # Each column should be 10 chars wide (plus padding/borders)
        lines = result.split('\n')
        # Header line should have appropriate width
        self.assertTrue(len(lines[1]) > 20)  # At least 2*10 + borders
    
    def test_empty_table(self):
        """Test table with no headers."""
        result = self.formatter.format_table([], [])
        self.assertEqual(result, "")
    
    def test_table_unicode_borders(self):
        """Test table with Unicode box characters."""
        formatter = OutputFormatter(use_colors=False, use_unicode=True)
        headers = ['A', 'B']
        rows = [['1', '2']]
        
        result = formatter.format_table(headers, rows)
        
        # Should contain Unicode box characters
        self.assertIn('─', result)
        self.assertIn('│', result)
        self.assertIn('┌', result)
        self.assertIn('└', result)
    
    def test_table_truncates_to_terminal_width(self):
        """Test that tables truncate to fit terminal width."""
        formatter = OutputFormatter(terminal_width=40, use_colors=False)
        headers = ['Column1', 'Column2', 'Column3', 'Column4']
        rows = [['VeryLongValue1', 'VeryLongValue2', 'VeryLongValue3', 'VeryLongValue4']]
        
        result = formatter.format_table(headers, rows)
        lines = result.split('\n')
        
        # No line should exceed terminal width
        for line in lines:
            self.assertLessEqual(len(line), formatter.terminal_width)


class TestListFormatting(unittest.TestCase):
    """Test list formatting functionality."""
    
    def setUp(self):
        self.formatter = OutputFormatter(use_colors=False)
    
    def test_bulleted_list(self):
        """Test bulleted list formatting."""
        items = ['Item 1', 'Item 2', 'Item 3']
        result = self.formatter.format_list(items)
        
        self.assertIn('•', result)
        self.assertIn('Item 1', result)
        self.assertIn('Item 2', result)
        self.assertIn('Item 3', result)
        
        lines = result.split('\n')
        self.assertEqual(len(lines), 3)
    
    def test_numbered_list(self):
        """Test numbered list formatting."""
        items = ['First', 'Second', 'Third']
        result = self.formatter.format_list(items, numbered=True)
        
        self.assertIn('1. First', result)
        self.assertIn('2. Second', result)
        self.assertIn('3. Third', result)
    
    def test_custom_bullet(self):
        """Test list with custom bullet character."""
        items = ['A', 'B']
        result = self.formatter.format_list(items, bullet='-')
        
        self.assertIn('- A', result)
        self.assertIn('- B', result)
    
    def test_empty_list(self):
        """Test formatting empty list."""
        result = self.formatter.format_list([])
        self.assertEqual(result, "")


class TestKeyValueFormatting(unittest.TestCase):
    """Test key-value pair formatting."""
    
    def setUp(self):
        self.formatter = OutputFormatter(use_colors=False)
    
    def test_simple_key_value(self):
        """Test basic key-value formatting."""
        data = {'Name': 'Test', 'Age': 30, 'City': 'NYC'}
        result = self.formatter.format_key_value(data)
        
        self.assertIn('Name', result)
        self.assertIn('Test', result)
        self.assertIn('Age', result)
        self.assertIn('30', result)
        
        lines = result.split('\n')
        self.assertEqual(len(lines), 3)
    
    def test_key_value_with_indent(self):
        """Test key-value with indentation."""
        data = {'Key': 'Value'}
        result = self.formatter.format_key_value(data, indent=4)
        
        self.assertTrue(result.startswith('    '))
    
    def test_key_value_custom_separator(self):
        """Test key-value with custom separator."""
        data = {'A': 'B'}
        result = self.formatter.format_key_value(data, separator=' = ')
        
        self.assertIn(' = ', result)
    
    def test_key_value_alignment(self):
        """Test that keys are aligned."""
        data = {'Short': '1', 'VeryLongKey': '2'}
        result = self.formatter.format_key_value(data)
        
        lines = result.split('\n')
        # Both lines should have ':' at same position
        colon_positions = [line.index(':') for line in lines]
        self.assertEqual(colon_positions[0], colon_positions[1])
    
    def test_empty_dict(self):
        """Test formatting empty dictionary."""
        result = self.formatter.format_key_value({})
        self.assertEqual(result, "")


class TestSectionFormatting(unittest.TestCase):
    """Test section formatting."""
    
    def setUp(self):
        self.formatter = OutputFormatter(use_colors=False)
    
    def test_simple_section(self):
        """Test basic section formatting."""
        result = self.formatter.format_section("Title", "Content here")
        
        self.assertIn("=== Title ===", result)
        self.assertIn("Content here", result)
        
        lines = result.split('\n')
        self.assertEqual(len(lines), 2)
    
    def test_section_with_color(self):
        """Test section with colored title."""
        formatter = OutputFormatter(use_colors=True)
        result = formatter.format_section("Title", "Content", ANSIColor.GREEN)
        
        self.assertIn(ANSIColor.GREEN, result)
        self.assertIn("Title", result)


class TestWordWrap(unittest.TestCase):
    """Test word wrapping functionality."""
    
    def setUp(self):
        self.formatter = OutputFormatter(terminal_width=20, use_colors=False)
    
    def test_wrap_long_text(self):
        """Test wrapping text that exceeds width."""
        text = "This is a very long sentence that should be wrapped"
        result = self.formatter.word_wrap(text)
        
        lines = result.split('\n')
        self.assertGreater(len(lines), 1)
        
        # Each line should be <= terminal width
        for line in lines:
            self.assertLessEqual(len(line), self.formatter.terminal_width)
    
    def test_wrap_short_text(self):
        """Test wrapping text within width."""
        text = "Short text"
        result = self.formatter.word_wrap(text)
        
        self.assertEqual(result, text)
    
    def test_wrap_custom_width(self):
        """Test wrapping with custom width."""
        text = "This should wrap at a specific width"
        result = self.formatter.word_wrap(text, width=15)
        
        lines = result.split('\n')
        for line in lines:
            self.assertLessEqual(len(line), 15)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience formatting functions."""
    
    def setUp(self):
        self.formatter = OutputFormatter(use_colors=False, use_unicode=False)
    
    def test_format_component_table(self):
        """Test component table formatting."""
        components = [
            {'id': 'SW1', 'type': 'Switch', 'page': 'Page1', 'state': 'ON'},
            {'id': 'LED1', 'type': 'Indicator', 'page': 'Page1', 'state': 'OFF'}
        ]
        
        result = format_component_table(self.formatter, components)
        
        self.assertIn('SW1', result)
        self.assertIn('LED1', result)
        self.assertIn('Switch', result)
        self.assertIn('Indicator', result)
    
    def test_format_vnet_table(self):
        """Test VNET table formatting."""
        vnets = [
            {'id': 'VNET1', 'state': 'HIGH', 'tabs': 5, 'dirty': False},
            {'id': 'VNET2', 'state': 'FLOAT', 'tabs': 3, 'dirty': True}
        ]
        
        result = format_vnet_table(self.formatter, vnets)
        
        self.assertIn('VNET1', result)
        self.assertIn('VNET2', result)
        self.assertIn('HIGH', result)
        self.assertIn('FLOAT', result)


class TestIntegration(unittest.TestCase):
    """Integration tests for formatter."""
    
    def test_complete_output(self):
        """Test combining multiple formatting features."""
        formatter = OutputFormatter(use_colors=False, use_unicode=False)
        
        # Create a complex output
        title = formatter.format_section("Component Status", "")
        
        table_data = [
            ['SW1', 'Switch', 'ON'],
            ['LED1', 'Indicator', 'OFF']
        ]
        table = formatter.format_table(['ID', 'Type', 'State'], table_data)
        
        details = formatter.format_key_value({
            'Total Components': 2,
            'Active': 1,
            'Inactive': 1
        })
        
        # Combine all parts
        output = f"{title}\n{table}\n\n{details}"
        
        # Verify all parts present
        self.assertIn("Component Status", output)
        self.assertIn("SW1", output)
        self.assertIn("Total Components", output)
    
    def test_with_colors_and_unicode(self):
        """Test formatter with all features enabled."""
        formatter = OutputFormatter(use_colors=True, use_unicode=True)
        
        result = formatter.format_table(
            ['ID', 'Status'],
            [['1', 'OK']],
            alignments=[Alignment.LEFT, Alignment.CENTER]
        )
        
        # Should have Unicode borders
        self.assertIn('─', result)
        self.assertIn('│', result)


if __name__ == '__main__':
    unittest.main()

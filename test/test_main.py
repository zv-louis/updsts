# encoding: utf-8-sig

import pytest
import sys
from unittest.mock import patch, MagicMock
from argparse import ArgumentParser
from io import StringIO


@pytest.mark.unit
class TestMainModule:
    """Test cases for the main module."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down for each test."""
        # Store original argv
        self.original_argv = sys.argv
        yield
        # Restore original argv
        sys.argv = self.original_argv
    
    @patch('updsts.__main__.get_logger')
    @patch('updsts.__main__.handle_get')
    def test_main_get_command(self, mock_handle_get, mock_get_logger):
        """Test main function with 'get' command."""
        # Arrange
        sys.argv = ['awssts', 'get', '-n', 'test_profile', '-t', '123456']
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Act
        from updsts.__main__ import main
        main()
        
        # Assert
        mock_get_logger.assert_called_once_with(verbose_level=0)
        mock_handle_get.assert_called_once()
    
    @patch('updsts.__main__.get_logger')
    @patch('updsts.__main__.handle_list')
    def test_main_list_command(self, mock_handle_list, mock_get_logger):
        """Test main function with 'list' command."""
        # Arrange
        sys.argv = ['awssts', 'list']
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Act
        from updsts.__main__ import main
        main()
        
        # Assert
        mock_get_logger.assert_called_once_with(verbose_level=0)
        mock_handle_list.assert_called_once()
    
    @patch('updsts.__main__.get_logger')
    @patch('updsts.__main__.handle_mcp')
    def test_main_mcp_command(self, mock_handle_mcp, mock_get_logger):
        """Test main function with 'mcp' command."""
        # Arrange
        sys.argv = ['awssts', 'mcp']
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Act
        from updsts.__main__ import main
        main()
        
        # Assert
        mock_get_logger.assert_called_once_with(verbose_level=0)
        mock_handle_mcp.assert_called_once()
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_no_command(self, mock_stdout):
        """Test main function with no command (should show help)."""
        # Arrange
        sys.argv = ['awssts']
        
        # Act
        from updsts.__main__ import main
        main()
        
        # Assert
        output = mock_stdout.getvalue()
        assert 'usage:' in output.lower()
        assert 'Available commands' in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_verbose_level(self, mock_stdout):
        """Test main function with verbose level."""
        # Arrange
        sys.argv = ['awssts', '-v', '2', 'list']
        
        # Act & Assert - This should not raise an exception
        from updsts.__main__ import main
        try:
            main()
        except SystemExit:
            # ArgumentParser might call sys.exit, which is expected
            pass
    
    @patch('builtins.print')
    def test_main_file_not_found_error(self, mock_print):
        """Test main function handling FileNotFoundError."""
        # Arrange
        sys.argv = ['awssts', 'list']
        
        with patch('updsts.__main__.get_logger') as mock_get_logger:
            with patch('updsts.__main__.handle_list') as mock_handle_list:
                mock_handle_list.side_effect = FileNotFoundError()
                
                # Act
                from updsts.__main__ import main
                main()
                
                # Assert
                mock_print.assert_called_with(
                    "Error: Secrets file not found. Please ensure the file exists or specify a valid path."
                )
    
    @patch('builtins.print')
    def test_main_permission_error(self, mock_print):
        """Test main function handling PermissionError."""
        # Arrange
        sys.argv = ['awssts', 'list']
        
        with patch('updsts.__main__.get_logger') as mock_get_logger:
            with patch('updsts.__main__.handle_list') as mock_handle_list:
                mock_handle_list.side_effect = PermissionError()
                
                # Act
                from updsts.__main__ import main
                main()
                
                # Assert
                mock_print.assert_called_with(
                    "Error: Permission denied when accessing the credential file. Check your permissions."
                )
    
    @patch('builtins.print')
    def test_main_key_error(self, mock_print):
        """Test main function handling KeyError."""
        # Arrange
        sys.argv = ['awssts', 'list']
        
        with patch('updsts.__main__.get_logger') as mock_get_logger:
            with patch('updsts.__main__.handle_list') as mock_handle_list:
                mock_handle_list.side_effect = KeyError('test_profile')
                
                # Act
                from updsts.__main__ import main
                main()
                
                # Assert
                mock_print.assert_called_with(
                    "Error: Profile name ''test_profile'' is not found in the credential file. Please check the profile name."
                )
    
    @patch('builtins.print')
    def test_main_value_error(self, mock_print):
        """Test main function handling ValueError."""
        # Arrange
        sys.argv = ['awssts', 'list']
        error_message = "Invalid configuration"
        
        with patch('updsts.__main__.get_logger') as mock_get_logger:
            with patch('updsts.__main__.handle_list') as mock_handle_list:
                mock_handle_list.side_effect = ValueError(error_message)
                
                # Act
                from updsts.__main__ import main
                main()
                
                # Assert
                mock_print.assert_called_with(f"Error: {error_message}")
    
    @patch('builtins.print')
    def test_main_generic_exception(self, mock_print):
        """Test main function handling generic Exception."""
        # Arrange
        sys.argv = ['awssts', 'list']
        error_message = "Something went wrong"
        
        with patch('updsts.__main__.get_logger') as mock_get_logger:
            with patch('updsts.__main__.handle_list') as mock_handle_list:
                mock_handle_list.side_effect = Exception(error_message)
                
                # Act
                from updsts.__main__ import main
                main()
                
                # Assert
                mock_print.assert_called_with(f"Exception: {error_message}")
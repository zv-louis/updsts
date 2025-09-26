# encoding: utf-8-sig

import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace

from updsts.cmd_handler import handle_get, handle_list, handle_mcp


@pytest.mark.unit
class TestCmdHandler:
    """Test cases for command handlers."""
    
    def test_handle_get_with_credential_file(self, temp_dir):
        """Test handle_get with credential file specified."""
        # Arrange
        mock_cred_file = str(temp_dir / "credentials")
        args = Namespace(
            profile_name='test_profile',
            totp_token='123456',
            credential_file=mock_cred_file,
            duration=7200
        )
        
        # Act & Assert
        with patch('updsts.cmd_handler.update_credentials') as mock_update:
            handle_get(args)
            mock_update.assert_called_once_with(
                profile_name='test_profile',
                totp_token='123456',
                duration=7200,
                sts_profile_name=None,
                target_key=None,
                cred_file=mock_cred_file
            )
    
    def test_handle_get_without_credential_file(self):
        """Test handle_get without credential file specified."""
        # Arrange
        args = Namespace(
            profile_name='test_profile',
            totp_token='123456',
            credential_file=None,
            duration=None
        )
        
        # Act & Assert
        with patch('updsts.cmd_handler.update_credentials') as mock_update:
            handle_get(args)
            mock_update.assert_called_once_with(
                profile_name='test_profile',
                totp_token='123456',
                duration=3600,
                sts_profile_name=None,
                target_key=None,
                cred_file=None
            )
    
    def test_handle_get_with_all_parameters(self):
        """Test handle_get with all optional parameters specified."""
        # Arrange
        args = Namespace(
            profile_name='test_profile',
            totp_token='123456',
            credential_file='/path/to/creds',
            duration=7200,
            sts_profile_name='custom_sts',
            target_key='custom_key'
        )
        
        # Act & Assert
        with patch('updsts.cmd_handler.update_credentials') as mock_update:
            handle_get(args)
            mock_update.assert_called_once_with(
                profile_name='test_profile',
                totp_token='123456',
                duration=7200,
                sts_profile_name='custom_sts',
                target_key='custom_key',
                cred_file='/path/to/creds'
            )
    
    def test_handle_list_with_profiles(self, temp_dir):
        """Test handle_list with existing profiles."""
        # Arrange
        mock_profiles = [
            {
                'profile_name': 'default',
                'aws_access_key_id': 'AKIAIOSFODNN7EXAMPLE',
                'aws_secret_access_key': 'wJal****',
                'aws_session_token': '(not defined)',
                'expiration_datetime': '(not defined)',
                'mfa_device_arn': 'arn:aws:iam::123456789012:mfa/user',
                'totp_secret_name': 'default_secret'
            },
            {
                'profile_name': 'test_profile',
                'aws_access_key_id': 'AKIAI44QH8DHBEXAMPLE',
                'aws_secret_access_key': 'je7M****',
                'aws_session_token': 'temp****',
                'expiration_datetime': '2024-01-01T12:00:00+00:00',
                'mfa_device_arn': 'arn:aws:iam::123456789012:mfa/testuser',
                'totp_secret_name': 'test_secret'
            }
        ]
        
        mock_cred_file = str(temp_dir / "credentials")
        args = Namespace(credential_file=mock_cred_file)
        
        # Act & Assert
        with patch('updsts.cmd_handler.get_profile_list') as mock_get_profiles:
            with patch('builtins.print') as mock_print:
                mock_get_profiles.return_value = mock_profiles
                
                handle_list(args)
                
                mock_get_profiles.assert_called_once_with(
                    credential_file=mock_cred_file,
                    secret_mask=True
                )
                
                # Verify print calls
                print_calls = mock_print.call_args_list
                call_args = []
                for call in print_calls:
                    if call[0]:  # Check if args exist
                        call_args.append(call[0][0])
                
                assert 'Profile Name: default' in call_args
                assert '  Access Key ID       : AKIAIOSFODNN7EXAMPLE' in call_args
                assert '  Secret Key          : wJal****' in call_args
                assert 'Profile Name: test_profile' in call_args
    
    def test_handle_list_no_profiles(self):
        """Test handle_list with no profiles."""
        # Arrange
        args = Namespace(credential_file=None)
        
        # Act & Assert
        with patch('updsts.cmd_handler.get_profile_list') as mock_get_profiles:
            with patch('builtins.print') as mock_print:
                mock_get_profiles.return_value = []
                
                handle_list(args)
                
                mock_get_profiles.assert_called_once_with(
                    credential_file=None,
                    secret_mask=True
                )
                mock_print.assert_called_once_with("No profiles found.")
    
    def test_handle_mcp_server_mode(self):
        """Test handle_mcp in server mode."""
        # Arrange
        args = Namespace(mcp_server=True)
        
        # Act & Assert
        with patch('updsts.cmd_handler.run_as_mcp_server') as mock_run_server:
            handle_mcp(args)
            mock_run_server.assert_called_once()
    
    def test_handle_mcp_test_mode(self):
        """Test handle_mcp in test mode."""
        # Arrange
        args = Namespace(mcp_server=False)
        
        # Act & Assert
        with patch('updsts.cmd_handler.disp_tools') as mock_disp_tools:
            handle_mcp(args)
            mock_disp_tools.assert_called_once()
    
    def test_handle_mcp_no_server_flag(self):
        """Test handle_mcp without server flag."""
        # Arrange
        args = Namespace(mcp_server=False)
        
        # Act & Assert
        with patch('updsts.cmd_handler.disp_tools') as mock_disp_tools:
            handle_mcp(args)
            mock_disp_tools.assert_called_once()
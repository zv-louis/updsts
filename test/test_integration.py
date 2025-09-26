# encoding: utf-8-sig

import pytest
from unittest.mock import patch, MagicMock
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from datetime import datetime, timezone

from updsts.awsutil import get_sts_token, update_credentials


@pytest.mark.integration
@pytest.mark.aws
class TestSTSIntegration:
    """Integration test cases for STS functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self, sample_credentials_file_content, temp_file_factory):
        """Set up test fixtures for each test method."""
        self.credentials_file = temp_file_factory(
            sample_credentials_file_content,
            "credentials"
        )
        
        # Sample STS response
        self.sample_sts_response = {
            'Credentials': {
                'AccessKeyId': 'ASIAIDDDGFHSDEXAMPLE',
                'SecretAccessKey': 'shortTokenExample',
                'SessionToken': 'FQoDYXdzEJr//////////wEaEXAMPLE',
                'Expiration': datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            }
        }
    
    @patch('updsts.awsutil.boto3.Session')
    def test_get_sts_token_success(self, mock_session):
        """Test successful STS token retrieval."""
        # Arrange
        mock_client = MagicMock()
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = mock_client
        mock_client.get_session_token.return_value = self.sample_sts_response
        
        # Act
        result = get_sts_token(
            profile_name='test_profile',
            totp_token='123456',
            duration_seconds=3600,
            credential_file=str(self.credentials_file)
        )
        
        # Assert
        assert result is not None
        assert result['AccessKeyId'] == 'ASIAIDDDGFHSDEXAMPLE'
        assert result['SecretAccessKey'] == 'shortTokenExample'
        assert result['SessionToken'] == 'FQoDYXdzEJr//////////wEaEXAMPLE'
        assert 'Expiration' in result
        
        # Verify boto3 calls
        mock_session.assert_called_once_with(
            aws_access_key_id='AKIAI44QH8DHBEXAMPLE',
            aws_secret_access_key='je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY'
        )
        mock_client.get_session_token.assert_called_once_with(
            DurationSeconds=3600,
            SerialNumber='arn:aws:iam::123456789012:mfa/testuser',
            TokenCode='123456'
        )
    
    @patch('updsts.awsutil.boto3.Session')
    def test_get_sts_token_with_proxy(self, mock_session):
        """Test STS token retrieval with proxy settings."""
        # Arrange
        mock_client = MagicMock()
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = mock_client
        mock_client.get_session_token.return_value = self.sample_sts_response
        
        # Act
        with patch.dict('os.environ', {
            'http_proxy': 'http://proxy.example.com:8080',
            'https_proxy': 'https://proxy.example.com:8080'
        }):
            result = get_sts_token(
                profile_name='test_profile',
                totp_token='123456',
                credential_file=str(self.credentials_file)
            )
        
        # Assert
        assert result is not None
        
        # Verify client was created with proxy configuration
        mock_session_instance.client.assert_called_once_with(
            'sts',
            proxies={
                'http': 'http://proxy.example.com:8080',
                'https': 'https://proxy.example.com:8080'
            }
        )
    
    def test_get_sts_token_no_totp_token(self):
        """Test STS token retrieval without TOTP token."""
        # Act & Assert
        with pytest.raises(ValueError, match="TOTP token is required"):
            get_sts_token(
                profile_name='test_profile',
                totp_token='',
                credential_file=str(self.credentials_file)
            )
    
    def test_get_sts_token_file_not_found(self):
        """Test STS token retrieval with non-existent credentials file."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            get_sts_token(
                profile_name='test_profile',
                totp_token='123456',
                credential_file='/nonexistent/path/credentials'
            )
    
    def test_get_sts_token_missing_profile(self):
        """Test STS token retrieval with missing profile."""
        # Act & Assert
        with pytest.raises(Exception, match="Error reading profile"):
            get_sts_token(
                profile_name='nonexistent_profile',
                totp_token='123456',
                credential_file=str(self.credentials_file)
            )
    
    @patch('updsts.awsutil.boto3.Session')
    def test_get_sts_token_client_error(self, mock_session):
        """Test STS token retrieval with client error."""
        # Arrange
        mock_client = MagicMock()
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = mock_client
        mock_client.get_session_token.side_effect = ClientError(
            {'Error': {'Code': 'InvalidUserCode.Expired', 'Message': 'The security token is expired'}},
            'GetSessionToken'
        )
        
        # Act
        result = get_sts_token(
            profile_name='test_profile',
            totp_token='123456',
            credential_file=str(self.credentials_file)
        )
        
        # Assert
        assert result is None
    
    @patch('updsts.awsutil.get_sts_token')
    @patch('updsts.awsutil.CredentialUpdater')
    def test_update_credentials_success(self, mock_updater_class, mock_get_sts_token):
        """Test successful credentials update."""
        # Arrange
        mock_sts_credentials = {
            'AccessKeyId': 'ASIAIDDDGFHSDEXAMPLE',
            'SecretAccessKey': 'shortTokenExample',
            'SessionToken': 'FQoDYXdzEJr//////////wEaEXAMPLE',
            'Expiration': '2024-01-01T12:00:00+00:00'
        }
        mock_get_sts_token.return_value = mock_sts_credentials
        
        mock_updater = MagicMock()
        mock_updater_class.return_value = mock_updater
        mock_updater.update_credential_file.return_value = {
            'updated_profile_name': 'test_profile_sts',
            'aws_access_key_id': 'ASIAIDDDGFHSDEXAMPLE',
            'aws_token_expiration': '2024-01-01T12:00:00+00:00'
        }
        
        # Act
        result = update_credentials(
            profile_name='test_profile',
            totp_token='123456',
            cred_file=str(self.credentials_file)
        )
        
        # Assert
        assert result is not None
        assert result['updated_profile_name'] == 'test_profile_sts'
        
        # Verify function calls
        mock_get_sts_token.assert_called_once_with(
            profile_name='test_profile',
            totp_token='123456',
            duration_seconds=3600,
            credential_file=str(self.credentials_file)
        )
        
        mock_updater.set_target_tag_name.assert_called_once_with('test_profile')
        mock_updater.set_credentials.assert_called_once_with(mock_sts_credentials)
        mock_updater.set_sts_profile_name.assert_called_once_with(None)
        mock_updater.update_credential_file.assert_called_once()
    
    @patch('updsts.awsutil.get_sts_token')
    def test_update_credentials_sts_failure(self, mock_get_sts_token):
        """Test credentials update when STS token retrieval fails."""
        # Arrange
        mock_get_sts_token.return_value = None
        
        # Act & Assert
        with pytest.raises(Exception, match="Failed to retrieve STS credentials"):
            update_credentials(
                profile_name='test_profile',
                totp_token='123456',
                cred_file=str(self.credentials_file)
            )
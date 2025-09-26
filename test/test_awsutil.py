# encoding: utf-8-sig

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from configparser import ConfigParser

from updsts.awsutil import (
    mask_string,
    get_credential_file_path,
    get_profile_info,
    get_profile_list
)


@pytest.mark.unit
class TestMaskString:
    """Test cases for mask_string function."""
    
    def test_mask_string_empty(self):
        """Test masking empty string."""
        assert mask_string("") == ""
    
    def test_mask_string_short(self):
        """Test masking string shorter than unmask_chars."""
        assert mask_string("abc", 4) == "abc"
        assert mask_string("ab", 4) == "ab"
    
    def test_mask_string_normal(self):
        """Test normal masking."""
        assert mask_string("abcdef", 4) == "abcd**"
        assert mask_string("password123", 4) == "pass*******"
    
    def test_mask_string_long(self):
        """Test masking very long string."""
        long_string = "very_long_string_example_that_exceeds_max_length"
        result = mask_string(long_string, 4, 16)
        assert result.startswith("very")
        assert "chars)" in result
        assert str(len(long_string)) in result
    
    def test_mask_string_whitespace(self):
        """Test masking string with whitespace."""
        assert mask_string("  test  ", 2) == "te**"


@pytest.mark.unit
class TestCredentialFilePath:
    """Test cases for get_credential_file_path function."""
    
    def test_get_default_path(self):
        """Test getting default credential file path."""
        expected_path = Path(os.path.expanduser("~")) / ".aws" / "credentials"
        assert get_credential_file_path() == expected_path
        assert get_credential_file_path(None) == expected_path
        assert get_credential_file_path("") == expected_path
        assert get_credential_file_path("  ") == expected_path
    
    def test_get_custom_path(self):
        """Test getting custom credential file path."""
        custom_path = "/custom/path/credentials"
        result = get_credential_file_path(custom_path)
        assert result == Path(custom_path)


@pytest.mark.unit
class TestProfileInfo:
    """Test cases for profile information functions."""
    
    def test_get_profile_info_existing(self, credentials_file):
        """Test getting existing profile information."""
        profile_info = get_profile_info(
            "default", 
            str(credentials_file),
            secret_mask=False
        )
        
        assert profile_info is not None
        assert profile_info['profile_name'] == 'default'
        assert profile_info['aws_access_key_id'] == 'AKIAIOSFODNN7EXAMPLE'
        assert profile_info['aws_secret_access_key'] == 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
        assert profile_info['mfa_device_arn'] == 'arn:aws:iam::123456789012:mfa/user'
        assert profile_info['totp_secret_name'] == 'default_secret'
    
    def test_get_profile_info_with_masking(self, credentials_file):
        """Test getting profile information with secret masking."""
        profile_info = get_profile_info(
            "default", 
            str(credentials_file),
            secret_mask=True
        )
        
        assert profile_info is not None
        # Check that the secret key is masked (contains asterisks)
        secret_key = profile_info['aws_secret_access_key']
        assert '*' in secret_key and secret_key.startswith('wJal')
        # Check that access key is not masked
        assert profile_info['aws_access_key_id'] == 'AKIAIOSFODNN7EXAMPLE'
    
    def test_get_profile_info_nonexistent(self, credentials_file):
        """Test getting non-existent profile information."""
        profile_info = get_profile_info(
            "nonexistent", 
            str(credentials_file),
            secret_mask=False
        )
        
        # Should return a dictionary with default values when profile doesn't exist
        assert profile_info is not None
    
    def test_get_profile_list(self, credentials_file):
        """Test getting list of all profiles."""
        profiles = get_profile_list(
            str(credentials_file),
            secret_mask=False
        )
        
        assert len(profiles) == 3
        profile_names = [p['profile_name'] for p in profiles]
        assert 'default' in profile_names
        assert 'test_profile' in profile_names
        assert 'sts_profile' in profile_names
    
    def test_get_profile_list_with_masking(self, credentials_file):
        """Test getting list of profiles with masking."""
        profiles = get_profile_list(
            str(credentials_file),
            secret_mask=True
        )
        
        for profile in profiles:
            if 'aws_secret_access_key' in profile and profile['aws_secret_access_key'] != '(not defined)':
                assert '*' in profile['aws_secret_access_key']
    
    def test_file_not_found(self):
        """Test handling of non-existent credentials file."""
        with pytest.raises(FileNotFoundError):
            get_profile_info("default", "/nonexistent/path/credentials")
        
        with pytest.raises(FileNotFoundError):
            get_profile_list("/nonexistent/path/credentials")
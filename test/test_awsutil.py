# encoding: utf-8-sig

import pytest
import io
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock
from configparser import ConfigParser

from updsts.awsutil import (
    mask_string,
    get_credential_file_path,
    get_sts_token,
    get_profile_info,
    get_profile_list,
    mask_url_credentials,
    load_credentials_config,
)


@pytest.mark.unit
class TestMaskString:
    """Test cases for mask_string function."""
    
    def test_mask_string_empty(self):
        """Test masking empty string."""
        assert mask_string("") == ""
    
    def test_mask_string_short(self):
        """Test masking string not longer than unmask_chars_head + unmask_chars_tail."""
        assert mask_string("abc", 4) == "abc"
        assert mask_string("ab", 4) == "ab"
        assert mask_string("abcdefgh", 4, 4) == "abcdefgh"
    
    def test_mask_string_normal(self):
        """Test normal masking."""
        assert mask_string("abcdefgh", 4, 0) == "abcd****"
        assert mask_string("abcdefgh", 4, 2) == "abcd**gh"
        assert mask_string("password123", 4) == "pass***d123"
    
    def test_mask_string_long(self):
        """Test masking very long string."""
        long_string = "very_long_string_example_that_exceeds_max_length"
        result = mask_string(long_string, 4, 4, 16)
        assert result == f"very********ngth ({len(long_string)} chars)"
        assert "chars)" in result
        assert str(len(long_string)) in result
    
    def test_mask_string_whitespace(self):
        """Test masking string with whitespace."""
        assert mask_string("  testcase  ", 2, 2) == "te****se"


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
        # Check that access key is also masked
        assert profile_info['aws_access_key_id'] == 'AKIA********MPLE (20 chars)'
    
    def test_get_profile_info_nonexistent(self, credentials_file):
        """Test getting non-existent profile information."""
        profile_info = get_profile_info(
            "nonexistent", 
            str(credentials_file),
            secret_mask=False
        )
        
        assert profile_info is None
    
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


@pytest.mark.unit
class TestMaskUrlCredentials:
    """Test cases for mask_url_credentials function."""

    def test_masks_password(self):
        assert mask_url_credentials("http://user:p%40ss@proxy:8080") == "http://user:****@proxy:8080"

    def test_without_credentials(self):
        assert mask_url_credentials("http://proxy:8080") == "http://proxy:8080"

    def test_username_only(self):
        assert mask_url_credentials("http://user@proxy:8080") == "http://user@proxy:8080"


@pytest.mark.unit
class TestNoSecretsInLog:
    """Raw secrets must not appear in logs even at DEBUG level."""

    ACCESS_KEY = "AKIARAWACCESSKEY0001"
    SECRET_KEY = "RawSecretAccessKeyValue0000000000000001"
    SESSION_TOKEN = "RawSessionTokenValue000000000000000001"

    @pytest.fixture
    def secret_credentials_file(self, temp_file_factory):
        return temp_file_factory(
            f"[default]\naws_access_key_id = {self.ACCESS_KEY}\n"
            f"aws_secret_access_key = {self.SECRET_KEY}\n"
            f"aws_session_token = {self.SESSION_TOKEN}\n"
            "mfa_device_arn = arn:aws:iam::123456789012:mfa/user\n",
            "credentials",
        )

    def assert_no_raw_secrets(self, caplog):
        for raw in (self.ACCESS_KEY, self.SECRET_KEY, self.SESSION_TOKEN, "proxypass"):
            assert raw not in caplog.text

    @pytest.mark.parametrize("secret_mask", [False, True])
    def test_get_profile_info(self, secret_credentials_file, caplog, secret_mask):
        caplog.set_level(logging.DEBUG, logger="awssts")
        get_profile_info("default", str(secret_credentials_file), secret_mask=secret_mask)
        assert "aws_secret_access_key" in caplog.text  # debug lines are emitted
        self.assert_no_raw_secrets(caplog)

    def test_get_profile_list(self, secret_credentials_file, caplog):
        caplog.set_level(logging.DEBUG, logger="awssts")
        get_profile_list(str(secret_credentials_file))
        self.assert_no_raw_secrets(caplog)

    @pytest.mark.aws
    def test_get_sts_token(self, secret_credentials_file, caplog, monkeypatch):
        caplog.set_level(logging.DEBUG, logger="awssts")
        monkeypatch.setenv("https_proxy", "http://proxyuser:proxypass@proxy:8080")
        with patch("updsts.awsutil.boto3.Session") as session:
            session.return_value.client.return_value.get_session_token.return_value = {
                "Credentials": {"AccessKeyId": "ASIANEW", "SecretAccessKey": "new",
                                "SessionToken": "new", "Expiration": datetime.now(timezone.utc)}
            }
            get_sts_token("default", "123456", credential_file=str(secret_credentials_file))
        assert "Using HTTPS proxy" in caplog.text
        self.assert_no_raw_secrets(caplog)


@pytest.fixture
def cp932_locale(monkeypatch):
    """Simulate a Japanese Windows locale: files opened without an explicit encoding are decoded as cp932."""
    real_text_encoding = io.text_encoding
    monkeypatch.setattr(io, "text_encoding",
                        lambda encoding, stacklevel=2: "cp932" if encoding is None else real_text_encoding(encoding))


@pytest.mark.unit
class TestCredentialFileEncoding:
    """The credentials file is read as UTF-8 (with or without BOM) regardless of the system locale."""

    BODY = ("# 日本語のコメント\n"  # its UTF-8 bytes are invalid as cp932
            "[default]\naws_access_key_id = AKIAIOSFODNN7EXAMPLE\n"
            "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n"
            "mfa_device_arn = arn:aws:iam::123456789012:mfa/user\n")

    @pytest.fixture(params=["utf-8", "utf-8-sig"])
    def utf8_credentials_file(self, request, temp_file_factory):
        path = temp_file_factory("", "credentials")
        path.write_bytes(self.BODY.encode(request.param))
        return path

    def test_get_profile_info(self, utf8_credentials_file, cp932_locale):
        assert get_profile_info("default", str(utf8_credentials_file))["profile_name"] == "default"

    def test_get_profile_list(self, utf8_credentials_file, cp932_locale):
        assert [p["profile_name"] for p in get_profile_list(str(utf8_credentials_file))] == ["default"]

    @pytest.mark.aws
    def test_get_sts_token(self, utf8_credentials_file, cp932_locale):
        with patch("updsts.awsutil.boto3.Session") as session:
            session.return_value.client.return_value.get_session_token.return_value = {
                "Credentials": {"AccessKeyId": "key", "SecretAccessKey": "secret",
                                "SessionToken": "token", "Expiration": datetime.now(timezone.utc)}
            }
            assert get_sts_token("default", "123456", credential_file=str(utf8_credentials_file)) is not None
        session.assert_called_once_with(aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
                                        aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")

    def test_non_utf8_file_raises_clear_error(self, temp_file_factory):
        path = temp_file_factory("", "credentials")
        path.write_bytes(self.BODY.encode("cp932"))
        with pytest.raises(ValueError, match="not UTF-8 encoded.*re-save it as UTF-8"):
            load_credentials_config(path)

    def test_percent_in_value_is_literal(self, temp_file_factory):
        path = temp_file_factory("[default]\naws_access_key_id = AKIA%EXAMPLE\nnote = 100%\n", "credentials")
        info = get_profile_info("default", str(path))
        assert info["aws_access_key_id"] == "AKIA%EXAMPLE"
        assert info["note"] == "100%"

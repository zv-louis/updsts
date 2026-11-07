# encoding: utf-8-sig

import pytest
import os
import platform
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

from updsts.upcred import CredentialUpdater


@pytest.mark.unit
class TestCredentialUpdater:
    """Test cases for CredentialUpdater class."""
    
    def test_init_without_path(self):
        """Test CredentialUpdater initialization without path."""
        updater = CredentialUpdater()
        assert updater.credential_file_path is None
        assert updater.creds == {}
        assert updater.target_tag_name is None
        assert updater.sts_profile_name is None
    
    def test_init_with_path(self, temp_dir):
        """Test CredentialUpdater initialization with path."""
        test_path = temp_dir / "test_credentials"
        updater = CredentialUpdater(test_path)
        assert updater.credential_file_path == test_path
    
    def test_set_credentials_path(self, temp_dir):
        """Test setting credentials path."""
        updater = CredentialUpdater()
        test_path = temp_dir / "test_credentials"
        
        # Test with Path object
        updater.set_credentials_path(test_path)
        assert updater.credential_file_path == test_path
        
        # Test with string path
        updater.set_credentials_path(str(test_path))
        assert updater.credential_file_path == test_path
    
    def test_set_target_tag_name(self):
        """Test setting target tag name."""
        updater = CredentialUpdater()
        updater.set_target_tag_name("test_profile")
        assert updater.target_tag_name == "test_profile"
    
    def test_set_credentials(self, sample_credentials):
        """Test setting credentials."""
        updater = CredentialUpdater()
        updater.set_credentials(sample_credentials)
        assert updater.creds == sample_credentials
    
    def test_set_sts_profile_name(self):
        """Test setting STS profile name."""
        updater = CredentialUpdater()
        updater.set_sts_profile_name("custom_sts")
        assert updater.sts_profile_name == "custom_sts"
    
    def test_update_credential_file_with_existing_tag(self, temp_file_factory, sample_credentials):
        """Test updating credentials file with existing replacement tag."""
        # Create credentials file with replacement tags
        credentials_content = """[default]
aws_access_key_id=AKIAIOSFODNN7EXAMPLE
aws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# ${{{ key=test_profile [auto update by updsts]
[test_profile_sts]
aws_access_key_id=old_access_key
aws_secret_access_key=old_secret_key
aws_session_token=old_session_token
expiration_datetime=old_expiration
# $}}} [auto update by updsts]

[another_profile]
aws_access_key_id=ANOTHER_ACCESS_KEY
"""
        
        credentials_file = temp_file_factory(credentials_content, "credentials")
        
        # Set up updater
        updater = CredentialUpdater(credentials_file)
        updater.set_target_tag_name("test_profile")
        updater.set_credentials(sample_credentials)
        
        # Update the file
        result = updater.update_credential_file()
        
        # Verify result
        assert result is not None
        assert result['updated_profile_name'] == 'test_profile_sts'
        assert result['aws_access_key_id'] == 'ASIAIDDDGFHSDEXAMPLE'
        
        # Verify file content
        updated_content = credentials_file.read_text(encoding='utf-8')
        assert 'ASIAIDDDGFHSDEXAMPLE' in updated_content
        assert 'shortTokenExample' in updated_content
        assert 'FQoDYXdzEJr//////////wEaEXAMPLE' in updated_content
        assert '2024-01-01T12:00:00+00:00' in updated_content
    
    def test_update_credential_file_without_existing_tag(self, temp_file_factory, sample_credentials):
        """Test updating credentials file without existing replacement tag."""
        # Create credentials file without replacement tags
        credentials_content = """[default]
aws_access_key_id=AKIAIOSFODNN7EXAMPLE
aws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

[another_profile]
aws_access_key_id=ANOTHER_ACCESS_KEY
"""
        
        credentials_file = temp_file_factory(credentials_content, "credentials")
        
        # Set up updater
        updater = CredentialUpdater(credentials_file)
        updater.set_target_tag_name("new_profile")
        updater.set_credentials(sample_credentials)
        
        # Update the file
        result = updater.update_credential_file()
        
        # Verify result
        assert result is not None
        assert result['updated_profile_name'] == 'new_profile_sts'
        
        # Verify file content
        updated_content = credentials_file.read_text(encoding='utf-8')
        assert '[new_profile_sts]' in updated_content
        assert 'ASIAIDDDGFHSDEXAMPLE' in updated_content
        assert '# ${{{ key=new_profile [auto update by updsts]' in updated_content
        assert '# $}}} [auto update by updsts]' in updated_content
    
    def test_update_credential_file_with_custom_sts_profile_name(self, temp_file_factory, sample_credentials):
        """Test updating credentials file with custom STS profile name."""
        credentials_content = """[default]
aws_access_key_id=AKIAIOSFODNN7EXAMPLE
"""
        
        credentials_file = temp_file_factory(credentials_content, "credentials")
        
        # Set up updater with custom STS profile name
        updater = CredentialUpdater(credentials_file)
        updater.set_target_tag_name("test_profile")
        updater.set_credentials(sample_credentials)
        updater.set_sts_profile_name("custom_sts_name")
        
        # Update the file
        result = updater.update_credential_file()
        
        # Verify result
        assert result is not None
        assert result['updated_profile_name'] == 'custom_sts_name'
        
        # Verify file content
        updated_content = credentials_file.read_text(encoding='utf-8')
        assert '[custom_sts_name]' in updated_content

    def test_update_credential_file_logs_actual_profile_name(self, temp_file_factory, sample_credentials, caplog):
        """Test that the log for a newly added block shows the profile name actually written."""
        credentials_file = temp_file_factory("[default]\naws_access_key_id=AKIAIOSFODNN7EXAMPLE\n", "credentials")
        caplog.set_level(logging.INFO, logger="awssts")

        updater = CredentialUpdater(credentials_file)
        updater.set_target_tag_name("test_profile")
        updater.set_credentials(sample_credentials)
        updater.set_sts_profile_name("custom_sts_name")
        updater.update_credential_file()

        assert "profile='custom_sts_name'" in caplog.text
        assert "test_profile_sts" not in caplog.text

    @pytest.mark.skipif(platform.system() == 'Windows', reason="File permission test not applicable on Windows")
    def test_update_credential_file_preserves_permissions(self, temp_file_factory, sample_credentials):
        """Test that file permissions are preserved during update."""
        credentials_content = """[default]
aws_access_key_id=AKIAIOSFODNN7EXAMPLE
"""
        
        credentials_file = temp_file_factory(credentials_content, "credentials")
        
        # Set specific permissions (Unix-like systems only)
        try:
            os.chmod(credentials_file, 0o600)  # rw-------
        except (OSError, AttributeError):
            pytest.skip("File permission test not applicable on this system")
        
        # Set up updater
        updater = CredentialUpdater(credentials_file)
        updater.set_target_tag_name("test_profile")
        updater.set_credentials(sample_credentials)
        
        # Update the file
        updater.update_credential_file()
        
        # Verify permissions are preserved
        new_mode = credentials_file.stat().st_mode
        assert new_mode & 0o777 == 0o600

    @pytest.mark.skipif(platform.system() == 'Windows', reason="File permission test not applicable on Windows")
    def test_update_credential_file_temp_file_is_owner_only(self, temp_file_factory, sample_credentials):
        """Test that the temp file is owner-only while secrets are being written, even with a stale temp file."""
        credentials_file = temp_file_factory("[default]\naws_access_key_id=AKIAIOSFODNN7EXAMPLE\n", "credentials")
        temp_file_path = credentials_file.with_suffix(".tmp")
        # a stale, world-readable temp file must not keep its mode
        temp_file_path.write_text("stale")
        os.chmod(temp_file_path, 0o644)

        updater = CredentialUpdater(credentials_file)
        updater.set_target_tag_name("test_profile")
        updater.set_credentials(sample_credentials)

        # capture the temp file mode just before permissions are copied from the original
        real_chmod = os.chmod
        modes = []
        def spy_chmod(path, mode, *args, **kwargs):
            modes.append(os.stat(path).st_mode & 0o777)
            return real_chmod(path, mode, *args, **kwargs)

        with patch("updsts.upcred.os.chmod", side_effect=spy_chmod):
            updater.update_credential_file()

        assert modes == [0o600]
        assert not temp_file_path.exists()

    def test_update_credential_file_with_stale_temp_file(self, temp_file_factory, sample_credentials):
        """Test that a leftover temp file does not prevent the update."""
        credentials_file = temp_file_factory("[default]\naws_access_key_id=AKIAIOSFODNN7EXAMPLE\n", "credentials")
        temp_file_path = credentials_file.with_suffix(".tmp")
        temp_file_path.write_text("stale")

        updater = CredentialUpdater(credentials_file)
        updater.set_target_tag_name("test_profile")
        updater.set_credentials(sample_credentials)
        updater.update_credential_file()

        assert not temp_file_path.exists()
        content = credentials_file.read_text(encoding="utf-8")
        assert "stale" not in content
        assert "[test_profile_sts]" in content

    def test_update_credential_file_cleans_up_temp_files(self, temp_file_factory, sample_credentials):
        """Test that temporary files are cleaned up."""
        credentials_content = """[default]
aws_access_key_id=AKIAIOSFODNN7EXAMPLE
"""
        
        credentials_file = temp_file_factory(credentials_content, "credentials")
        temp_file_path = credentials_file.with_suffix(".tmp")
        
        # Set up updater
        updater = CredentialUpdater(credentials_file)
        updater.set_target_tag_name("test_profile")
        updater.set_credentials(sample_credentials)
        
        # Update the file
        updater.update_credential_file()
        
        # Verify temp file is cleaned up
        assert not temp_file_path.exists()
        
        # Verify original file exists
        assert credentials_file.exists()

    def test_update_credential_file_removes_temp_file_on_error(self, temp_file_factory, sample_credentials):
        """Test that the temp file is removed and the original is kept when reading fails."""
        credentials_file = temp_file_factory("", "credentials")
        # secrets before a non-UTF-8 (cp932) comment get copied to the temp file before the decode error
        original_bytes = ("[default]\naws_access_key_id=AKIAIOSFODNN7EXAMPLE\n"
                          "# 日本語のコメント\n").encode("cp932")
        credentials_file.write_bytes(original_bytes)
        temp_file_path = credentials_file.with_suffix(".tmp")

        updater = CredentialUpdater(credentials_file)
        updater.set_target_tag_name("default")
        updater.set_credentials(sample_credentials)

        with pytest.raises(ValueError, match="not UTF-8 encoded.*re-save it as UTF-8"):
            updater.update_credential_file()

        assert not temp_file_path.exists()
        assert credentials_file.read_bytes() == original_bytes

    def test_update_credential_file_keeps_original_when_replace_fails(self, temp_file_factory, sample_credentials):
        """Test that the original file stays intact and the temp file is removed when the replace fails."""
        credentials_content = "[default]\naws_access_key_id=AKIAIOSFODNN7EXAMPLE\n"
        credentials_file = temp_file_factory(credentials_content, "credentials")
        original_bytes = credentials_file.read_bytes()
        temp_file_path = credentials_file.with_suffix(".tmp")

        updater = CredentialUpdater(credentials_file)
        updater.set_target_tag_name("test_profile")
        updater.set_credentials(sample_credentials)

        with patch("updsts.upcred.os.replace", side_effect=PermissionError("locked")):
            with pytest.raises(PermissionError):
                updater.update_credential_file()

        assert credentials_file.read_bytes() == original_bytes
        assert not temp_file_path.exists()

    def test_update_credential_file_with_bom(self, temp_file_factory, sample_credentials):
        """Test that a UTF-8 file with BOM is updated in place and written back without the BOM."""
        credentials_file = temp_file_factory("", "credentials")
        credentials_file.write_bytes((
            "# ${{{ key=default [auto update by updsts]\n"
            "[default_sts]\naws_access_key_id=OLD\n"
            "# $}}} [auto update by updsts]\n"
            "# 日本語のコメント\n").encode("utf-8-sig"))

        updater = CredentialUpdater(credentials_file)
        updater.set_target_tag_name("default")
        updater.set_credentials(sample_credentials)
        result = updater.update_credential_file()

        raw = credentials_file.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf")
        content = raw.decode("utf-8")
        # the existing block (on the first line, right after the BOM) is replaced, not appended
        assert content.count("[default_sts]") == 1
        assert "OLD" not in content
        assert f"aws_access_key_id={sample_credentials['AccessKeyId']}" in content
        assert "# 日本語のコメント" in content
        assert result["updated_profile_name"] == "default_sts"

    def test_update_credential_file_message_handler(self, temp_file_factory, sample_credentials, capsys):
        """Test 'found key' message is passed to the message handler (CLI mode)."""
        credentials_content = """# ${{{ key=test_profile [auto update by updsts]
[test_profile_sts]
aws_access_key_id=old_access_key
# $}}} [auto update by updsts]
"""
        credentials_file = temp_file_factory(credentials_content, "credentials")
        updater = CredentialUpdater(credentials_file)
        updater.set_target_tag_name("test_profile")
        updater.set_credentials(sample_credentials)
        updater.set_message_handler(print)

        updater.update_credential_file()

        assert capsys.readouterr().out == "found key : key='test_profile'\n"

    def test_update_credential_file_without_message_handler(self, temp_file_factory, sample_credentials, capsys):
        """Test nothing is written to stdout without a message handler (MCP mode)."""
        credentials_content = """# ${{{ key=test_profile [auto update by updsts]
[test_profile_sts]
aws_access_key_id=old_access_key
# $}}} [auto update by updsts]
"""
        credentials_file = temp_file_factory(credentials_content, "credentials")
        updater = CredentialUpdater(credentials_file)
        updater.set_target_tag_name("test_profile")
        updater.set_credentials(sample_credentials)

        updater.update_credential_file()

        assert capsys.readouterr().out == ""

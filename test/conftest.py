# encoding: utf-8-sig

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture(scope="function")
def temp_dir():
    """Fixture that provides a temporary directory for each test."""
    test_tmp_dir = Path(tempfile.mkdtemp(prefix="updsts_pytest_"))
    yield test_tmp_dir
    # Cleanup
    if test_tmp_dir.exists():
        shutil.rmtree(test_tmp_dir, ignore_errors=True)

@pytest.fixture(scope="function")
def temp_file_factory(temp_dir):
    """Fixture that provides a factory function to create temporary files."""
    def create_temp_file(content: str, filename: str = None) -> Path:
        if filename is None:
            temp_file = temp_dir / f"temp_{len(list(temp_dir.iterdir()))}.txt"
        else:
            temp_file = temp_dir / filename
        
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file.write_text(content, encoding='utf-8')
        return temp_file
    
    return create_temp_file

@pytest.fixture(scope="function")
def sample_credentials():
    """Fixture providing sample AWS credentials for testing."""
    return {
        'AccessKeyId': 'ASIAIDDDGFHSDEXAMPLE',
        'SecretAccessKey': 'shortTokenExample',
        'SessionToken': 'FQoDYXdzEJr//////////wEaEXAMPLE',
        'Expiration': '2024-01-01T12:00:00+00:00'
    }

@pytest.fixture(scope="function")
def sample_credentials_file_content():
    """Fixture providing sample credentials file content."""
    return """[default]
aws_access_key_id=AKIAIOSFODNN7EXAMPLE
aws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
mfa_device_arn=arn:aws:iam::123456789012:mfa/user
totp_secret_name=default_secret

[test_profile]
aws_access_key_id=AKIAI44QH8DHBEXAMPLE
aws_secret_access_key=je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY
aws_session_token=temporary_session_token_example
mfa_device_arn=arn:aws:iam::123456789012:mfa/testuser
totp_secret_name=test_secret
expiration_datetime=2024-01-01T12:00:00+00:00

[sts_profile]
aws_access_key_id=ASIAIDDDGFHSDEXAMPLE
aws_secret_access_key=shortTokenExample
aws_session_token=FQoDYXdzEJr
expiration_datetime=2024-01-01T10:00:00+00:00
"""

@pytest.fixture(scope="function")
def credentials_file(temp_file_factory, sample_credentials_file_content):
    """Fixture providing a temporary credentials file."""
    return temp_file_factory(sample_credentials_file_content, "credentials")

# Configure pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests") 
    config.addinivalue_line("markers", "aws: Tests that interact with AWS services (mocked)")
    config.addinivalue_line("markers", "slow: Slow tests that may take longer to run")
# encoding: utf-8-sig

import os
import sys
import boto3
from datetime import datetime, timezone

from botocore.exceptions import BotoCoreError, ClientError
from configparser import ConfigParser, NoSectionError, NoOptionError
from pathlib import Path
from typing import Optional, Dict, Any

from .logutil import get_logger
from .upcred import CredentialUpdater

# ----------------------------------------------------------------------------
def mask_string(s: str,
                unmask_chars_head: int = 4,
                unmask_chars_tail: int = 4,
                max_strlen = 16) -> str:
    """
    Mask the middle characters of the input string `s`, leaving head and tail visible.

    Args:
        s (str): The input string to mask
        unmask_chars_head (int, optional): Number of characters to show at the beginning. Defaults to 4.
        unmask_chars_tail (int, optional): Number of characters to show at the end. Defaults to 4.
        max_strlen (int, optional): Maximum display length before truncation. Defaults to 16.

    Returns:
        str: Masked string with the following behavior:
            - If string length <= unmask_chars_head + unmask_chars_tail: returns the string as is
            - If string length > max_strlen: shows head + masked chars + tail + ' (total_length chars)'
            - Otherwise: shows head + masked middle + tail

    Examples:
        mask_string("abc", 4, 4) -> "abc"
        mask_string("abcdefgh", 4, 0) -> "abcd****"
        mask_string("abcdefgh", 4, 2) -> "abcd**gh"
        mask_string("very_long_string_example", 4, 4, 16) -> "very********ple (24 chars)"
    """
    if not s:
        return ''

    # Strip whitespace and newlines from input
    s = s.strip()
    str_len = len(s)
    if str_len <= unmask_chars_head + unmask_chars_tail:
        return s

    tail_part = s[-unmask_chars_tail:] if unmask_chars_tail > 0 else ''

    # Handle long strings
    if str_len > max_strlen:
        truncate_len = max_strlen
        middle_mask_len = truncate_len - unmask_chars_head - unmask_chars_tail
        if middle_mask_len <= 0:
            return s[:unmask_chars_head] + tail_part + f' ({str_len} chars)'
        masked_part = '*' * middle_mask_len
        return s[:unmask_chars_head] + masked_part + tail_part + f' ({str_len} chars)'

    # Normal masking for strings within max_strlen
    middle_mask_len = str_len - unmask_chars_head - unmask_chars_tail
    masked_part = '*' * middle_mask_len
    return s[:unmask_chars_head] + masked_part + tail_part


# ----------------------------------------------------------------------------
def get_credential_file_path(credential_file: str | None = None) -> Path:
    """
    Get the path to the AWS credentials file.
    Args:
        credential_file (str | None, optional): Path to the AWS credentials file. 
            If None, the default location (~/.aws/credentials) is used. Defaults to None.
    Returns:
        credential_file_path (Path): Path object of the credential file.
    """
    cred_path  = credential_file.strip() if credential_file is not None else credential_file
    if not cred_path:
        user_home = os.path.expanduser("~")
        credential_file_path = Path(user_home) / ".aws" / "credentials"
    else:
        credential_file_path = Path(cred_path)
    logger = get_logger()
    logger.debug(f"Using credential file: {credential_file_path}")
    return credential_file_path

# ----------------------------------------------------------------------------
def get_sts_token(profile_name: str,
                  totp_token: str,
                  duration_seconds: int = 3600,
                  credential_file: str | None = None) -> Optional[Dict[str, Any]]:
    """
    Get temporary STS token using MFA.
    Args:
        profile_name (str): The profile name in the AWS credentials file.
        totp_token (str): The TOTP token of the registerd MFA device. 
        credential_file (str | None, optional): Path to the AWS credentials file. 
            If None, the default location (~/.aws/credentials) is used. Defaults to None.
    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the temporary STS credentials
            if successful, None otherwise. 
    Raises:
        Exception: If there is an error reading the credentials file or obtaining the STS token.
    """
    logger = get_logger()

    if totp_token is None or len(totp_token) == 0:
        raise ValueError("TOTP token is required to obtain STS token.")

    credential_file = get_credential_file_path(credential_file)
    if not credential_file.exists():
        raise FileNotFoundError(f"Credential file '{credential_file}' does not exist.")
    config = ConfigParser()
    config.read(credential_file)
    try:
        access_key = config.get(profile_name, 'aws_access_key_id')
        secret_key = config.get(profile_name, 'aws_secret_access_key')
        mfa_arn    = config.get(profile_name, 'mfa_device_arn')
    except (NoOptionError) as e:
        raise Exception(f"Profile '{profile_name}' is missing required options: {e}")
    except (NoSectionError) as e:
        raise Exception(f"Error reading profile '{profile_name}' from credentials file: {e}")

    logger.debug(f"Using profile '{profile_name}' with access key '{access_key}' and MFA device ARN '{mfa_arn}'")

    try:
        # Read proxy settings from environment variables
        proxies = {}
        http_proxy = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY')
        https_proxy = os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY')
        if http_proxy:
            proxies['http'] = http_proxy
            logger.debug(f"Using HTTP proxy: {http_proxy}")
        if https_proxy:
            proxies['https'] = https_proxy
            logger.debug(f"Using HTTPS proxy: {https_proxy}")

        # Create a session with explicit credentials
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )

        # Create STS client with proxy configuration if available
        client_config = {}
        if proxies:
            client_config['proxies'] = proxies

        sts_client = session.client('sts', **client_config)
        response = sts_client.get_session_token(DurationSeconds=duration_seconds,
                                                SerialNumber=mfa_arn,
                                                TokenCode=totp_token)
        credentials = response['Credentials']
        logger.info(f"Successfully obtained temporary STS credentials for profile '{profile_name}'")

        # Convert expiration time from UTC to local timezone
        expiration_utc = credentials['Expiration']
        # AWS returns naive datetime in UTC, so we need to make it timezone-aware
        if expiration_utc.tzinfo is None:
            expiration_utc = expiration_utc.replace(tzinfo=timezone.utc)
        # Convert to local timezone
        expiration_local = expiration_utc.astimezone()

        return {
            'AccessKeyId': credentials['AccessKeyId'],
            'SecretAccessKey': credentials['SecretAccessKey'],
            'SessionToken': credentials['SessionToken'],
            'Expiration': expiration_local.isoformat()
        }
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Error obtaining STS token: {e}")
        return None

# ----------------------------------------------------------------------------
def get_profile_info(profile_name: str,
                     credential_file: str | None = None,
                     secret_mask: bool = False,
                     ctx: ConfigParser = None) -> Optional[Dict[str, str]]:
    """
    Get the credencials from the AWS credentials file for the specified profile.
    Args:
        profile_name (str): The profile name in the AWS credentials file.
        credential_file (str | None, optional): Path to the AWS credentials file. 
            If None, the default location (~/.aws/credentials) is used. Defaults to None.
    Returns:
        Optional[Dict[str, str]]: A dictionary containing secret details
            if successful, None otherwise.
    Raises:
        Exception: If there is an error reading the profile from the credentials file.
    """
    logger = get_logger()
    config = ctx
    if config is None:
        credential_file = get_credential_file_path(credential_file)
        if not credential_file.exists():
            raise FileNotFoundError(f"Credential file '{credential_file}' does not exist.")
        config = ConfigParser()
        config.read(credential_file)
    item_dic = None
    try:
        item_dic = {
            'aws_access_key_id': '(not defined)',
            'aws_secret_access_key': '(not defined)',
            'aws_session_token': '(not defined)',
            'mfa_device_arn': '(not defined)',
            'totp_secret_name': '(not defined)',
            'expiration_datetime': '(not defined)'
        }
        for key, value in config.items(profile_name):
            # Remove whitespace and newlines from log output
            raw_sensitive_value = value.strip() if value else value
            logger.debug(f"Profile '{profile_name}': {key} = {raw_sensitive_value}")
            # Mask secret key and session token if required
            if key == 'aws_access_key_id':
                secret_key_id = mask_string(raw_sensitive_value) if (raw_sensitive_value and secret_mask) else raw_sensitive_value
                item_dic[key] = secret_key_id
            elif key == 'aws_secret_access_key':
                secret_key = mask_string(raw_sensitive_value) if (raw_sensitive_value and secret_mask) else raw_sensitive_value
                item_dic[key] = secret_key
            elif key == 'aws_session_token':
                session_token = mask_string(raw_sensitive_value) if (raw_sensitive_value and secret_mask) else raw_sensitive_value
                item_dic[key] = session_token
            else:
                item_dic[key] = raw_sensitive_value
        item_dic['profile_name'] = profile_name
        return item_dic
    except (NoSectionError) as e:
        logger.error(f"Error reading profile '{profile_name}' from credentials file: {e}")
    except (NoOptionError) as e:
        logger.error(f"Profile '{profile_name}' is missing required options: {e}")
    return item_dic

# ----------------------------------------------------------------------------
def get_profile_list(credential_file: str | None = None,
                     secret_mask: bool = False) -> list[dict[str, str]]:
    """
    Get the list of credencials from the AWS credentials file.
    Args:
        credential_file (str | None, optional): Path to the AWS credentials file. 
            If None, the default location (~/.aws/credentials) is used. Defaults to None.
    Returns:
        Optional[list[Dict[str, str]]]: A list of dictionaries containing secret details
            if successful, None otherwise.
    Raises:
        Exception: If there is an error reading the profiles file.
    """
    logger = get_logger()
    credential_file = get_credential_file_path(credential_file)
    if not credential_file.exists():
        raise FileNotFoundError(f"Credential file '{credential_file}' does not exist.")
    config = ConfigParser()
    config.read(credential_file)
    profiles = []
    for section in config.sections():
        item_dic = get_profile_info(profile_name=section,
                                    credential_file=credential_file,
                                    secret_mask=secret_mask,
                                    ctx=config)
        if item_dic:
            profiles.append(item_dic)

    if not profiles:
        logger.info("No valid profiles found in the credentials file.")
    else:
        logger.info(f"Found {len(profiles)} profiles in the credentials file.")
    return profiles

# ----------------------------------------------------------------------------
def update_credentials(profile_name: str,
                       totp_token: str,
                       duration: int = 3600,
                       sts_profile_name: str | None = None,
                       target_key: str | None = None,
                       cred_file: str | os.PathLike | None = None) -> dict[str, str] | None:
    """
    Update the AWS credentials file with new STS tokens.
    """
    logger = get_logger()
    ret = None
    try:
        sts_credentials = get_sts_token(profile_name=profile_name,
                                        totp_token=totp_token,
                                        credential_file=cred_file,
                                        duration_seconds=duration)
        if sts_credentials:
            target_key = profile_name if target_key is None else target_key
            credential_file_path = Path(cred_file) if cred_file else get_credential_file_path()
            updater = CredentialUpdater(credential_path=credential_file_path)
            updater.set_target_tag_name(target_key)
            updater.set_credentials(sts_credentials)
            updater.set_sts_profile_name(sts_profile_name)
            ret = updater.update_credential_file()
            logger.info(f"STS Credentials for profile '{profile_name}' updated successfully.")
            print(f"STS Credentials of profile '{profile_name}' updated successfully.")
            print(f"The temporary credential({ret.get("updated_profile_name", '')}) will expire at: {sts_credentials.get('Expiration', '')}")
        else:
            logger.error("Failed to retrieve STS credentials.")
            raise Exception("Failed to retrieve STS credentials.")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    return ret

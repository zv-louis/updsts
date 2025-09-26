# encoding : utf-8-sig

import asyncio
import traceback
from pathlib import Path
from typing import Annotated, Any

from .logutil import get_logger
from .awsutil import *

#-------------------------------------------------------------------------------------------
async def updsts_update_sts_credential_impl(profile_name: str,
                                            totp_token: str,
                                            cred_file: str | None = None,
                                            duration: int = 3600) -> dict[str, str] | None:
    """
    Implementation for updating AWS STS credentials.

    Args:
        profile_name (str): Profile name to get sts secret key.
        totp_token (str): TOTP token of ARN device.
        cred_file (str | None): Credential file. If None, the default credential file will be used.

    Returns:
        list[dict[str, str]]: List containing the updated credential details.

    Raises:
        ValueError: If any validation fails or operation encounters an error.
    """
    ret = None
    try:
        ret = update_credentials(profile_name=profile_name,
                                 totp_token=totp_token,
                                 cred_file=cred_file,
                                 duration=duration)
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error updating credentials for profile '{profile_name}': {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"Failed to update credentials for profile '{profile_name}': {str(e)}") from e
    return ret


#-------------------------------------------------------------------------------------------
async def updsts_get_credential_info_impl(profile_name: str,
                                    cred_file: str | None = None) -> dict[str, str] | None:
    """
    Implementation for getting AWS STS credential info.

    Args:
        profile_name (str): Profile name to get sts secret key.
        cred_file (str | None): Credential file. If None, the default credential file will be used.

    Returns:
        dict[str, str] | None: Dictionary containing the credential details or None if not found.

    Raises:
        ValueError: If any validation fails or operation encounters an error.
    """
    logger = get_logger()
    logger.info(f"DEBUG: awssts_get_credential_info_impl called with profile_name='{profile_name}', cred_file='{cred_file}'")
    ret = None
    try:
        logger.info(f"DEBUG: About to call get_profile_info")
        ret = get_profile_info(profile_name=profile_name,
                               credential_file=cred_file,
                               secret_mask=True)
        # Clean the return value for logging to avoid newline issues
        safe_ret = {k: v.strip() if isinstance(v, str) else v for k, v in ret.items()} if ret else ret
        logger.info(f"DEBUG: get_profile_info returned: {safe_ret}")
    except Exception as e:
        logger.error(f"Error retrieving credentials for profile '{profile_name}': {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"Failed to retrieve credentials for profile '{profile_name}': {str(e)}") from e
    return ret

#-------------------------------------------------------------------------------------------
async def updsts_get_credential_info_list_impl(cred_file: str | None = None) -> list[dict[str, str]]:
    """
    Implementation for getting list of AWS STS credential info.

    Args:
        cred_file (str | None): Credential file. If None, the default credential file will be used.

    Returns:
        list[dict[str, str]] | None: List containing the credential details.

    Raises:
        ValueError: If any validation fails or operation encounters an error.
    """
    ret = None
    try:
        ret = get_profile_list(credential_file=cred_file,
                               secret_mask=True)
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error retrieving credential list: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"Failed to retrieve credential list: {str(e)}") from e
    return ret
# encoding : utf-8-sig

import asyncio
import traceback

from fastmcp import Client, FastMCP
from fastmcp.client.transports import FastMCPTransport
from typing import Annotated
from pydantic import Field

from .logutil import get_logger
from .mcp_impl import *

# FastMCP instance
mcp = FastMCP("updsts")

# -------------------------------------------------------------------------------------------
# return the FastMCP instance
def get_mcp():
    return mcp

# -------------------------------------------------------------------------------------------
# run the MCP server
def run_as_mcp_server():
    """
    Run the MCP server with stdio transport.
    """
    logger = get_logger()
    try:
        logger.info("Starting awssts MCP server with stdio transport")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Failed to start MCP server: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise

# -------------------------------------------------------------------------------------------
# display the list of tools available in the MCP server
async def list_server_tools(mcp: FastMCP):
    transport = FastMCPTransport(mcp=mcp)
    async with Client(transport=transport) as client:
        result = await client.list_tools()
        for tool in result:
            print(f"------------------------------------------------------------------------------------------------")
            print(f"## '{tool.name}' ##\n") 
            print(f"{tool.description}\n")

# -------------------------------------------------------------------------------------------
# helper for running the test
def disp_tools():
    """
    Display all available MCP tools in the server.
    
    This function runs the list_server_tools function in an event loop.
    """
    logger = get_logger()
    try:
        asyncio.run(list_server_tools(mcp))
        logger.info("Successfully displayed MCP tools list")
    except Exception as e:
        logger.error(f"Failed to display MCP tools: {str(e)}")
        raise

# -------------------------------------------------------------------------------------------
# mcp tool for registering a secret from QR code
@mcp.tool()
async def updsts_update_sts_credential(
        profile_name:  Annotated[str, Field(description="Profile name to get sts secret key.")],
        totp_token: Annotated[str, Field(description="TOTP token of ARN device.")],
        sts_profile_name: Annotated[str | None, Field(description="STS Profile name in the AWS credentials file. If None or empty string, '<profile_name>_sts' will be used.")] = None,
        cred_file: Annotated[str | None, Field(description="Credential file. If None, the default credential file will be used.")] = None,
        duration: Annotated[int, Field(description="Duration seconds of the sts token (default: 3600).")] = 3600,
) -> dict[str, str] | None:
    """
    Get and update AWS credentials for the specified profile using TOTP token.

    This tool obtains temporary STS credentials using MFA authentication and updates
    the AWS credentials file with the new session token and keys.

    Args:
        profile_name (str):
            AWS profile name to update
        totp_token (str):
            TOTP token from the registered MFA device.
            <note>: The registerd totp secret name may be not match with the profile_name.
                    so, check it by using 'updsts_get_credential_info' first to get totp secret name.
                    or prompt user to input the correct TOTP token if there is no totp secret registered.
        sts_profile_name (str | None):
            Specify STS Profile name in the updated AWS credentials file.
            If this is None or a empty string, '<profile_name>_sts' will be used as the default sts profile name. Defaults is None.
        cred_file (str | None):
            Path to AWS credentials file (optional)
            If this is None or a empty string, the default location (~/.aws/credentials) is used. Defaults is None.
        duration (int): Duration seconds of the sts token (default: 3600)

    Returns:
        dict[str, str] | None: Dictionary containing the updated credential details or None if failed
    """
    ret = None
    ret = await updsts_update_sts_credential_impl(profile_name=profile_name,
                                                  totp_token=totp_token,
                                                  sts_profile_name=sts_profile_name,
                                                  cred_file=cred_file,
                                                  duration=duration)
    return ret

# -------------------------------------------------------------------------------------------
# mcp tool for registering a secret from QR code
@mcp.tool()
async def updsts_get_credential_info(
        profile_name:  Annotated[str, Field(description="Profile name to get sts secret key.")],
        cred_file: Annotated[str | None, Field(description="Credential file. If None, the default credential file will be used.")]
) -> dict[str, str] | None:
    """
    Get registerd AWS credential information for the specified profile.

    This tool retrieves the registerd AWS credentials for the specified profile name
    from the AWS credentials file.

    Args:
        profile_name (str):
            AWS profile name to get credentials for
        cred_file (str | None):
            Path to AWS credentials file (optional)
            If this is None or a empty string, the default location (~/.aws/credentials) is used. Defaults is None.
    
    Returns:
        dict[str, str] | None: Dictionary containing the credential details or None if not found
    """
    ret = None
    ret = await updsts_get_credential_info_impl(profile_name=profile_name,
                                                cred_file=cred_file)
    return ret

# -------------------------------------------------------------------------------------------
# mcp tool for registering a secret from QR code
@mcp.tool()
async def updsts_get_credential_info_list(
        cred_file: Annotated[str | None, Field(description="Credential file. If None, the default credential file will be used.")]
) -> list[dict[str, str]]:
    """
    Get registerd AWS credential information list for all profiles.

    This tool retrieves the all AWS credentials in the cred_file.

    Args:
        cred_file (str | None):
            Path to AWS credentials file (optional)
            If this is None or a empty string, the default location (~/.aws/credentials) is used. Defaults is None.
    
    Returns:
        list[dict[str, str]]: The list of the dictionary containing the credential details or empty list if not found.
    """
    ret = []
    ret = await updsts_get_credential_info_list_impl(cred_file=cred_file)
    return ret
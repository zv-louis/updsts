# encoding: utf-8-sig

import os
import sys
from pathlib import Path
from argparse import ArgumentParser

from .logutil import get_logger
from .cmdparam import *
from .awsutil import *
from .mcp_server import *

# ----------------------------------------------------------------------------
def handle_get(args):
    """
    Handle the 'get' command to generate a TOTP token for a given secret name.

    Args:
        args (argparse.Namespace): Parsed command line arguments.
    """
    profile_name = args.profile_name
    totp_token = args.totp_token
    cred_file = args.credential_file if args.credential_file else None
    duration = args.duration if args.duration else 3600
    sts_profile_name = args.sts_profile_name if hasattr(args, 'sts_profile_name') and args.sts_profile_name else None
    target_key = args.target_key if hasattr(args, 'target_key') and args.target_key else None

    update_credentials(profile_name=profile_name,
                       totp_token=totp_token,
                       duration=duration,
                       sts_profile_name=sts_profile_name,
                       target_key=target_key,
                       cred_file=cred_file)

# ----------------------------------------------------------------------------
def handle_list(args):
    """
    Handle the 'list' command to display all registered secrets.

    Args:
        args (argparse.Namespace): Parsed command line arguments.
    """
    credential_file = args.credential_file if args.credential_file else None
    profiles = get_profile_list(credential_file=credential_file,
                                secret_mask=True)
    if not profiles:
        print("No profiles found.")
    else:
        for prof in profiles:
            print(f"Profile Name: {prof['profile_name']}")
            print(f"  Access Key ID       : {prof['aws_access_key_id']}")
            print(f"  Secret Key          : {prof['aws_secret_access_key']}")
            print(f"  Session Token       : {prof['aws_session_token']}") 
            print(f"  Expiration DateTime : {prof['expiration_datetime']}")
            print(f"  MFA Device ARN      : {prof['mfa_device_arn']}")
            print(f"  TOTP Secret Name    : {prof['totp_secret_name']}")
            print()

# ----------------------------------------------------------------------------
def handle_mcp(args):
    """
    Handle the 'mcp' command to run the MCP server.

    Args:
        args (argparse.Namespace): Parsed command line arguments.
    """

    run_mcp = args.mcp_server if args.mcp_server else False
    if run_mcp:
        # If the MCP server flag is set, run the MCP server
        run_as_mcp_server()
        pass
    else:
        # Otherwise, run the MCP server test
        disp_tools()
        pass

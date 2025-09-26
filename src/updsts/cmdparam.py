# encoding: utf-8-sig

import argparse

# ----------------------------------------------------------------------------
def register_sub_get(subparsers,
                     handle_get: callable,
                     parent_parser: argparse.ArgumentParser):
    """
    Register the 'update' subcommand to the argument parser.
    """
    get_parser = subparsers.add_parser(
        'get',
        help='Get/Update new sts token',
        description='Get/Update new sts token.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parent_parser]
    )
    get_parser.add_argument(
        '-n',
        '--profile_name',
        type=str,
        required=True,
        help='Profile name to get sts secret key.'
    )
    get_parser.add_argument(
        '-t',
        '--totp_token',
        type=str,
        required=True,
        help='MFA TOTP token of the user'
    )
    get_parser.add_argument(
        '-d',
        '--duration',
        type=int,
        required=False,
        default=3600,
        help='Duration seconds of the sts token (default: 3600)'
    )
    get_parser.set_defaults(handler=handle_get)
    return subparsers

# ----------------------------------------------------------------------------
def register_sub_list(subparsers,
                      handle_list: callable,
                      parent_parser: argparse.ArgumentParser):
    """
    Register the 'list' subcommand to the argument parser.
    """
    list_parser = subparsers.add_parser(
        'list',
        help='List all profile names',
        description='List all profile names.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parent_parser]
    )
    # Set the function to handle the 'list' command
    list_parser.set_defaults(handler=handle_list)
    return subparsers

# ----------------------------------------------------------------------------
def register_sub_mcp(subparsers,
                     handle_mcp: callable,
                     parent_parser: argparse.ArgumentParser):
    """
    Register the 'mcp' subcommand to the argument parser.
    """
    mcp_parser = subparsers.add_parser(
        'mcp',
        help='Subcommand for mcp functions',
        description='Manage TOTP secrets using MCP tools.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parent_parser]
    )
    mcp_parser.add_argument(
        "--mcp-server",
        action="store_true",
        help="Run as MCP server"
    )
    mcp_parser.set_defaults(handler=handle_mcp)
    return subparsers

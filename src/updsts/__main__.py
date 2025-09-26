# encoding: utf-8-sig

import os
import sys
from pathlib import Path
from argparse import ArgumentParser

from .cmdparam import *
from .cmd_handler import *
from .logutil import get_logger

# ---------------------------------------------------------------------------------------
def main():
    argp = ArgumentParser(prog="updsts",
                          description="Get/Update profile of the aws sts security tokens.")
    # Register common arguments
    common = ArgumentParser(add_help=False)
    common.add_argument(
        '-v',
        '--verbose',
        type=int,
        default=0,
        choices=[0, 1, 2],
        metavar='LEVEL',
        help='Set the verbosity level (0: normal, 1: verbose, 2: debug).'
    )
    user_home = os.path.expanduser("~")
    common.add_argument(
        '-c',
        '--credential_file',
        type=str,
        default=None,
        help='Path to the credetial file where profiles stored. (default: ~/.aws/credentials)'
    )

    subparsers = argp.add_subparsers(dest='command',
                                     help='Available commands')
    # Register subcommands
    register_sub_get(subparsers, handle_get, parent_parser=common)
    register_sub_list(subparsers, handle_list, parent_parser=common)
    register_sub_mcp(subparsers, handle_mcp, parent_parser=common)

    try:
        # Parse the command line arguments
        args = argp.parse_args()
        # If no command is specified, show help
        if args.command is None:
            argp.print_help()
        else:
            # Initialize the logger with the specified verbosity level
            _ = get_logger(verbose_level=args.verbose)
            # Execute the handler for the specified command
            if hasattr(args, 'handler'):
                args.handler(args)
            else:
                argp.print_help()

    except FileNotFoundError:
        print("Error: Secrets file not found. Please ensure the file exists or specify a valid path.")
    except PermissionError:
        print("Error: Permission denied when accessing the credential file. Check your permissions.")
    except KeyError as e:
        print(f"Error: Profile name '{e}' is not found in the credential file. Please check the profile name.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Exception: {e}")

# ---------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()

# updsts

A simple CUI-based AWS STS credential management tool and local MCP server for AWS multi-factor authentication

English | [日本語](README_ja.md)

<!-- TOC tocDepth:2..3 chapterDepth:2..6 -->

- [Overview](#overview)
- [Features](#features)
- [Runtime Environment](#runtime-environment)
- [Building Module Package](#building-module-package)
- [Usage](#usage)
  - [Running module directly from project](#running-module-directly-from-project)
  - [Installing module package to Python environment](#installing-module-package-to-python-environment)
  - [Registering as MCP Server](#registering-as-mcp-server)
- [CUI Tool Command Options](#cui-tool-command-options)
  - [Common Options](#common-options)
  - [get Command](#get-command)
  - [list Command](#list-command)
  - [mcp Command](#mcp-command)
- [AWS Credentials File](#aws-credentials-file)
  - [AWS Credentials File Format](#aws-credentials-file-format)
  - [AWS Credentials File Storage Location](#aws-credentials-file-storage-location)
- [Available MCP Tools](#available-mcp-tools)
  - [`updsts_update_sts_credential`](#updsts_update_sts_credential)
  - [`updsts_get_credential_info`](#updsts_get_credential_info)
  - [`updsts_get_credential_info_list`](#updsts_get_credential_info_list)
- [Security Notes](#security-notes)
- [License](#license)

<!-- /TOC -->

## Overview

updsts is a command-line tool that retrieves AWS STS (Security Token Service) credentials from existing AWS credential (.aws/credentials) file information and automatically reflects them in the credential file.  
It also has local MCP server functionality that automatically updates temporary credential information in AWS credential files, enabling operation through common Agent tools.

## Features

- Obtain temporary AWS STS credentials using MFA authentication
- Automatically update AWS credentials file with new session tokens
- Support for TOTP-based MFA devices
- List all AWS profiles in credentials file
- Preserve existing credential profiles safely
- Can be operated from common Agent tools when functioning as a local MCP server
- Support for proxy environments

## Runtime Environment

This project uses uv as the package manager.  
Using uv allows you to automatically reproduce the runtime environment.  

For uv installation, see here:

- [Installing uv](https://docs.astral.sh/uv/getting-started/installation/)

```bash
# Assuming the project is cloned in the updsts directory
cd updsts
# Install dependencies and run. Display help
uv run -m updsts --help
```

## Building Module Package

To create a module package, run the following uv command.  
The generated package will be saved in the dist directory.  
The generated package can be installed with pip, etc.

```bash
# Assuming the project is cloned in the updsts directory
cd updsts 
# Create package
uv build
```

## Usage

### Running module directly from project

You can run directly from the project directory using uv.  

When running from outside the project directory,
specify the project directory with the `--directory` option.

```bash
# Using uv (from project directory)
# Get and update STS credentials for a profile
uv run [--directory {project_dir}] -m updsts get -n "profile_name" -t "123456"

# List all AWS profiles
uv run [--directory {project_dir}] -m updsts list

# Start as MCP server
uv run [--directory {project_dir}] -m updsts mcp --mcp-server
```

### Installing module package to Python environment

You can also install and use the built module package with the pip command.

```bash
# To install with pip, run the following command
# Install module package
pip install updsts-<version>.tar.gz
# Or install wheel file
pip install updsts-<version>-py3-none-any.whl

# To install with uv, run the following command
uv pip install updsts-<version>.tar.gz
# Or install wheel file
uv pip install updsts-<version>-py3-none-any.whl
```

After installation, you can run commands as follows:

```bash
# Get and update STS credentials for a profile
python -m updsts get -n "profile_name" -t "123456"
# List all AWS profiles
python -m updsts list
# Start as MCP server
python -m updsts mcp --mcp-server
```

### Registering as MCP Server

By registering as an MCP server, you can operate updsts from common Agent tools.

```json
{
  // Example configuration for registering as MCP server
  //
  // (Note) 
  // Registration keys may differ depending on the Agent tool used,
  // so please refer to the manual of each Agent tool you use for detailed procedures.
  "mcpServers" {
    // Configuration for starting updsts as MCP server using uv
    "updsts-uv": {
      "type": "stdio",
      "command": "uv",
      "args": [
          "run",
          "--directory",
          "${path_to_this_project}",
          "-m",
          "updsts",
          "mcp",
          "--mcp-server"
      ],
      "env": {},
    },
    // Configuration for starting when module is installed in Python environment
    "updsts-py": {
      "type": "stdio",
      "command": "python",
      "args": [
          "-m",
          "updsts",
          "mcp",
          "--mcp-server"
      ],
      "env": {}
    }
  }
}
```

## CUI Tool Command Options

### Common Options

- `-v, --verbose LEVEL`: Set output information detail level (0: normal, 1: verbose, 2: debug)
- `-c, --credential-file FILE`: Path to the AWS credentials file (default: ~/.aws/credentials)

### get Command

Get and update STS credentials for the specified AWS profile.

```bash
uv run [--directory {project_dir}] -m updsts get -n <profile_name> -t <totp_token>
```

- `-n, --profile`: AWS profile name to get STS token (required)
- `-t, --totp-token`: TOTP token generated by MFA device (required)
- `-sn, --sts-profile-name`: STS profile name to generate in AWS credentials file (optional, default: AWS profile name + "_sts")
- `-d, --duration`: Token duration in seconds (optional, default: 3600)
- `-c, --credential-file`: Path to credentials file (optional, default: ~/.aws/credentials)

### list Command

Display all AWS profiles in the credentials file.

```bash
uv run [--directory {project_dir}] -m updsts list
```

### mcp Command

Start the module as a local MCP server.  
You can operate updsts using Agent tools.

```bash
uv run [--directory {project_dir}] -m updsts mcp --mcp-server
```

If the `--mcp-server` option is not specified, it will output the MCP tool list.

```bash
uv run [--directory {project_dir}] -m updsts mcp
```

## AWS Credentials File

### AWS Credentials File Format

updsts works with standard AWS CLI credentials file format.  
It preserves existing profiles while updating only the specified sections.  

Example credentials file:

```ini
[default]
# Access Key ID (required)
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
# Secret Access Key (required)
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLE
# IAM user's MFA device ARN (required. User must add this)
mfa_device_arn = arn:aws:iam::123456789012:mfa/user 
# TOTP secret name managed by mktotp mcp server (optional. User can add this)
# If this is configured and the `mktotp` mcp server is available, Agent will auto-generate and use TOTP token.
totp_secret_name = my_totp_secret 

# The section enclosed by the following tags is automatically created/updated by updsts.
# ${{{ key=<profile name that requested STS> [auto update by updsts]
[default_sts]
aws_access_key_id = ASIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYtempKEY
aws_session_token = IQoJb3JpZ2luX2VjE...
expiration_datetime = 2025-10-05T15:30:00+09:00
# $}}} [auto update by updsts]
```

updsts automatically manages sections between special tags while leaving other profiles intact.  
Tags are automatically added during the first execution, so there is no need to add them manually.

### AWS Credentials File Storage Location

By default, AWS credentials are stored in the following location.  
※ This is the same file used by the AWS CLI.

```text
~/.aws/credentials
```

You can specify a different location with the `-c` option.

## Available MCP Tools

When started as an MCP server, the following tools are available from Agent tools.

### `updsts_update_sts_credential`

Get and update AWS credentials for the specified profile using TOTP token.

- Parameters:
  - `profile_name` (str): AWS profile name to update (required)
  - `totp_token` (str): TOTP token from MFA device (required)
  - `sts_profile_name` (str | None): STS profile name to create in AWS credentials file (optional)
    - If None or empty string, `<profile_name>_sts` will be used (default: None)
  - `cred_file` (str | None): Path to credentials file (optional)
    - If None or empty string, default location (~/.aws/credentials) is used (default: None)
  - `duration` (int): STS token duration in seconds (optional, default: 3600)
- Returns (dict[str, str] | None): Dictionary containing updated credential details or None if failed

### `updsts_get_credential_info`

Get AWS credential information for the specified profile.  
However, for security reasons, `aws_secret_access_key` and `aws_session_token` are returned masked.

- Parameters:
  - `profile_name` (str): AWS profile name to retrieve (required)
  - `cred_file` (str | None): Path to credentials file (optional)
    - If None or empty string, default location (~/.aws/credentials) is used (default: None)
- Returns (dict[str, str] | None): Dictionary containing credential details or None if not found

### `updsts_get_credential_info_list`

Get AWS credential information for all profiles in the credentials file.  
However, for security reasons, `aws_secret_access_key` and `aws_session_token` are returned masked.

- Parameters:
  - `cred_file` (str | None): Path to credentials file (optional)
    - If None or empty string, default location (~/.aws/credentials) is used (default: None)
- Returns (list[dict[str, str]]): List of dictionaries containing credential details or empty list if no profiles found

## Security Notes

- AWS credentials files contain sensitive information, so protect them with appropriate permission settings (recommended: 600)

## License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.

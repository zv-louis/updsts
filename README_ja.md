# updsts

AWSのSTS認証情報をcredentalファイルへ反映させるシンプルなCUIツールとローカルMCPサーバー

[English](README.md) | 日本語

<!-- TOC tocDepth:2..3 chapterDepth:2..6 -->

- [1. 概要](#1-概要)
- [2. 特徴](#2-特徴)
- [3. 実行環境](#3-実行環境)
- [4. インストール/使用方法](#4-インストール使用方法)
- [5. MCPサーバーとして登録する](#5-mcpサーバーとして登録する)
- [6. CUIツール コマンドオプション](#6-cuiツール-コマンドオプション)
  - [6-1. 共通オプション](#6-1-共通オプション)
  - [6-2. `get` コマンド](#6-2-get-コマンド)
  - [6-3. `list` コマンド](#6-3-list-コマンド)
  - [6-4. `mcp` コマンド](#6-4-mcp-コマンド)
- [7. AWS認証情報ファイル](#7-aws認証情報ファイル)
  - [7-1. AWS認証情報ファイル形式](#7-1-aws認証情報ファイル形式)
  - [7-2. AWS認証情報ファイルの場所](#7-2-aws認証情報ファイルの場所)
- [8. 提供される MCP tool 一覧](#8-提供される-mcp-tool-一覧)
  - [`updsts_update_sts_credential`](#updsts_update_sts_credential)
  - [`updsts_get_credential_info`](#updsts_get_credential_info)
  - [`updsts_get_credential_info_list`](#updsts_get_credential_info_list)
- [9. セキュリティに関する注意事項](#9-セキュリティに関する注意事項)
- [10. ライセンス](#10-ライセンス)

<!-- /TOC -->

## 1. 概要

updsts は 既存のAWS credential(.aws/credentails)ファイルに登録されている認証情報から AWS STS（Security Token Service）認証情報を取得し,credentialファイルへ自動で反映するコマンドラインツールです。  
AWS認証情報ファイル内の一時的な認証情報を自動的に更新するローカルMCPサーバーの機能も持っていて、一般的なエージェントツールからの操作も可能です。

## 2. 特徴

- MFA認証を使用したAWS STS一時認証情報の取得
- AWS認証情報ファイルの新しいセッショントークンによる自動更新
- TOTPベースのMFAデバイスのサポート
- 認証情報ファイル内のすべてのAWSプロファイルの一覧表示
- 既存の認証情報プロファイルの安全な保護
- ローカルMCPサーバーとして機能し、一般的なエージェントツールからの操作が可能
　(もちろん、secret key, session token等の機密情報はLLMに送信されないように考慮されています)
- プロキシ環境のサポート

## 3. 実行環境

このプロジェクトではパッケージマネージャーとしてuvを使用しています。  
uvを使用することで実行環境を自動的に再現できます。  

uvのインストールについてはこちらを参照してください:

- [Installing uv](https://docs.astral.sh/uv/getting-started/installation/)

## 4. インストール/使用方法

uv環境にインストールして使用します.  

```bash
# gitリポジトリから直接インストール
uv tool install git+{リポジトリのURL}
```

インストール後は、toolとして `updsts` コマンドを直接使用できます.  

```bash
updsts --help
```

## 5. MCPサーバーとして登録する

MCPサーバーとして登録することで、一般的なエージェントツールから updsts を操作できます。

```json
{
  // MCPサーバーとして登録する設定例
  //
  // (注意) 
  // 登録キーは使用するエージェントツールによって異なる場合があるため、
  // 詳細な手順については使用するエージェントツールのマニュアルを参照してください。
  "mcpServers" {
    // uvを使用してupdsts をMCPサーバーとして起動する設定
    "updsts-uv": {
      "type": "stdio",
      "command": "updsts",
      "args": [
          "mcp",
          "--mcp-server"
      ],
      "env": {},
    }
  }
}
```

## 6. CUIツール コマンドオプション

### 6-1. 共通オプション

- `-v, --verbose LEVEL`: 出力情報の詳細レベルを設定 (0: 通常, 1: 詳細, 2: デバッグ)
- `-c, --credential-file FILE`: AWS認証情報ファイルのパス (デフォルト: ~/.aws/credentials)

### 6-2. `get` コマンド

指定されたAWSプロファイルのSTS認証情報を取得・更新します。

```bash
updsts get -n <profile_name> -t <totp_token>
```

- `-n, --profile`: STSトークンを取得するAWSプロファイル名 (必須)
- `-t, --totp-token`: MFAデバイスで生成されたTOTPトークン (必須)
- `-sn, --sts-profile-name`: AWS認証情報ファイル内に生成するSTSプロファイル名 (オプション、デフォルト: AWSプロファイル名 + "_sts")
- `-d, --duration`: トークン持続時間（秒）(オプション、デフォルト: 3600)
- `-c, --credential-file`: 認証情報ファイルのパス. (オプション、デフォルト: ~/.aws/credentials)

### 6-3. `list` コマンド

認証情報ファイル内のすべてのAWSプロファイルを表示します。

```bash
updsts list
```

### 6-4. `mcp` コマンド

モジュールをローカルMCPサーバーとして起動します。  
エージェントツールを使用してupdsts を操作できます。

```bash
updsts mcp --mcp-server
```

`--mcp-server` オプションが指定されていない場合、MCPツールリストを出力します。

```bash
updsts mcp
```

## 7. AWS認証情報ファイル

### 7-1. AWS認証情報ファイル形式

updsts は AWS CLI の標準的なAWS認証情報ファイル形式を操作します。  
既存のプロファイルを保持しながら、指定されたセクションのみを更新します。  

認証情報ファイルの例:  

```ini
[default]
# アクセスキーID (必須)
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
# シークレットアクセスキー (必須)
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLE
# IAMユーザーのMFAデバイスARN (必須. ユーザが追加してください)
mfa_device_arn = arn:aws:iam::123456789012:mfa/user 
# mktotp mcpサーバで管理されているTOTPシークレット名 (任意. ユーザが追加してください)
# この項目が設定してあれば、Agentは `mktotp` mcpサーバー が利用可能であれば、TOTPトークンを自動生成して使用します.
totp_secret_name = my_totp_secret 

# 以下のタグに囲まれた部分が updsts によって自動的に作成/更新されます.
# ${{{ key=<STSをリクエストしたプロファイル名> [auto update by updsts]
[default_sts]
aws_access_key_id = ASIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYtempKEY
aws_session_token = IQoJb3JpZ2luX2VjE...
expiration_datetime = 2025-10-05T15:30:00+09:00
# $}}} [auto update by updsts]
```

updstsは特別なタグ間のセクションを自動的に管理し、他のプロファイルはそのまま保持します.  
タグは初回の実行時に自動的に追加されるため、手動で追加する必要はありません。

### 7-2. AWS認証情報ファイルの場所

デフォルトでは、AWS認証情報は以下の場所に保存されます.  
※ aws cli が使用するファイルと同じです.  

```text
~/.aws/credentials
```

`-c` オプションで別の場所のファイルを指定できます.  

## 8. 提供される MCP tool 一覧

MCPサーバーとして起動した場合、以下のtoolがAgentから利用可能です.

### `updsts_update_sts_credential`

指定されたAWSプロファイルのSTS認証情報を取得し、credentialファイル内にstsのプロファイルを作成/更新します。

- パラメータ:
  - `profile_name` (str): 更新するAWSプロファイル名 (必須)
  - `totp_token` (str): MFAデバイスからのTOTPトークン (必須)
  - `sts_profile_name` (str | None): AWS認証情報ファイル内に作成するSTSプロファイル名 (オプション)
    - Noneまたは空文字列の場合、`<profile_name>_sts`が使用されます (デフォルト: None)
  - `cred_file` (str | None): 認証情報ファイルのパス (オプション)
    - Noneまたは空文字列の場合、デフォルトの場所(~/.aws/credentials)が使用されます (デフォルト: None)
  - `duration` (int): STSトークンの有効期間（秒）(オプション、デフォルト: 3600)
- 戻り値 (dict[str, str] | None): 更新された認証情報の詳細を含む辞書、または失敗時はNone

### `updsts_get_credential_info`

プロファイル名を指定して、credentialファイル内に存在するAWSプロファイルの情報を取得します.  
ただし、セキュリティ上の理由から、`aws_secret_access_key` , `aws_session_token` はマスクした情報が返却されます.  

- パラメータ:
  - `profile_name` (str): 取得するAWSプロファイル名 (必須)
  - `cred_file` (str | None): 認証情報ファイルのパス (オプション)
    - Noneまたは空文字列の場合、デフォルトの場所(~/.aws/credentials)が使用されます (デフォルト: None)
- 戻り値 (dict[str, str] | None): 認証情報の詳細を含む辞書、または見つからない場合はNone

### `updsts_get_credential_info_list`

credentialファイル内のすべてのAWSプロファイルの情報を取得します.  
ただし、セキュリティ上の理由から、`aws_secret_access_key` , `aws_session_token` はマスクした情報が返却されます.  

- パラメータ:
  - `cred_file` (str | None): 認証情報ファイルのパス (オプション)
    - Noneまたは空文字列の場合、デフォルトの場所(~/.aws/credentials)が使用されます (デフォルト: None)
- 戻り値 (list[dict[str, str]]): 認証情報の詳細を含む辞書のリスト、またはプロファイルが見つからない場合は空リスト

## 9. セキュリティに関する注意事項

- AWS認証情報ファイルには機密情報が含まれているため、適切な権限設定で保護してください (推奨: 600)

## 10. ライセンス

このプロジェクトはMIT ライセンスの下でライセンスされています。  
詳細については[LICENSE](LICENSE)ファイルを参照してください。  

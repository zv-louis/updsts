# updsts

AWSのSTS認証情報を認証情報ファイルへ反映させるシンプルなCUIツールとローカルMCPサーバー

[English](README.md) | 日本語

<!-- TOC tocDepth:2..3 chapterDepth:2..6 -->

- [updsts](#updsts)
  - [1. 概要](#1-概要)
  - [2. 特徴](#2-特徴)
  - [3. 実行環境](#3-実行環境)
  - [4. インストール/使用方法](#4-インストール使用方法)
    - [4-1. uv tool としてインストールする](#4-1-uv-tool-としてインストールする)
    - [4-2. uvx で利用する](#4-2-uvx-で利用する)
    - [4-3. MCPサーバーとして登録する](#4-3-mcpサーバーとして登録する)
    - [4-4. Claude PluginとしてMCPサーバーをインストールする](#4-4-claude-pluginとしてmcpサーバーをインストールする)
  - [5. CUIツール コマンドオプション](#5-cuiツール-コマンドオプション)
    - [5-1. 共通オプション](#5-1-共通オプション)
    - [5-2. `get` コマンド](#5-2-get-コマンド)
    - [5-3. `list` コマンド](#5-3-list-コマンド)
    - [5-4. `mcp` コマンド](#5-4-mcp-コマンド)
  - [6. 認証情報ファイル](#6-認証情報ファイル)
    - [6-1. 認証情報ファイル形式](#6-1-認証情報ファイル形式)
    - [6-2. 認証情報ファイルの場所](#6-2-認証情報ファイルの場所)
  - [7. 提供される MCPツール一覧](#7-提供される-mcpツール一覧)
    - [`updsts_update_sts_credential`](#updsts_update_sts_credential)
    - [`updsts_get_credential_info`](#updsts_get_credential_info)
    - [`updsts_get_credential_info_list`](#updsts_get_credential_info_list)
  - [8. セキュリティに関する注意事項](#8-セキュリティに関する注意事項)
  - [9. ライセンス](#9-ライセンス)

<!-- /TOC -->

## 1. 概要

updsts は、既存の認証情報ファイル（~/.aws/credentials）に登録されている認証情報から AWS STS（Security Token Service）認証情報を取得し、  
独立したプロファイルとして認証情報ファイルに反映します。  
ローカルMCPサーバーとしても動作し、エージェントツールから STS プロファイルを参照・更新できます。  
これにより、STS 認証情報を使う AWS 操作を自動化しやすくなります。

## 2. 特徴

- MFA認証を使用したAWS STS一時認証情報の取得
- 認証情報ファイル内のSTS用プロファイルの更新
- TOTPベースのMFAデバイスのサポート
- 認証情報ファイル内のすべてのAWSプロファイルの一覧表示（機密情報はマスク）
- 更新対象以外のプロファイルをそのまま保持
- ローカルMCPサーバーとして機能し、一般的なエージェントツールからの操作が可能  
  （secret key や session token などの機密情報はマスクして返し、LLMには渡しません）
- プロキシ環境のサポート

## 3. 実行環境

このプロジェクトではパッケージマネージャーとしてuvを使用しています。  
uvを使用することで実行環境を自動的に再現できます。  

uvのインストールについてはこちらを参照してください:

- [Installing uv](https://docs.astral.sh/uv/getting-started/installation/)

## 4. インストール/使用方法

uv または uvx で利用します。  

### 4-1. uv tool としてインストールする

```bash
# PyPIからインストール
uv tool install updsts
```

インストール後は、ツールとして `updsts` コマンドを直接使用できます。  

```bash
updsts --help
```

### 4-2. uvx で利用する

インストールせずに、uvx コマンドで PyPI から直接 updsts を起動します。

```bash
uvx updsts --help
# 常に最新版を使うには @latest を付ける
uvx updsts@latest --help
```

### 4-3. MCPサーバーとして登録する

MCPサーバーとして登録することで、一般的なエージェントツールから updsts を操作できます。  
MCPサーバーの登録手順は、使っているエージェントツールのマニュアルを参照してください。

```jsonc
{
  // MCPサーバーとして登録する設定例
  //
  // (注意)
  // エージェントツールによって登録キーが異なります。
  "mcpServers": {
    // uvx で updsts をMCPサーバーとして起動する設定
    "updsts-uv": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "updsts@latest", // バージョンを固定する場合は、"updsts@0.9.2" のように指定する
        "mcp",
        "--mcp-server"
      ],
      "env": {}
    }
  }
}
```

### 4-4. Claude PluginとしてMCPサーバーをインストールする

updsts は Claude Plugin としてインストールできます。  

```bash
# マーケットプレイスを追加
/plugin marketplace add zv-louis/zv-plugin-marketplace
# マーケットプレイスからインストール
/plugin install updsts-mcp@zv-plugins
```

## 5. CUIツール コマンドオプション

### 5-1. 共通オプション

- `-v, --verbose LEVEL`: 出力情報の詳細レベルを設定（0: 通常, 1: 詳細, 2: デバッグ）
- `-c, --credential_file FILE`: 認証情報ファイルのパス（デフォルト: ~/.aws/credentials）

### 5-2. `get` コマンド

指定されたAWSプロファイルのSTS認証情報を取得・更新します。

```bash
updsts get -n <profile_name> -t <totp_token>
```

- `-n, --profile_name`: STSトークンを取得するAWSプロファイル名（必須）
- `-t, --totp_token`: MFAデバイスで生成されたTOTPトークン（必須）
- `-sn, --sts_profile_name`: 認証情報ファイル内に生成するSTSプロファイル名（オプション、デフォルト: AWSプロファイル名 + "_sts"）
- `-d, --duration`: トークン持続時間（秒）（オプション、デフォルト: 3600）
- `-c, --credential_file`: 認証情報ファイルのパス（オプション、デフォルト: ~/.aws/credentials）

### 5-3. `list` コマンド

認証情報ファイル内のすべてのAWSプロファイルを表示します。  
機密情報（`aws_access_key_id`, `aws_secret_access_key`, `aws_session_token`）はマスクして表示されます。

```bash
updsts list
```

### 5-4. `mcp` コマンド

updsts をローカルMCPサーバーとして起動します。  
エージェントツールから updsts を操作できます。

```bash
updsts mcp --mcp-server
```

`--mcp-server` オプションが指定されていない場合、MCPツールリストを出力します。

```bash
updsts mcp
```

## 6. 認証情報ファイル

### 6-1. 認証情報ファイル形式

updsts は AWS CLI の標準的な認証情報ファイル形式を操作します。  
既存のプロファイルを保持しながら、指定されたセクションのみを更新します。  

認証情報ファイルの例:  

```ini
[default]
# アクセスキーID (必須)
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
# シークレットアクセスキー (必須)
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLE
# IAMユーザーのMFAデバイスARN (必須。ユーザーが追加してください)
mfa_device_arn = arn:aws:iam::123456789012:mfa/user 
# mktotp MCPサーバーで管理されているTOTPシークレット名 (任意。ユーザーが追加してください)
# この項目が設定されていて `mktotp` MCPサーバーが利用可能な場合、エージェントは TOTPトークンを自動生成して使用します。
totp_secret_name = my_totp_secret 

# 以下のタグに囲まれた部分が updsts によって自動的に作成/更新されます。
# ${{{ key=<STSをリクエストしたプロファイル名> [auto update by updsts]
[default_sts]
aws_access_key_id = ASIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYtempKEY
aws_session_token = IQoJb3JpZ2luX2VjE...
expiration_datetime = 2025-10-05T15:30:00+09:00
# $}}} [auto update by updsts]
```

updsts は特別なタグ間のセクションを自動的に管理し、他のプロファイルはそのまま保持します。  
タグは初回の実行時に自動的に追加されるため、手動で追加する必要はありません。

### 6-2. 認証情報ファイルの場所

デフォルトでは、AWS認証情報は以下の場所に保存されます。  
※ aws cli が使用するファイルと同じです。  

```text
~/.aws/credentials
```

`-c` オプションで別の場所のファイルを指定できます。  

## 7. 提供される MCPツール一覧

MCPサーバーとして起動した場合、以下のツールがエージェントから利用可能です。

### `updsts_update_sts_credential`

指定されたAWSプロファイルのSTS認証情報を取得し、認証情報ファイル内にSTSのプロファイルを作成/更新します。

- パラメータ:
  - `profile_name`（`str`）: 更新するAWSプロファイル名（必須）
  - `totp_token`（`str`）: MFAデバイスからのTOTPトークン（必須）
  - `sts_profile_name`（`str`）: 認証情報ファイル内に作成するSTSプロファイル名（オプション）
    - 空文字列の場合、`<profile_name>_sts` が使用されます（デフォルト: 空文字列）
  - `cred_file`（`str`）: 認証情報ファイルのパス（オプション）
    - 空文字列の場合、デフォルトの場所（~/.aws/credentials）が使用されます（デフォルト: 空文字列）
  - `duration`（`int`）: STSトークンの有効期間（秒）（オプション、デフォルト: 3600）
- 戻り値（`dict[str, str]`）: 更新結果を含む辞書
  - `updated_profile_name`: 更新したSTSプロファイル名
  - `aws_access_key_id`: 取得したSTS認証情報のアクセスキーID（マスク済み）
  - `aws_token_expiration`: STS認証情報の有効期限（ローカルタイムゾーンのISO 8601形式）
  - シークレットアクセスキーとセッショントークンは返却されません
  - 失敗時は戻り値ではなく、エラー（`ValueError`）として通知されます

### `updsts_get_credential_info`

プロファイル名を指定して、認証情報ファイル内に存在するAWSプロファイルの情報を取得します。  
ただし、セキュリティ上の理由から、`aws_access_key_id`, `aws_secret_access_key`, `aws_session_token` はマスクした情報が返却されます。  

- パラメータ:
  - `profile_name`（`str`）: 取得するAWSプロファイル名（必須）
  - `cred_file`（`str`）: 認証情報ファイルのパス（オプション）
    - 空文字列の場合、デフォルトの場所（~/.aws/credentials）が使用されます（デフォルト: 空文字列）
- 戻り値（`dict[str, str] | None`）: 認証情報の詳細を含む辞書、または見つからない場合は `None`

### `updsts_get_credential_info_list`

認証情報ファイル内のすべてのAWSプロファイルについて、情報を取得します。  
ただし、セキュリティ上の理由から、`aws_access_key_id`, `aws_secret_access_key`, `aws_session_token` はマスクした情報が返却されます。  

- パラメータ:
  - `cred_file`（`str`）: 認証情報ファイルのパス（オプション）
    - 空文字列の場合、デフォルトの場所（~/.aws/credentials）が使用されます（デフォルト: 空文字列）
- 戻り値（`list[dict[str, str]]`）: 認証情報の詳細を含む辞書のリスト、またはプロファイルが見つからない場合は空リスト

## 8. セキュリティに関する注意事項

- 認証情報ファイルには機密情報が含まれているため、適切な権限設定で保護してください（推奨: 600）

## 9. ライセンス

このプロジェクトはMIT ライセンスの下でライセンスされています。  
詳細については[LICENSE](LICENSE)ファイルを参照してください。  

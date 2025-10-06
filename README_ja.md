# updsts

AWSのSTS認証情報をcredentalファイルへ反映させるシンプルなCUIツールとローカルMCPサーバー

[English](README.md) | 日本語

<!-- TOC tocDepth:2..3 chapterDepth:2..6 -->

- [概要](#概要)
- [特徴](#特徴)
- [実行環境](#実行環境)
- [モジュールパッケージのビルド](#モジュールパッケージのビルド)
- [使用方法](#使用方法)
  - [プロジェクトから直接実行](#プロジェクトから直接実行)
  - [モジュールパッケージをPython環境にインストール](#モジュールパッケージをpython環境にインストール)
  - [MCPサーバーとして登録](#mcpサーバーとして登録)
- [CUIツール コマンドオプション](#cuiツール-コマンドオプション)
  - [共通オプション](#共通オプション)
  - [get コマンド](#get-コマンド)
  - [list コマンド](#list-コマンド)
  - [mcp コマンド](#mcp-コマンド)
- [AWS認証情報ファイル](#aws認証情報ファイル)
  - [AWS認証情報ファイル形式](#aws認証情報ファイル形式)
  - [AWS認証情報ファイルの場所](#aws認証情報ファイルの場所)
- [提供される MCP tool 一覧](#提供される-mcp-tool-一覧)
  - [`updsts_update_sts_credential`](#updsts_update_sts_credential)
  - [`updsts_get_credential_info`](#updsts_get_credential_info)
  - [`updsts_get_credential_info_list`](#updsts_get_credential_info_list)
- [セキュリティに関する注意事項](#セキュリティに関する注意事項)
- [ライセンス](#ライセンス)

<!-- /TOC -->

## 概要

updsts は 既存のAWS credential(.aws/credentails)ファイルに登録されている認証情報から AWS STS（Security Token Service）認証情報を取得し,credentialファイルへ自動で反映するコマンドラインツールです。  
AWS認証情報ファイル内の一時的な認証情報を自動的に更新するローカルMCPサーバーの機能も持っていて、一般的なエージェントツールからの操作も可能です。

## 特徴

- MFA認証を使用したAWS STS一時認証情報の取得
- AWS認証情報ファイルの新しいセッショントークンによる自動更新
- TOTPベースのMFAデバイスのサポート
- 認証情報ファイル内のすべてのAWSプロファイルの一覧表示
- 既存の認証情報プロファイルの安全な保護
- ローカルMCPサーバーとして機能し、一般的なエージェントツールからの操作が可能
- プロキシ環境のサポート

## 実行環境

このプロジェクトではパッケージマネージャーとしてuvを使用しています。  
uvを使用することで実行環境を自動的に再現できます。  

uvのインストールについてはこちらを参照してください:

- [Installing uv](https://docs.astral.sh/uv/getting-started/installation/)

```bash
# updsts ディレクトリにプロジェクトがクローンされていることを前提
cd updsts
# 依存関係をインストールして実行。ヘルプを表示
uv run -m updsts --help
```

## モジュールパッケージのビルド

モジュールパッケージを作成するには、以下のuvコマンドを実行します。  
生成されたパッケージはdistディレクトリに保存されます。  
生成されたパッケージはpip等でインストールできます。

```bash
# updsts ディレクトリにプロジェクトがクローンされていることを前提
cd updsts
# パッケージ作成
uv build
```

## 使用方法

### プロジェクトから直接実行

uvを使用してプロジェクトディレクトリから直接実行できます。  

プロジェクトディレクトリ外から実行する場合は、
`--directory` オプションでプロジェクトディレクトリを指定してください。

```bash
# uvを使用（プロジェクトディレクトリから）
# プロファイルのSTS認証情報を取得・更新
uv run [--directory {project_dir}] -m updsts get -n "profile_name" -t "123456"

# 全AWSプロファイルを一覧表示
uv run [--directory {project_dir}] -m updsts list

# MCPサーバーとして起動
uv run [--directory {project_dir}] -m updsts mcp --mcp-server
```

### モジュールパッケージをPython環境にインストール

ビルドしたモジュールパッケージをpipコマンドでインストールして使用することも可能です。

```bash
# pipでインストールする場合は以下のコマンドを実行
# モジュールパッケージをインストール
python -m pip install updsts-<version>.tar.gz
# またはwheelファイルをインストール
python -m pip pip install updsts-<version>-py3-none-any.whl

# uvでインストールする場合は以下のコマンドを実行
uv pip install updsts-<version>.tar.gz
# またはwheelファイルをインストール
uv pip install updsts-<version>-py3-none-any.whl
```

インストール後は以下のようにコマンドを実行できます:

```bash
# プロファイルのSTS認証情報を取得・更新
python -m updsts get -n "profile_name" -t "123456"
# 全AWSプロファイルを一覧表示
python -m updsts list
# MCPサーバーとして起動
python -m updsts mcp --mcp-server
```

### MCPサーバーとして登録

MCPサーバーとして登録することで、一般的なエージェントツールからupdsts を操作できます。

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
    // モジュールがPython環境にインストールされている場合の起動設定
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

## CUIツール コマンドオプション

### 共通オプション

- `-v, --verbose LEVEL`: 出力情報の詳細レベルを設定 (0: 通常, 1: 詳細, 2: デバッグ)
- `-c, --credential-file FILE`: AWS認証情報ファイルのパス (デフォルト: ~/.aws/credentials)

### get コマンド

指定されたAWSプロファイルのSTS認証情報を取得・更新します。

```bash
uv run [--directory {project_dir}] -m updsts get -n <profile_name> -t <totp_token>
```

- `-n, --profile`: STSトークンを取得するAWSプロファイル名 (必須)
- `-t, --totp-token`: MFAデバイスで生成されたTOTPトークン (必須)
- `-sn, --sts-profile-name`: AWS認証情報ファイル内に生成するSTSプロファイル名 (オプション、デフォルト: AWSプロファイル名 + "_sts")
- `-d, --duration`: トークン持続時間（秒）(オプション、デフォルト: 3600)
- `-c, --credential-file`: 認証情報ファイルのパス. (オプション、デフォルト: ~/.aws/credentials)

### list コマンド

認証情報ファイル内のすべてのAWSプロファイルを表示します。

```bash
uv run [--directory {project_dir}] -m updsts list
```

### mcp コマンド

モジュールをローカルMCPサーバーとして起動します。  
エージェントツールを使用してupdsts を操作できます。

```bash
uv run [--directory {project_dir}] -m updsts mcp --mcp-server
```

`--mcp-server` オプションが指定されていない場合、MCPツールリストを出力します。

```bash
uv run [--directory {project_dir}] -m updsts mcp
```

## AWS認証情報ファイル

### AWS認証情報ファイル形式

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

### AWS認証情報ファイルの場所

デフォルトでは、AWS認証情報は以下の場所に保存されます.  
※ aws cli が使用するファイルと同じです.  

```text
~/.aws/credentials
```

`-c` オプションで別の場所のファイルを指定できます.  

## 提供される MCP tool 一覧

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

## セキュリティに関する注意事項

- AWS認証情報ファイルには機密情報が含まれているため、適切な権限設定で保護してください (推奨: 600)

## ライセンス

このプロジェクトはMIT ライセンスの下でライセンスされています。  
詳細については[LICENSE](LICENSE)ファイルを参照してください。  

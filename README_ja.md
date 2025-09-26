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
- [AWS認証情報ファイル形式](#aws認証情報ファイル形式)
- [mcp tool 一覧](#mcp-tool-一覧)
  - [`updsts_update_sts_credential`](#updsts_update_sts_credential)
  - [`updsts_get_credential_info`](#updsts_get_credential_info)
  - [`updsts_get_credential_info_list`](#updsts_get_credential_info_list)
- [ファイル保存場所](#ファイル保存場所)
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
pip install updsts-<version>.tar.gz
# またはwheelファイルをインストール
pip install updsts-<version>-py3-none-any.whl

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

- `-n, --profile`: 更新するAWSプロファイル名 (必須)
- `-t, --totp-token`: MFAデバイスで生成されたTOTPトークン (必須)
- `-d, --duration`: トークン持続時間（秒）(オプション、デフォルト: 3600)

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

## AWS認証情報ファイル形式

updsts は標準的なAWS認証情報ファイル形式で動作します。  
既存のプロファイルを保持しながら、指定されたセクションのみを更新します。  

認証情報ファイルの例:  
updsts を動作させるには、 mfa_device_arn の設定が必要です

```ini
[default]
# アクセスキーID (required)
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
# シークレットアクセスキー (required)
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLE
# IAMユーザーのMFAデバイスARN (required)
mfa_device_arn = arn:aws:iam::123456789012:mfa/user 
# mktotp mcpサーバで管理されているTOTPシークレット名 (optional)
# 設定してあればAgentはTOTPトークンを自動生成して使用します.
totp_secret_name = my_totp_secret 

# ${{{ key=default [auto update by updsts]
[default_sts]
aws_access_key_id = ASIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYtempKEY
aws_session_token = IQoJb3JpZ2luX2VjE...
expiration_datetime = 2025-10-05T15:30:00+09:00
# $}}} [auto update by updsts]
```

updstsは特別なタグ間のセクションを自動的に管理し、他のプロファイルはそのまま保持します.  
タグは初回の実行時に自動的に追加されるため、手動で追加する必要はありません。

## MCP tool 一覧

MCPサーバーとして起動した場合、以下のtoolがAgentから利用可能です.

### `updsts_update_sts_credential`

指定されたAWSプロファイルのSTS認証情報を取得・更新します。

- パラメータ:
  - `profile_name` (str): 更新するAWSプロファイル名 (必須)
  - `totp_token` (str): MFAデバイスからのTOTPトークン (必須)
  - `cred_file` (str | None): 認証情報ファイルのパス (オプション、デフォルト: None)
  - `duration` (int): トークン持続時間（秒）(オプション、デフォルト: 3600)
- 戻り値: 更新された認証情報、またはNone

### `updsts_get_credential_info`

指定されたAWSプロファイルの認証情報を取得します.  
ただし、secret_access_key, session_token はマスクして表示されます.  
(LLMにsecret情報を渡さないようになっています)

- パラメータ:
  - `profile_name` (str): 取得するAWSプロファイル名 (必須)
  - `cred_file` (str | None): 認証情報ファイルのパス (オプション、デフォルト: None)
- 戻り値: 認証情報の辞書、またはNone

### `updsts_get_credential_info_list`

認証情報ファイル内のすべてのAWSプロファイルの認証情報を取得します.  
ただし、secret_access_key, session_token はマスクして表示されます.  
(LLMにsecret情報を渡さないようになっています)

- パラメータ:
  - `cred_file` (str | None): 認証情報ファイルのパス (オプション、デフォルト: None)
- 戻り値: 認証情報の辞書のリスト、または空リスト

## ファイル保存場所

デフォルトでは、AWS認証情報は以下の場所に保存されます.  

```text
~/.aws/credentials
```

`-c` オプションで別の場所を指定できます.  

## セキュリティに関する注意事項

- AWS認証情報ファイルには機密情報が含まれているため、適切な権限設定で保護してください (推奨: 600)
- 一時的なSTSトークンには制限された有効期限があり、自動的に失効します
- 強力なMFAデバイスを使用し、TOTPシークレットを安全に保管してください

## ライセンス

このプロジェクトはMIT ライセンスの下でライセンスされています。  
詳細については[LICENSE](LICENSE)ファイルを参照してください。  

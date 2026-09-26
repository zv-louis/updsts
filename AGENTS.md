# updsts project

既存の AWS プロファイルと MFA の TOTP トークンから一時的な STS 認証情報を取得し、AWS の credentials ファイルを更新する CUI ツール兼ローカル MCP サーバー。
MCP 経由で操作される前提のため、アクセスキーやシークレットキーなどの秘密情報をマスクせずに LLM 側へ返さないことを設計上の原則としている。

## 技術スタック

- Python 3.12 以上、パッケージ管理は uv、ビルドは hatchling
- 主な依存: `boto3`（STS の `get_session_token`）、`fastmcp`（MCP サーバー）、`pydantic`
- テスト: pytest（マーカー: `slow` / `integration` / `unit` / `aws`。AWS 呼び出しはモック）

## ディレクトリ構成

```text
src/updsts/
  __main__.py     CLI エントリポイント（main）。引数解析と例外のメッセージ化
  cmdparam.py     argparse のサブコマンド定義（get / list / mcp）
  cmd_handler.py  サブコマンドのハンドラ
  awsutil.py      業務ロジック: credentials ファイルの読み込み、STS トークン取得、マスク処理
  upcred.py       CredentialUpdater: credentials ファイルの該当ブロックを書き換える
  logutil.py      ロガー（コンソール出力は stderr。MCP の stdio を汚さないため）
  mcp_server.py   FastMCP のツール定義（薄いラッパー）
  mcp_impl.py     MCP ツールの実装、例外を ValueError に揃える共通処理
src/updsts_main.py  Claude プラグイン用の MCP 起動スクリプト（PEP 723 のインライン依存を持つ）
test/             モジュールごとの pytest
.claude-plugin/   Claude Code プラグインのマニフェスト
.mcp.json         プラグイン用 MCP サーバー設定（uv run src/updsts_main.py mcp --mcp-server）
```

処理の流れは、CLI なら `__main__.py` → `cmd_handler.py` → `awsutil.py` → `upcred.py`、MCP なら `mcp_server.py` → `mcp_impl.py` → `awsutil.py` → `upcred.py` となる。

## CLI

```bash
updsts get -n <profile> -t <totp_token>              # STS 認証情報を取得して credentials ファイルを更新
updsts get -n <profile> -t <totp> -sn <sts_profile>  # 書き込み先のプロファイル名を指定（既定は <profile>_sts）
updsts get -n <profile> -t <totp> -d 7200            # 有効期間（秒）を指定（既定は 3600）
updsts list                                          # プロファイル一覧（秘密情報はマスク表示）
updsts mcp --mcp-server                              # MCP サーバーとして起動（オプションなしならツール一覧を表示）
```

共通オプションは `-v, --verbose`（0: 通常、1: 詳細、2: デバッグ）と `-c, --credential_file`。

## MCP ツール

| ツール | 内容 |
| --- | --- |
| `updsts_update_sts_credential` | TOTP トークンで STS 認証情報を取得し、credentials ファイルを更新 |
| `updsts_get_credential_info` | 指定プロファイルの情報（秘密情報はマスク済み） |
| `updsts_get_credential_info_list` | 全プロファイルの情報（秘密情報はマスク済み） |

各ツールの `cred_file` と `sts_profile_name` は、空文字列なら既定値を使う。
TOTP トークンは mktotp などで生成する前提で、プロファイルの `totp_secret_name` がその対応付けに使われる。

## credentials ファイル

- 既定の場所は `~/.aws/credentials`
- 元になるプロファイルには `aws_access_key_id` / `aws_secret_access_key` / `mfa_device_arn` が必要。`totp_secret_name` は任意
- 取得した STS 認証情報は、次のタグで囲まれたブロックを丸ごと書き換える。`key` は元のプロファイル名。ブロックがなければ末尾に追加する

  ```ini
  # ${{{ key=<profile> [auto update by updsts]
  [<profile>_sts]
  aws_access_key_id=...
  aws_secret_access_key=...
  aws_session_token=...
  expiration_datetime=...
  # $}}} [auto update by updsts]
  ```

- 書き換えは `.tmp` に書いてから置き換える。元ファイルの権限を引き継ぐ
- `expiration_datetime` はローカルタイムゾーンの ISO 8601 形式
- プロキシは環境変数 `http_proxy` / `https_proxy` から読む
- ログファイルは `~/.awscm/log/awscm.log`

## 開発

```bash
uv sync                 # 依存のインストール
uv run pytest           # テスト実行
uv run updsts --help    # ローカル実行
```

## 変更時の注意

- MCP ツールの戻り値やログに秘密情報を生の値で含めない。`get_profile_info` / `get_profile_list` を MCP から呼ぶときは `secret_mask=True` を渡す
- ログは stderr に出す。stdout は MCP の stdio 通信に使われる
- 依存を変えるときは `pyproject.toml` と `src/updsts_main.py` のインライン依存の両方を更新する
- バージョンは `pyproject.toml` と `.claude-plugin/plugin.json` の両方にある

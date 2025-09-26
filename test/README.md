# Test Documentation

このディレクトリには、`updsts` プロジェクトの包括的なテストスイートが含まれています。

## テストフレームワーク

このプロジェクトでは、**pytest**を使用しています：

- **pytest**: 最新のテストフレームワーク（カバレッジレポート、マーカー機能、フィクスチャ付き）

## テストの構成

### テストファイル

- `test_awsutil.py` - AWS関連ユーティリティ関数のテスト
- `test_upcred.py` - 認証情報更新機能のテスト
- `test_cmd_handler.py` - コマンドハンドラーのテスト
- `test_main.py` - メインモジュールのテスト
- `test_integration.py` - STS統合テストとエンドツーエンドテスト

### 補助ファイル

- `conftest.py` - pytest設定とフィクスチャ定義
- `run_pytest.py` - pytest基本実行スクリプト
- `run_all_tests.py` - pytest包括実行スクリプト（カバレッジ付き）
- `tmp/` - テスト時に作成される一時ファイル用ディレクトリ

## テストの実行

### 基本的なpytest実行

```bash
# 基本的なpytest実行
uv run pytest test/ -v

# カバレッジ付き実行
uv run pytest test/ --cov=src/updsts --cov-report=html --cov-report=term-missing

# 特定のマーカーでフィルタ
uv run pytest test/ -m "integration" -v     # 統合テストのみ
uv run pytest test/ -m "unit" -v            # 単体テストのみ
uv run pytest test/ -m "aws" -v             # AWS関連テストのみ

# 専用スクリプトでの実行
uv run python test/run_pytest.py            # 基本実行
uv run python test/run_all_tests.py         # 包括実行（カバレッジ付き）
```

### 高度なpytest機能

```bash
# 並列実行（pytest-xdistが必要）
uv run pytest test/ -n auto

# 失敗時にデバッガーを起動
uv run pytest test/ --pdb

# 最初の失敗で停止
uv run pytest test/ -x

# より詳細な出力
uv run pytest test/ -vv --tb=long

# 特定のテストファイルのみ実行
uv run pytest test/test_awsutil.py -v

# 特定のテストクラス/メソッドのみ実行
uv run pytest test/test_awsutil.py::TestMaskString::test_mask_string_normal -v
```

## テストの特徴

### 🚀 **pytest機能**

- **フィクスチャ**: `conftest.py`で定義された再利用可能なテストデータ
- **マーカー**: `@pytest.mark.integration`、`@pytest.mark.aws` などでテストを分類
- **パラメータ化**: 複数の入力での自動テスト実行
- **カバレッジレポート**: HTML/XML/ターミナル出力
- **詳細な失敗情報**: 改善されたトレースバック表示

### 📊 **カバレッジレポート**

現在のカバレッジ目標: **80%以上**

- `src/updsts/cmd_handler.py`: 100.00% ✅
- `src/updsts/__main__.py`: 94.87% ✅
- `src/updsts/awsutil.py`: 94.62% ✅
- `src/updsts/upcred.py`: 70.18% 🔶

### 🔧 **一時ファイル管理**

- **pytest フィクスチャ**: `temp_dir`、`temp_file_factory`で自動管理
- 全テストで独立した一時ディレクトリを作成
- テスト完了後に自動クリーンアップ
- `test/tmp/`ディレクトリを使用してプロジェクトに残存ファイルが残らない

### 🏷️ **テストマーカー**

```bash
@pytest.mark.unit          # 単体テスト
@pytest.mark.integration   # 統合テスト
@pytest.mark.aws           # AWS関連テスト（モック使用）
@pytest.mark.slow          # 時間のかかるテスト
```

## 設定ファイル

### pytest.ini

```ini
[pytest]
minversion = 6.0
addopts = -ra -q --strict-markers --tb=short
testpaths = test
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    aws: marks tests that interact with AWS services
```

### pyproject.toml (coverage設定)

```toml
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report] 
show_missing = true
precision = 2
```

## テスト環境の設定

### 必要な依存関係

```toml
[dependency-groups]
test = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0", 
    "pytest-mock>=3.12.0",
]
```

### インストール

```bash
# すべてのテスト依存関係をインストール
uv sync --group test

# または個別にインストール
uv add --group test pytest pytest-cov pytest-mock
```

## テスト実行例

### pytest実行例

```bash
$ uv run pytest test/ --cov=src/updsts --cov-report=term-missing -v
======================================================= test session starts =======================================================
collected 81 items

test\test_awsutil_pytest.py::TestMaskString::test_mask_string_empty PASSED                                               [  1%]
test\test_awsutil_pytest.py::TestMaskString::test_mask_string_normal PASSED                                              [  2%]
test\test_integration_pytest.py::TestSTSIntegration::test_get_sts_token_success PASSED                                   [ 98%]
test\test_upcred_pytest.py::TestCredentialUpdater::test_update_credential_file_cleans_up_temp_files PASSED              [100%]

========================================================= tests coverage ==========================================================
Name                        Stmts   Miss Branch BrPart   Cover   Missing
------------------------------------------------------------------------
src\updsts\__main__.py         35      1      4      1  94.87%   56
src\updsts\awsutil.py         144      6     42      4  94.62%   52, 116, 156, 222-223, 252->247, 256
src\updsts\cmd_handler.py      34      0      6      0 100.00%
src\updsts\upcred.py           96     26     18      4  70.18%   85-121, 123->154, 162
------------------------------------------------------------------------
TOTAL                         468    108     86     12  76.17%

================================================== 79 passed, 2 skipped in 2.35s ==================================================
```

## 注意事項

- すべての一時ファイルは `test/tmp/` 内に作成されます
- テスト実行後は自動的にクリーンアップされます
- プロジェクトルートに残存ファイルは作成されません
- テストは相互に独立しており、並列実行が可能です
- pytestフィクスチャとマーカーを活用して効率的なテスト管理を実現しています.

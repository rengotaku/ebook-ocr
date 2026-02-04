# video-separater Constitution

## Core Principles

### I. Pipeline-First
すべての機能はパイプラインのステップとして設計する。
各ステップは独立して実行・テスト可能であること。
入力は画像/動画ファイル、出力はテキスト/Markdown。

### II. Test-First (NON-NEGOTIABLE)
TDD 必須: テスト作成 → テスト FAIL 確認 → 実装 → テスト PASS 確認。
Red-Green-Refactor サイクルを厳守する。
テストフレームワーク: pytest。
カバレッジ目標: ≥80%。

### III. Ollama Integration
OCR・VLM 機能は Ollama API 経由で提供する。
モデル名・URL は設定可能にする（デフォルト値あり）。
API 呼び出しはタイムアウト付きで実装する。

### IV. Immutability & Side-Effect Isolation
データ変換は純粋関数を優先する。
ファイル I/O はパイプラインの境界（入力/出力）に限定する。
中間状態の変更（mutation）を避ける。

### V. Simplicity (YAGNI)
要求された機能のみ実装する。
過剰な抽象化・設定オプションを避ける。
1ファイル 800行以下、1関数 50行以下を目安とする。

## Technical Constraints

- Python 3.13+
- 依存管理: requirements.txt + venv
- ビルド/テスト: Makefile
- OCR エンジン: DeepSeek-OCR (Ollama)
- VLM: gemma3:12b (Ollama, 設定変更可)
- 画像処理: Pillow, OpenCV

## Development Workflow

1. spec → plan → tasks → implement (SpecKit 準拠)
2. TDD: RED → GREEN → Refactor
3. Phase ごとにコミット
4. サブエージェント活用: tdd-generator (opus), phase-executor (sonnet)

## Governance

Constitution はすべての開発プラクティスに優先する。
変更には文書化・承認・移行計画が必要。

**Version**: 1.0.0 | **Ratified**: 2026-02-04 | **Last Amended**: 2026-02-04

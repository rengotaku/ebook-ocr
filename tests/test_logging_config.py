"""Tests for src.logging_config module."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from src.logging_config import get_logger, setup_logging


class TestSetupLogging:
    """setup_logging() のテスト"""

    def test_setup_with_yaml_config(self, tmp_path: Path) -> None:
        """YAML設定ファイルからロギングをセットアップ"""
        config_file = tmp_path / "logging.yml"
        config_file.write_text(
            "version: 1\n"
            "disable_existing_loggers: false\n"
            "handlers:\n"
            "  console:\n"
            "    class: logging.StreamHandler\n"
            "    level: DEBUG\n"
            "root:\n"
            "  level: DEBUG\n"
            "  handlers: [console]\n"
        )

        setup_logging(config_path=config_file)

        logger = logging.getLogger("test_yaml_config")
        assert logger.getEffectiveLevel() <= logging.DEBUG

    def test_setup_with_string_path(self, tmp_path: Path) -> None:
        """文字列パスでもセットアップ可能"""
        config_file = tmp_path / "logging.yml"
        config_file.write_text("version: 1\ndisable_existing_loggers: false\nroot:\n  level: WARNING\n")

        setup_logging(config_path=str(config_file))

    def test_setup_fallback_when_no_config(self, tmp_path: Path) -> None:
        """設定ファイルが存在しない場合はフォールバック"""
        nonexistent = tmp_path / "nonexistent.yml"
        setup_logging(config_path=nonexistent)

        logger = logging.getLogger("test_fallback")
        assert logger is not None

    def test_setup_creates_log_directory(self, tmp_path: Path) -> None:
        """file handlerのログディレクトリを自動作成"""
        log_dir = tmp_path / "logs"
        config_file = tmp_path / "logging.yml"
        config_file.write_text(
            "version: 1\n"
            "disable_existing_loggers: false\n"
            "handlers:\n"
            "  file:\n"
            "    class: logging.FileHandler\n"
            "    level: DEBUG\n"
            f"    filename: {log_dir / 'app.log'}\n"
            "root:\n"
            "  level: DEBUG\n"
            "  handlers: [file]\n"
        )

        setup_logging(config_path=config_file)
        assert log_dir.exists()

    def test_setup_default_config_path(self) -> None:
        """デフォルトでconf/logging.ymlを使用"""
        # conf/logging.yml が存在するのでエラーなく実行される
        setup_logging()


class TestGetLogger:
    """get_logger() のテスト"""

    def test_returns_logger_instance(self) -> None:
        """Logger インスタンスを返す"""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_returns_same_logger_for_same_name(self) -> None:
        """同じ名前なら同じインスタンスを返す"""
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        assert logger1 is logger2


@pytest.fixture(autouse=True)
def _reset_logging():
    """各テスト後にルートロガーをリセット"""
    yield
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.WARNING)

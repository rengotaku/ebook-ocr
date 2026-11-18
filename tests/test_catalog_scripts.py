"""scripts/catalog のパース処理のテスト（ネットワークは使わない）."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "catalog"))

import parse_mybook  # noqa: E402  (scripts/catalog を import path に足してから読む)

HTML = """
<ul>
  <li class="bookshelfList__listBox">
    <a href="/mybook/series/list?titleId=T1&displayStatus=true"
       name="aid=A1&titleName=サンプル本&authorNm=著者&publisherNm=出版社">
      <img class="bookshelfList__itemListImage" src="/photo/1.jpg">
      サンプル本
    </a>
  </li>
</ul>
"""


class TestParseMybookHref:
    def test_title_id_is_taken_from_a_path_with_query(self) -> None:
        rows = parse_mybook.parse_html(HTML)

        assert len(rows) == 1
        assert rows[0]["titleId"] == "T1"

    def test_meta_is_parsed_from_the_name_attribute(self) -> None:
        rows = parse_mybook.parse_html(HTML)

        assert rows[0]["aid"] == "A1"
        assert rows[0]["author"] == "著者"

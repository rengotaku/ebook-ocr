# Phase 4: RED テスト結果 - 番号情報欠落ページの処理

**Phase**: 4
**User Story**: US4 - 番号情報欠落ページの処理
**機能要件**: FR-008
**Status**: RED (FAIL確認済み)
**Date**: 2026-02-09

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | 4 |
| FAIL テスト数 | 1 |
| PASS テスト数 | 6 |
| 合計テスト数 | 7 |
| テストファイル | tests/book_converter/test_page_grouper.py |
| テストクラス | TestFallbackToPreviousSection |

## テストファイル一覧

| ファイル | 追加テスト数 |
|---------|------------|
| tests/book_converter/test_page_grouper.py | 7 (1 FAIL, 6 PASS) |

## FAILテスト一覧

| テストファイル | テストメソッド | 期待動作 | 現状 |
|--------------|--------------|----------|------|
| test_page_grouper.py | test_first_content_page_without_section_not_dropped | 最初のコンテンツページ（セクション情報なし）がドロップされない | ページがドロップされる |

## PASSテスト一覧（既に実装済みの機能）

以下のテストは既存の実装で既にPASSしている:

| テストメソッド | 期待動作 |
|--------------|----------|
| test_fallback_to_previous_section | セクション情報なしのページが直前のセクションに配置される |
| test_consecutive_missing_sections | 連続するセクション情報なしページが同じセクションに配置される |
| test_first_chapter_page_without_section_stays_in_chapter | 章扉後の最初のページがセクション情報なしでも章レベルに留まる |
| test_fallback_preserves_page_order | フォールバック後もページ順序が保持される |
| test_fallback_when_section_not_in_toc | TOCにないセクション番号は直前のセクションにフォールバック |
| test_section_transition_with_missing_info | セクション間のセクション情報なしページが直前のセクションに配置される |

## 実装ヒント

### FAILテストの修正ポイント

**test_first_content_page_without_section_not_dropped**:

現在の実装では `_assign_pages_to_sections()` で `current_section = None` の場合、ページがどのセクションにも割り当てられずドロップされる。

```python
# 現在のロジック（問題あり）
if current_section:
    if current_section not in assignments:
        assignments[current_section] = []
    assignments[current_section].append(page)
# current_section が None の場合、ページは無視される
```

**修正案**:
1. 最初のコンテンツページでセクション情報がない場合、TOCの最初の章に配置する
2. または、前付け（front-matter）に配置して情報損失を防ぐ
3. または、未分類ページ用の特別なセクションを作成する

### 推奨修正

```python
def _assign_pages_to_sections(...):
    assignments: dict[str, list[ET.Element]] = {}
    current_section = None
    unassigned_pages: list[ET.Element] = []  # 新規: 未割り当てページ

    for page in pages:
        section_num = _extract_section_from_page(page)

        if section_num and section_num in toc_lookup:
            current_section = section_num

        if current_section:
            if current_section not in assignments:
                assignments[current_section] = []
            assignments[current_section].append(page)
        else:
            # 新規: 未割り当てページを追跡
            unassigned_pages.append(page)

    # 未割り当てページを最初の章に配置するか、特別処理
    return assignments, unassigned_pages  # API変更が必要
```

## FAIL出力例

```
FAILED tests/book_converter/test_page_grouper.py::TestFallbackToPreviousSection::test_first_content_page_without_section_not_dropped

self = <tests.book_converter.test_page_grouper.TestFallbackToPreviousSection object at 0x...>

    def test_first_content_page_without_section_not_dropped(self) -> None:
        """First content page without section info should NOT be dropped."""
        ...
>       assert "2" in all_page_numbers, (
            "Page 2 should NOT be dropped from output. "
            f"Found pages: {all_page_numbers}"
        )
E       AssertionError: Page 2 should NOT be dropped from output. Found pages: ['1', '3']
E       assert '2' in ['1', '3']
```

## 次のステップ

1. **GREEN実装**: `_assign_pages_to_sections()` にセクション情報なしページの特別処理を追加
2. **検証**: `make test` で全テストPASSを確認
3. **リグレッションテスト**: 既存のUS1+US2+US3テストがすべてPASSすることを確認

## 備考

- 基本的なフォールバック機能（直前のセクションへの配置）は Phase 2 で既に実装済み
- Phase 4 で発見されたのは「最初のコンテンツページにセクション情報がない」エッジケース
- このエッジケースは FR-008 の要件「直前のページと同じセクションに配置」の境界条件

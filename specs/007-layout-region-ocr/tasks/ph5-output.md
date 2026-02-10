# Phase 5 Output: US4 - フォールバック処理

**日付**: 2026-02-11
**Phase**: Phase 5 (US4 - フォールバック処理)
**ステータス**: GREEN - 全テスト成功

## 作業サマリ

Phase 5では、User Story 4「フォールバック処理」を実装しました。レイアウト検出に失敗した場合や検出領域のカバー率が低い場合に、ページ全体OCRにフォールバックする機能を追加しました。

### 完了タスク

| タスクID | 説明 | ステータス |
|---------|------|----------|
| T057 | RED テスト結果読み取り | ✅ 完了 |
| T058 | calculate_coverage() 関数実装 | ✅ 完了 |
| T059 | should_fallback() 関数実装 | ✅ 完了 |
| T060 | ocr_by_layout() にフォールバック統合 | ✅ 完了 |
| T061 | `make test` PASS 確認 (GREEN) | ✅ 完了 |
| T062 | リグレッションテスト確認 | ✅ 完了 |
| T063 | Phase 5 出力生成 | ✅ 完了 |

**進捗**: 7/7 タスク完了 (100%)

---

## 変更ファイル一覧

### 実装追加

| ファイル | 変更種別 | 説明 |
|---------|---------|------|
| src/layout_ocr.py | 既存更新 | calculate_coverage(), should_fallback() 追加、ocr_by_layout() フォールバック統合 |

### テスト更新

| ファイル | 変更種別 | 説明 |
|---------|---------|------|
| tests/test_layout_ocr.py | 既存更新 | Phase 5 RED テスト（18テストケース追加）、Phase 4の1テスト削除 |

---

## 実装の詳細

### 1. calculate_coverage() 関数実装 (T058)

**ファイル**: `src/layout_ocr.py`

**アルゴリズム** (data-model.md準拠):
```python
def calculate_coverage(regions: list[dict], page_size: tuple[int, int]) -> float:
    """検出領域がページをカバーする割合を計算。"""
    if not regions or page_size[0] <= 0 or page_size[1] <= 0:
        return 0.0

    page_area = page_size[0] * page_size[1]
    total_region_area = sum(
        (r["bbox"][2] - r["bbox"][0]) * (r["bbox"][3] - r["bbox"][1])
        for r in regions
    )
    return total_region_area / page_area
```

**特徴**:
- ページ面積に対する検出領域の合計面積の割合を計算
- 空のregionsまたはゼロページサイズは0.0を返す
- ゼロ除算を回避

### 2. should_fallback() 関数実装 (T059)

**ファイル**: `src/layout_ocr.py`

**フォールバック条件** (research.md準拠):
1. 領域が検出されなかった
2. 検出領域のカバー率が30%未満
3. ページ全体が1つのFIGUREとして検出された（90%以上カバー）

**実装**:
```python
def should_fallback(
    regions: list[dict],
    page_size: tuple[int, int],
    threshold: float = 0.3,
) -> bool:
    """フォールバックが必要かどうかを判定。"""
    # 条件1: 領域なし
    if not regions:
        return True

    # OCR対象領域のみをフィルタ（ABANDONを除外）
    ocr_regions = [r for r in regions if r["type"] != "ABANDON"]
    if not ocr_regions:
        return True

    # 条件2: カバー率が閾値未満
    coverage = calculate_coverage(ocr_regions, page_size)
    if coverage < threshold:
        return True

    # 条件3: 単一FIGUREがページの90%以上をカバー
    if len(ocr_regions) == 1 and ocr_regions[0]["type"] == "FIGURE":
        if coverage >= 0.9:
            return True

    return False
```

**特徴**:
- ABANDON領域を除外してOCR対象領域のみを評価
- カスタムしきい値をサポート（デフォルト: 0.3）
- 単一FIGUREの全ページカバー検出（90%以上）

### 3. ocr_by_layout() フォールバック統合 (T060)

**ファイル**: `src/layout_ocr.py`

**変更内容**:
- フォールバック判定を追加
- フォールバック時はページ全体をDeepSeek-OCRで処理
- フォールバック結果は `region_type="FALLBACK"` で返す

**実装**:
```python
def ocr_by_layout(
    page_path: str,
    layout: dict,
    base_url: str = "http://localhost:11434",
    timeout: int = 60,
) -> list[OCRResult]:
    regions = layout.get("regions", [])
    page_size = tuple(layout.get("page_size", [0, 0]))

    # フォールバック判定
    if should_fallback(regions, page_size):
        # ページ全体OCRを実行
        img = Image.open(page_path)
        image_b64 = encode_pil_image(img)

        payload = {
            "model": "deepseek-ocr",
            "messages": [
                {
                    "role": "user",
                    "content": "",
                    "images": [image_b64],
                },
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 4096,
            },
        }

        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()

        result_json = response.json()
        ocr_text = result_json["message"]["content"]

        # フォールバック結果を返す
        return [
            OCRResult(
                region_type="FALLBACK",
                text=ocr_text,
                formatted=ocr_text,
            )
        ]

    # 通常の領域別OCR処理（既存コード）
    ...
```

**特徴**:
- フォールバック時はページ全体を1つのOCRResultとして返す
- DeepSeek-OCRを使用（VLMではない）
- formatted も text と同じ内容（フォーマット不要）

### 4. Phase 4 テスト削除

**ファイル**: `tests/test_layout_ocr.py`

**削除したテスト**:
- `TestOcrByLayoutEdgeCases::test_ocr_by_layout_empty_regions`

**理由**:
- Phase 4 では空regions時に空リストを返すことを期待していた
- Phase 5 US4 実装により、空regionsはフォールバックトリガーとなる
- 新しい Phase 5 テスト `test_ocr_by_layout_fallback_empty_regions` が正しい動作を検証
- 古いテストは削除し、コメントで理由を記載

---

## テスト結果

### Phase 5 テスト (tests/test_layout_ocr.py)

```
53 passed in 0.24s
```

#### 新規追加テスト一覧（Phase 5）

| テストクラス | テストメソッド | 検証内容 |
|------------|--------------|---------|
| TestCalculateCoverage | test_calculate_coverage_single_region | 単一領域: 25%カバー率 |
| TestCalculateCoverage | test_calculate_coverage_multiple_regions | 複数領域: 12.5%カバー率 |
| TestCalculateCoverage | test_calculate_coverage_full_page | 全ページ: 100%カバー率 |
| TestCalculateCoverage | test_calculate_coverage_empty_regions | 空regions: 0%カバー率 |
| TestCalculateCoverage | test_calculate_coverage_real_world_example | 実世界例: 64.7%カバー率 |
| TestShouldFallback | test_should_fallback_empty_regions | 空regions → True |
| TestShouldFallback | test_should_fallback_low_coverage | 4%カバー率 → True |
| TestShouldFallback | test_should_fallback_sufficient_coverage | 36%カバー率 → False |
| TestShouldFallback | test_should_fallback_exactly_30_percent | 30%カバー率 → False (境界値) |
| TestShouldFallback | test_should_fallback_custom_threshold | カスタムしきい値50% |
| TestShouldFallback | test_should_fallback_single_figure_full_page | 全ページFIGURE → True |
| TestShouldFallback | test_should_fallback_multiple_figures_not_fallback | 複数FIGURE → False |
| TestFallbackEmptyLayout | test_ocr_by_layout_fallback_empty_regions | 空layout → ページ全体OCR |
| TestFallbackEmptyLayout | test_ocr_by_layout_fallback_missing_regions_key | regionsキー欠落 → フォールバック |
| TestFallbackLowCoverage | test_ocr_by_layout_fallback_below_30_percent | 1%カバー率 → ページ全体OCR |
| TestFallbackLowCoverage | test_ocr_by_layout_no_fallback_above_30_percent | 50%カバー率 → 通常OCR |
| TestFallbackLowCoverage | test_ocr_by_layout_fallback_29_percent_coverage | 29%カバー率 → フォールバック |
| TestFallbackSingleFigure | test_ocr_by_layout_fallback_full_page_figure | 全ページFIGURE → フォールバック |
| TestFallbackEdgeCases | test_calculate_coverage_zero_page_size | ゼロページサイズハンドリング |
| TestFallbackEdgeCases | test_calculate_coverage_negative_bbox | 負bbox座標ハンドリング |
| TestFallbackEdgeCases | test_should_fallback_only_abandon_regions | ABANDONのみ → True |

### リグレッションテスト

関連テストファイル全て通過:
- `tests/test_layout_ocr.py`: 53/53 PASS (Phase 4 + Phase 5)
- `tests/test_reading_order.py`: 20/20 PASS (Phase 3)
- `tests/test_ocr_deepseek.py`: 8/8 PASS
- `tests/test_utils.py`: 12/12 PASS

**合計**: 93/93 テスト成功

**Note**: `tests/test_detect_figures.py` の3件のテストは Phase 5 実装前から失敗しており（`doclayout_yolo` モジュール不足）、Phase 5 の変更とは無関係です。

---

## 次フェーズへの引き継ぎ

### 実装完了項目

1. ✅ **calculate_coverage()**: 検出領域のカバー率計算
2. ✅ **should_fallback()**: フォールバック判定ロジック
3. ✅ **ocr_by_layout() フォールバック統合**: ページ全体OCRへの切り替え

### 後続フェーズでの利用可能な機能

- `ocr_by_layout(page_path, layout)`: 自動フォールバック対応
  - 空regions → ページ全体OCR
  - 30%未満カバー率 → ページ全体OCR
  - 全ページFIGURE（90%以上） → ページ全体OCR
  - それ以外 → 領域別OCR

- フォールバック結果:
  - `region_type="FALLBACK"`
  - DeepSeek-OCRで処理
  - 1つのOCRResultとして返す

### Phase 6 で実装予定の機能

**Polish & パイプライン統合**:
- `src/pipeline.py` への統合
- `config.yaml` にパラメータ追加（coverage_threshold, min_region_area）
- Makefile 更新
- quickstart.md の検証

**依存関係**:
- Phase 6 は、Phase 5 で実装した完全な領域別OCR機能をパイプラインに統合

---

## 発見した問題点

### なし

すべてのテストが成功し、既存機能への影響もありません。

---

## 備考

### フォールバック判定の設計判断

**デフォルトしきい値: 30%**
- research.md の仕様に準拠
- カスタムしきい値をサポート（`threshold` パラメータ）

**ABANDON領域の扱い**
- フォールバック判定時にABANDON領域を除外
- OCR対象領域のみでカバー率を計算
- ABANDONのみのページはフォールバックをトリガー

**単一FIGUREの特別扱い**
- 90%以上カバーする単一FIGUREはフォールバック
- ページ全体が1つの図として誤検出された場合の対策
- 複数FIGUREの場合は通常処理

### region_type="FALLBACK" の導入

フォールバック結果を明示的に識別するため、新しいregion_type `"FALLBACK"` を導入しました。

**利点**:
1. フォールバック実行の明示的な記録
2. デバッグ・ログ出力で識別可能
3. 後続処理でフォールバック結果を特別扱い可能

**代替案**:
- `region_type="TEXT"` も許容されるが、通常のTEXT領域と区別できない
- テストでは `region_type in ("FALLBACK", "TEXT")` で両方を許容

### エッジケース対応

**ゼロページサイズ**:
- `calculate_coverage()` は 0.0 を返す
- ゼロ除算を回避

**負のbbox座標**:
- そのまま計算（面積が負にならない）
- 実世界では発生しないが、堅牢性のため対応

**regionsキー欠落**:
- `layout.get("regions", [])` で空リストとして処理
- フォールバックをトリガー

### テストカバレッジ

Phase 5 では以下の観点をカバー:
- カバー率計算の正確性 (5テスト)
- フォールバック判定ロジック (7テスト)
- 空layout フォールバック (2テスト)
- 低カバー率フォールバック (3テスト)
- 全ページFIGURE フォールバック (1テスト)
- エッジケース (3テスト)

**合計**: 21テスト追加（18 Phase 5 新規 + 既存53 = 71テスト、Phase 4テスト1件削除で実質53テスト）

---

**ステータス**: ✅ Phase 5 完了 - 次は Phase 6 (Polish & パイプライン統合) へ

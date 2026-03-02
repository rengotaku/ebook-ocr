SHELL := /bin/bash
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Load defaults from config.yaml (overridable via: make run VIDEO="..." INTERVAL=3)
# Read config values using Python (avoids Make's # comment interpretation issue)
CFG = python3 -c "import yaml; c=yaml.safe_load(open('config.yaml')); print(c.get('$(1)','') if c.get('$(1)') is not None else '')"

VIDEO ?= $(shell $(call CFG,video))
OUTPUT ?= $(shell $(call CFG,output))
INTERVAL ?= $(shell $(call CFG,interval))
THRESHOLD ?= $(shell $(call CFG,threshold))

# Hash directory (set manually for individual targets)
# Usage: make ocr HASHDIR=output/a3f8c2d1e5b7f9c0
HASHDIR ?=

# Limit option for quick testing (optional)
# Usage: make run VIDEO=input.mp4 LIMIT=25
LIMIT ?=
LIMIT_OPT := $(if $(LIMIT),--limit $(LIMIT),)

# Book converter variables
INPUT_MD ?=
OUTPUT_XML ?=
USE_LLM ?= $(shell $(call CFG,use_llm_toc_classifier))

.PHONY: help setup run extract-frames deduplicate split-spreads detect-layout run-ocr consolidate preview-extract preview-trim preview-trim-grid test test-book-converter test-cov converter convert-sample heading-report normalize-headings validate-toc ruff pylint lint clean clean-all

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup: $(VENV)/bin/activate ## Create venv and install dependencies

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	touch $(VENV)/bin/activate

# === Individual CLI Commands (New Pipeline) ===

extract-frames: setup ## Step 1: Extract frames from video (requires VIDEO, OUTPUT or HASHDIR)
	@test -n "$(VIDEO)" || { echo "Error: VIDEO required. Usage: make extract-frames VIDEO=input.mp4 OUTPUT=output"; exit 1; }
	@test -n "$(OUTPUT)$(HASHDIR)" || { echo "Error: OUTPUT or HASHDIR required"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.extract_frames "$(VIDEO)" -o "$(or $(HASHDIR),$(OUTPUT))/frames" -i $(INTERVAL)

deduplicate: setup ## Step 2: Deduplicate frames (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make deduplicate HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.deduplicate "$(HASHDIR)/frames" -o "$(HASHDIR)/pages" -t $(THRESHOLD) $(LIMIT_OPT)

SPREAD_MODE ?= $(shell $(call CFG,spread_mode))

# Split trim (新命名規則)
SPREAD_LEFT_PAGE_OUTER ?= $(shell $(call CFG,spread_left_trim))
SPREAD_LEFT_PAGE_INNER ?= $(shell $(call CFG,spread_left_page_inner))
SPREAD_RIGHT_PAGE_INNER ?= $(shell $(call CFG,spread_right_page_inner))
SPREAD_RIGHT_PAGE_OUTER ?= $(shell $(call CFG,spread_right_trim))

# Global trim
GLOBAL_TRIM_TOP ?= $(shell $(call CFG,global_trim_top))
GLOBAL_TRIM_BOTTOM ?= $(shell $(call CFG,global_trim_bottom))
GLOBAL_TRIM_LEFT ?= $(shell $(call CFG,global_trim_left))
GLOBAL_TRIM_RIGHT ?= $(shell $(call CFG,global_trim_right))

split-spreads: setup ## Step 2.5: Split spread images into pages (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make split-spreads HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.split_spreads "$(HASHDIR)/pages" \
		--mode $(SPREAD_MODE) \
		--left-page-outer $(SPREAD_LEFT_PAGE_OUTER) \
		--left-page-inner $(SPREAD_LEFT_PAGE_INNER) \
		--right-page-inner $(SPREAD_RIGHT_PAGE_INNER) \
		--right-page-outer $(SPREAD_RIGHT_PAGE_OUTER) \
		--global-trim-top $(GLOBAL_TRIM_TOP) \
		--global-trim-bottom $(GLOBAL_TRIM_BOTTOM) \
		--global-trim-left $(GLOBAL_TRIM_LEFT) \
		--global-trim-right $(GLOBAL_TRIM_RIGHT)

preview-extract: setup ## Preview: Extract sample frames to preview/frames/ (requires VIDEO)
	@test -n "$(VIDEO)" || { echo "Error: VIDEO parameter required. Usage: make preview-extract VIDEO=input.mp4"; exit 1; }
	@test -f "$(VIDEO)" || { echo "Error: VIDEO file not found: $(VIDEO)"; exit 1; }
	$(eval HASH := $(shell PYTHONPATH=$(CURDIR) $(PYTHON) -m src.preprocessing.hash "$(VIDEO)" --prefix-only 2>/dev/null))
	@test -n "$(HASH)" || { echo "Error: Failed to compute hash for VIDEO $(VIDEO)"; exit 1; }
	$(eval HASHDIR := $(or $(OUTPUT),output)/$(HASH))
	$(eval PREVIEW_DIR := $(HASHDIR)/preview/frames)
	@echo "=== Extracting preview frames to $(PREVIEW_DIR) ==="
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.extract_frames "$(VIDEO)" -o "$(PREVIEW_DIR)" -i $(INTERVAL)
	@echo "=== Preview frames extracted: $(PREVIEW_DIR) ==="

preview-trim: setup ## Preview: Apply trim to preview/frames/ -> preview/trimmed/ (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make preview-trim HASHDIR=output/<hash>"; exit 1; }
	@test -d "$(HASHDIR)/preview/frames" || { echo "Error: $(HASHDIR)/preview/frames not found. Run 'make preview-extract' first."; exit 1; }
	@echo "=== Applying trim to preview frames ==="
	PYTHONPATH=$(CURDIR) $(PYTHON) -c \
		"from src.cli.split_spreads import preview_trim; \
		from src.preprocessing.split_spread import SpreadMode, TrimConfig; \
		preview_trim('$(HASHDIR)/preview', \
			mode=SpreadMode.$(shell echo $(SPREAD_MODE) | tr a-z A-Z), \
			trim_config=TrimConfig( \
				global_top=$(or $(GLOBAL_TRIM_TOP),0.0), \
				global_bottom=$(or $(GLOBAL_TRIM_BOTTOM),0.0), \
				global_left=$(or $(GLOBAL_TRIM_LEFT),0.0), \
				global_right=$(or $(GLOBAL_TRIM_RIGHT),0.0), \
				left_page_outer=$(or $(SPREAD_LEFT_PAGE_OUTER),0.0), \
				left_page_inner=$(or $(SPREAD_LEFT_PAGE_INNER),0.0), \
				right_page_inner=$(or $(SPREAD_RIGHT_PAGE_INNER),0.0), \
				right_page_outer=$(or $(SPREAD_RIGHT_PAGE_OUTER),0.0)))"
	@echo "=== Preview trim complete: $(HASHDIR)/preview/trimmed ==="

preview-trim-grid: setup ## Preview: Show trim grid guides (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required"; exit 1; }
	@test -d "$(HASHDIR)/preview/frames" || { echo "Error: Run 'make preview-extract' first."; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.preview_trim_grid \
		"$(HASHDIR)/preview/frames" \
		-o "$(HASHDIR)/preview/trim-grid" \
		--step 0.05 \
		--max 0.30 \
		--spread-mode $(SPREAD_MODE)

detect-layout: setup ## Step 3: Detect layout using yomitoku (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make detect-layout HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.detect_layout "$(HASHDIR)/pages" -o "$(HASHDIR)/layout" --device cpu $(LIMIT_OPT)

run-ocr: setup ## Step 4: Run ROVER multi-engine OCR (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make run-ocr HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.run_ocr "$(HASHDIR)/pages" -o "$(HASHDIR)/ocr_output" --layout-dir "$(HASHDIR)/layout" --device cpu $(LIMIT_OPT)

consolidate: setup ## Step 5: Consolidate OCR results (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make consolidate HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.consolidate "$(HASHDIR)/ocr_output" -o "$(HASHDIR)" $(LIMIT_OPT)

# === Full Pipeline (Convenience) ===

run: setup ## Run full pipeline for a video (VIDEO required, OUTPUT/LIMIT optional)
	@test -n "$(VIDEO)" || { echo "Error: VIDEO required. Usage: make run VIDEO=input.mp4 [LIMIT=25]"; exit 1; }
	$(eval HASH := $(shell PYTHONPATH=$(CURDIR) $(PYTHON) -m src.preprocessing.hash "$(VIDEO)" --prefix-only 2>/dev/null))
	@test -n "$(HASH)" || { echo "Error: Failed to compute hash for $(VIDEO)"; exit 1; }
	$(eval HASHDIR := $(or $(OUTPUT),output)/$(HASH))
	@echo "=== Output directory: $(HASHDIR) $(if $(LIMIT),(LIMIT=$(LIMIT)),)==="
	@echo "=== Step 1: Extract Frames ==="
	@$(MAKE) --no-print-directory extract-frames VIDEO="$(VIDEO)" HASHDIR="$(HASHDIR)"
	@echo "=== Step 2: Deduplicate ==="
	@$(MAKE) --no-print-directory deduplicate HASHDIR="$(HASHDIR)" LIMIT="$(LIMIT)"
	@echo "=== Step 2.5: Split Spreads ==="
	@$(MAKE) --no-print-directory split-spreads HASHDIR="$(HASHDIR)"
	@echo "=== Step 3: Detect Layout ==="
	@$(MAKE) --no-print-directory detect-layout HASHDIR="$(HASHDIR)" LIMIT="$(LIMIT)"
	@echo "=== Step 4: Run OCR ==="
	@$(MAKE) --no-print-directory run-ocr HASHDIR="$(HASHDIR)" LIMIT="$(LIMIT)"
	@echo "=== Step 5: Consolidate ==="
	@$(MAKE) --no-print-directory consolidate HASHDIR="$(HASHDIR)" LIMIT="$(LIMIT)"
	@echo "=== Step 6: Convert to XML ==="
	@$(MAKE) --no-print-directory converter INPUT_MD="$(HASHDIR)/book.md" OUTPUT_XML="$(HASHDIR)/book.xml"
	@echo "=== Done: $(HASHDIR)/book.xml ==="

# === Book Converter ===

converter: setup ## Convert book.md to XML (Usage: make converter INPUT_MD=path/to/book.md OUTPUT_XML=path/to/book.xml [THRESHOLD=0.5] [VERBOSE=1])
	@test -n "$(INPUT_MD)" || { echo "Error: INPUT_MD required. Usage: make converter INPUT_MD=input.md OUTPUT_XML=output.xml"; exit 1; }
	@test -n "$(OUTPUT_XML)" || { echo "Error: OUTPUT_XML required. Usage: make converter INPUT_MD=input.md OUTPUT_XML=output.xml"; exit 1; }
	PYTHONPATH=$(CURDIR) $(if $(USE_LLM),USE_LLM_TOC_CLASSIFIER=$(USE_LLM)) $(PYTHON) -m src.book_converter.cli "$(INPUT_MD)" "$(OUTPUT_XML)" --group-pages \
		$(if $(THRESHOLD),--running-head-threshold $(THRESHOLD)) \
		$(if $(VERBOSE),--verbose)

convert-sample: setup ## Convert sample book.md to XML
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.book_converter.cli tests/book_converter/fixtures/sample_book.md output/sample_book.xml --group-pages

# === Heading Normalization ===

heading-report: setup ## Generate heading pattern report (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make heading-report HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.normalize_headings report "$(HASHDIR)/book.md"

normalize-headings: setup ## Normalize headings to match TOC (requires HASHDIR, optional APPLY=1)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make normalize-headings HASHDIR=output/<hash> [APPLY=1]"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.normalize_headings normalize "$(HASHDIR)/book.md" $(if $(APPLY),--apply)

validate-toc: setup ## Validate TOC-body heading matching (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make validate-toc HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.normalize_headings validate "$(HASHDIR)/book.md"

# === Testing ===

test: setup ## Run fast tests only (excludes slow/e2e/ocr tests)
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/ -v -m "not slow and not e2e and not ocr"

test-all: setup ## Run all tests (including slow/e2e/ocr tests)
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/ -v

test-slow: setup ## Run only slow tests
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/ -v -m "slow or e2e or ocr"

test-book-converter: setup ## Run book_converter tests (fast only)
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/book_converter/ -v -m "not slow and not e2e and not ocr"

test-cov: setup ## Run tests with coverage (fast only)
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/ -v --cov=src --cov-report=term-missing -m "not slow and not e2e and not ocr"

test-cov-all: setup ## Run all tests with coverage (including slow)
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/ -v --cov=src --cov-report=term-missing

coverage: test-cov ## Alias for test-cov

# === Linting ===

ruff: ## Run ruff linter
	ruff check src/ tests/
	ruff format --check src/ tests/

pylint: ## Run pylint static analysis
	pylint --rcfile=pyproject.toml --exit-zero src/

lint: ruff pylint ## Run all linters (ruff + pylint)

# === Cleanup ===

clean: ## Remove output files (keep venv)
	rm -rf $(OUTPUT)

clean-all: clean ## Remove output and venv
	rm -rf $(VENV)

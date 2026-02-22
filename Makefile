SHELL := /bin/bash
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Load defaults from config.yaml (overridable via: make run VIDEO="..." INTERVAL=3)
CFG = grep '^$(1):' config.yaml | head -1 | sed 's/^[^:]*: *//' | sed 's/^"//;s/"$$//'

VIDEO ?= $(shell $(call CFG,video))
OUTPUT ?= $(shell $(call CFG,output))
INTERVAL ?= $(shell $(call CFG,interval))
THRESHOLD ?= $(shell $(call CFG,threshold))
OCR_TIMEOUT ?= $(shell $(call CFG,ocr_timeout))

# Hash directory (set manually for individual targets)
# Usage: make ocr HASHDIR=output/a3f8c2d1e5b7f9c0
HASHDIR ?=

# Book converter variables
INPUT_MD ?=
OUTPUT_XML ?=

.PHONY: help setup run extract-frames deduplicate split-spreads detect-layout run-ocr consolidate build-book test test-book-converter test-cov converter convert-sample clean clean-all

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
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.deduplicate "$(HASHDIR)/frames" -o "$(HASHDIR)/pages" -t $(THRESHOLD)

LEFT_TRIM ?= $(shell $(call CFG,spread_left_trim))
RIGHT_TRIM ?= $(shell $(call CFG,spread_right_trim))
ASPECT_RATIO ?= $(shell $(call CFG,spread_aspect_ratio))

split-spreads: setup ## Step 2.5: Split spread images into pages (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make split-spreads HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.split_spreads "$(HASHDIR)/pages" --left-trim $(LEFT_TRIM) --right-trim $(RIGHT_TRIM) --aspect-ratio $(ASPECT_RATIO)

detect-layout: setup ## Step 3: Detect layout using yomitoku (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make detect-layout HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.detect_layout "$(HASHDIR)/pages" -o "$(HASHDIR)/layout" --device cpu --detect-code

run-ocr: setup ## Step 4: Run ROVER multi-engine OCR (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make run-ocr HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.run_ocr "$(HASHDIR)/pages" -o "$(HASHDIR)/ocr_output" --layout-dir "$(HASHDIR)/layout" --device cpu

consolidate: setup ## Step 5: Consolidate OCR results (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make consolidate HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.consolidate "$(HASHDIR)" -o "$(HASHDIR)"

# === Full Pipeline (Convenience) ===

run: setup ## Run full pipeline for a video (VIDEO required, OUTPUT optional)
	@test -n "$(VIDEO)" || { echo "Error: VIDEO required. Usage: make run VIDEO=input.mp4"; exit 1; }
	$(eval HASH := $(shell PYTHONPATH=$(CURDIR) $(PYTHON) -m src.preprocessing.hash "$(VIDEO)" --prefix-only 2>/dev/null))
	@test -n "$(HASH)" || { echo "Error: Failed to compute hash for $(VIDEO)"; exit 1; }
	$(eval HASHDIR := $(or $(OUTPUT),output)/$(HASH))
	@echo "=== Output directory: $(HASHDIR) ==="
	@echo "=== Step 1: Extract Frames ==="
	@$(MAKE) --no-print-directory extract-frames VIDEO="$(VIDEO)" HASHDIR="$(HASHDIR)"
	@echo "=== Step 2: Deduplicate ==="
	@$(MAKE) --no-print-directory deduplicate HASHDIR="$(HASHDIR)"
	@echo "=== Step 3: Detect Layout ==="
	@$(MAKE) --no-print-directory detect-layout HASHDIR="$(HASHDIR)"
	@echo "=== Step 4: Run OCR ==="
	@$(MAKE) --no-print-directory run-ocr HASHDIR="$(HASHDIR)"
	@echo "=== Step 5: Consolidate ==="
	@$(MAKE) --no-print-directory consolidate HASHDIR="$(HASHDIR)"
	@echo "=== Step 6: Convert to XML ==="
	@$(MAKE) --no-print-directory converter INPUT_MD="$(HASHDIR)/book.md" OUTPUT_XML="$(HASHDIR)/book.xml"
	@echo "=== Done: $(HASHDIR)/book.xml ==="

# === Legacy Targets (for backward compatibility) ===

yomitoku-detect: setup ## [LEGACY] Run yomitoku layout detection (use detect-layout instead)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make yomitoku-detect HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.detect_layout "$(HASHDIR)/pages" -o "$(HASHDIR)/layout" --device cpu

rover-ocr: setup ## [LEGACY] Run ROVER OCR (use run-ocr instead)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make rover-ocr HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.run_ocr "$(HASHDIR)/pages" -o "$(HASHDIR)/ocr_output" --device cpu

build-book: setup ## [LEGACY] Build book.txt from ROVER outputs (use consolidate instead)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make build-book HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.consolidate "$(HASHDIR)/ocr_output" -o "$(HASHDIR)"

# === Book Converter ===

converter: setup ## Convert book.md to XML (Usage: make converter INPUT_MD=path/to/book.md OUTPUT_XML=path/to/book.xml [THRESHOLD=0.5] [VERBOSE=1])
	@test -n "$(INPUT_MD)" || { echo "Error: INPUT_MD required. Usage: make converter INPUT_MD=input.md OUTPUT_XML=output.xml"; exit 1; }
	@test -n "$(OUTPUT_XML)" || { echo "Error: OUTPUT_XML required. Usage: make converter INPUT_MD=input.md OUTPUT_XML=output.xml"; exit 1; }
	PYTHONPATH=$(CURDIR) USE_LLM_TOC_CLASSIFIER=true $(PYTHON) -m src.book_converter.cli "$(INPUT_MD)" "$(OUTPUT_XML)" --group-pages \
		$(if $(THRESHOLD),--running-head-threshold $(THRESHOLD)) \
		$(if $(VERBOSE),--verbose)

convert-sample: setup ## Convert sample book.md to XML
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.book_converter.cli tests/book_converter/fixtures/sample_book.md output/sample_book.xml --group-pages

# === Testing ===

test: setup ## Run tests
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/ -v

test-book-converter: setup ## Run book_converter tests
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/book_converter/ -v

test-cov: setup ## Run tests with coverage
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/ -v --cov=src --cov-report=term-missing

coverage: test-cov ## Alias for test-cov

# === Cleanup ===

clean: ## Remove output files (keep venv)
	rm -rf $(OUTPUT)

clean-all: clean ## Remove output and venv
	rm -rf $(VENV)

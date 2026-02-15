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

.PHONY: help setup run extract split-spreads yomitoku-detect yomitoku-ocr rover-ocr build-book test test-book-converter test-cov converter convert-sample clean clean-all

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: $(VENV)/bin/activate ## Create venv and install dependencies

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	touch $(VENV)/bin/activate

run: setup ## Run full pipeline (ROVER multi-engine OCR: yomitoku+paddle+easyocr)
	PYTHONPATH=$(CURDIR) $(PYTHON) src/pipeline.py "$(VIDEO)" -o "$(OUTPUT)" -i $(INTERVAL) -t $(THRESHOLD) --device cpu --ocr-timeout $(OCR_TIMEOUT)

extract: setup ## Extract frames only (skip OCR)
	PYTHONPATH=$(CURDIR) $(PYTHON) src/pipeline.py "$(VIDEO)" -o "$(OUTPUT)" -i $(INTERVAL) -t $(THRESHOLD) --skip-ocr

LEFT_TRIM ?= $(shell $(call CFG,spread_left_trim))
RIGHT_TRIM ?= $(shell $(call CFG,spread_right_trim))
ASPECT_RATIO ?= $(shell $(call CFG,spread_aspect_ratio))

split-spreads: setup ## Split spread images into pages (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make split-spreads HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) src/split_spread.py "$(HASHDIR)/pages" --left-trim $(LEFT_TRIM) --right-trim $(RIGHT_TRIM) --aspect-ratio $(ASPECT_RATIO) --renumber

yomitoku-detect: setup ## Run yomitoku layout detection and visualization (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make yomitoku-detect HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -c "from src.ocr_yomitoku import detect_layout_yomitoku; detect_layout_yomitoku('$(HASHDIR)/pages', '$(HASHDIR)', device='cpu')"

yomitoku-ocr: setup ## [LEGACY] Re-run single-engine Yomitoku OCR (use 'make run' for ROVER)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make yomitoku-ocr HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -c "from src.layout_ocr import run_yomitoku_ocr; run_yomitoku_ocr('$(HASHDIR)/pages', '$(HASHDIR)/book.txt', device='cpu')"

rover-ocr: setup ## Run ROVER multi-engine OCR (yomitoku+paddle+easyocr) with character-level voting (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make rover-ocr HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) src/ocr_rover.py "$(HASHDIR)/pages" -o "$(HASHDIR)/ocr_output"

build-book: setup ## Build book.txt and book.md from ROVER outputs (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make build-book HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) src/consolidate.py "$(HASHDIR)"

# OBSOLETE TARGETS (kept for reference, not maintained)
# ocr: setup ## [OBSOLETE] Run DeepSeek-OCR - file removed, use 'make run' instead
# detect: setup ## [OBSOLETE] Run YOLO-based layout detection - replaced by yomitoku-detect
# layout-ocr: setup ## [OBSOLETE] Run region-based OCR with cropping - replaced by yomitoku-ocr
# ensemble-ocr: setup ## [OBSOLETE] Run ensemble OCR - use 'make run' instead
# integrated-ocr: setup ## [OBSOLETE] Run integrated OCR - use 'make run' instead

test: setup ## Run tests
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/ -v

test-book-converter: setup ## Run book_converter tests
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/book_converter/ -v

test-cov: setup ## Run tests with coverage
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/ -v --cov=src --cov-report=term-missing

converter: setup ## Convert book.md to XML (Usage: make converter INPUT_MD=path/to/book.md OUTPUT_XML=path/to/book.xml [THRESHOLD=0.5] [VERBOSE=1])
	@test -n "$(INPUT_MD)" || { echo "Error: INPUT_MD required. Usage: make converter INPUT_MD=input.md OUTPUT_XML=output.xml"; exit 1; }
	@test -n "$(OUTPUT_XML)" || { echo "Error: OUTPUT_XML required. Usage: make converter INPUT_MD=input.md OUTPUT_XML=output.xml"; exit 1; }
	PYTHONPATH=$(CURDIR) USE_LLM_TOC_CLASSIFIER=true $(PYTHON) -m src.book_converter.cli "$(INPUT_MD)" "$(OUTPUT_XML)" --group-pages \
		$(if $(THRESHOLD),--running-head-threshold $(THRESHOLD)) \
		$(if $(VERBOSE),--verbose)

convert-sample: setup ## Convert sample book.md to XML
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.book_converter.cli tests/book_converter/fixtures/sample_book.md output/sample_book.xml --group-pages

clean: ## Remove output files (keep venv)
	rm -rf $(OUTPUT)

clean-all: clean ## Remove output and venv
	rm -rf $(VENV)

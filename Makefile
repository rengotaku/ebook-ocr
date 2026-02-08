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
OCR_MODEL ?= $(shell $(call CFG,ocr_model))
VLM_MODEL ?= $(shell $(call CFG,vlm_model))
VLM_URL ?= $(shell $(call CFG,ollama_url))
OCR_TIMEOUT ?= $(shell $(call CFG,ocr_timeout))
VLM_TIMEOUT ?= $(shell $(call CFG,vlm_timeout))
MIN_CONFIDENCE ?= $(shell $(call CFG,min_confidence))

# Hash directory (set manually for individual targets)
# Usage: make ocr HASHDIR=output/a3f8c2d1e5b7f9c0
HASHDIR ?=

# Book converter variables
INPUT_MD ?=
OUTPUT_XML ?=

.PHONY: help setup run extract ocr test test-book-converter test-cov converter convert-sample clean clean-all

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: $(VENV)/bin/activate ## Create venv and install dependencies

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	touch $(VENV)/bin/activate

run: setup ## Run full pipeline (DeepSeek-OCR + VLM figure description)
	PYTHONPATH=$(CURDIR) $(PYTHON) src/pipeline.py "$(VIDEO)" -o "$(OUTPUT)" -i $(INTERVAL) -t $(THRESHOLD) --ocr-model $(OCR_MODEL) --vlm-model $(VLM_MODEL) --ollama-url $(VLM_URL) --ocr-timeout $(OCR_TIMEOUT) --vlm-timeout $(VLM_TIMEOUT) --min-confidence $(MIN_CONFIDENCE)

extract: setup ## Extract frames only (skip OCR)
	PYTHONPATH=$(CURDIR) $(PYTHON) src/pipeline.py "$(VIDEO)" -o "$(OUTPUT)" -i $(INTERVAL) -t $(THRESHOLD) --skip-ocr

ocr: setup ## Run DeepSeek-OCR on pages (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make ocr HASHDIR=output/<hash>"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) src/ocr_deepseek.py "$(HASHDIR)/pages" -o "$(HASHDIR)/book.txt"

test: setup ## Run tests
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/ -v

test-book-converter: setup ## Run book_converter tests
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/book_converter/ -v

test-cov: setup ## Run tests with coverage
	PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest tests/ -v --cov=src --cov-report=term-missing

converter: setup ## Convert book.md to XML (Usage: make converter INPUT_MD=path/to/book.md OUTPUT_XML=path/to/book.xml [THRESHOLD=0.5] [VERBOSE=1])
	@test -n "$(INPUT_MD)" || { echo "Error: INPUT_MD required. Usage: make converter INPUT_MD=input.md OUTPUT_XML=output.xml"; exit 1; }
	@test -n "$(OUTPUT_XML)" || { echo "Error: OUTPUT_XML required. Usage: make converter INPUT_MD=input.md OUTPUT_XML=output.xml"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.book_converter.cli "$(INPUT_MD)" "$(OUTPUT_XML)" \
		$(if $(THRESHOLD),--running-head-threshold $(THRESHOLD)) \
		$(if $(VERBOSE),--verbose)

convert-sample: setup ## Convert sample book.md to XML
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.book_converter.cli tests/book_converter/fixtures/sample_book.md output/sample_book.xml

clean: ## Remove output files (keep venv)
	rm -rf $(OUTPUT)

clean-all: clean ## Remove output and venv
	rm -rf $(VENV)

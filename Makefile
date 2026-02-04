SHELL := /bin/bash
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Default video file (override with: make run VIDEO="path/to/video.mov")
VIDEO ?= movies/2026-01-31 15.44.11.mov
OUTPUT ?= output
INTERVAL ?= 1.5
THRESHOLD ?= 8
MODEL ?= gemma3:12b
VLM_URL ?= http://localhost:11434

# Hash directory (set automatically by pipeline, or manually for individual targets)
# Usage: make ocr HASHDIR=output/a3f8c2d1e5b7f9c0
HASHDIR ?=

.PHONY: help setup run extract ocr test clean clean-all

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: $(VENV)/bin/activate ## Create venv and install dependencies

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	touch $(VENV)/bin/activate

run: setup ## Run full pipeline (DeepSeek-OCR + VLM figure description)
	$(PYTHON) src/pipeline.py "$(VIDEO)" -o "$(OUTPUT)" -i $(INTERVAL) -t $(THRESHOLD) --vlm-model $(MODEL) --ollama-url $(VLM_URL)

extract: setup ## Extract frames only (skip OCR)
	$(PYTHON) src/pipeline.py "$(VIDEO)" -o "$(OUTPUT)" -i $(INTERVAL) -t $(THRESHOLD) --skip-ocr

ocr: setup ## Run DeepSeek-OCR on pages (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make ocr HASHDIR=output/<hash>"; exit 1; }
	$(PYTHON) src/ocr_deepseek.py "$(HASHDIR)/pages" -o "$(HASHDIR)/book.txt"

test: setup ## Run tests
	$(PYTHON) -m pytest tests/ -v

clean: ## Remove output files (keep venv)
	rm -rf $(OUTPUT)

clean-all: clean ## Remove output and venv
	rm -rf $(VENV)

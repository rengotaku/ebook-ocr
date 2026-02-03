SHELL := /bin/bash
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Default video file (override with: make run VIDEO="path/to/video.mov")
VIDEO ?= movies/2026-01-31 15.44.11.mov
OUTPUT ?= output
INTERVAL ?= 1.5
THRESHOLD ?= 8
ENGINE ?= tesseract
MODEL ?= gemma3:12b
VLM_URL ?= http://localhost:11434

# Hash directory (set automatically by pipeline, or manually for individual targets)
# Usage: make ocr HASHDIR=output/a3f8c2d1e5b7f9c0
HASHDIR ?=

.PHONY: help setup run extract hash dedup preprocess detect ocr run-v2 describe-figures run-v3 ocr-v3 clean clean-all

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: $(VENV)/bin/activate ## Create venv and install dependencies

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	touch $(VENV)/bin/activate

run: setup ## Run full pipeline (hash → extract → dedup → preprocess → OCR)
	$(PYTHON) src/pipeline.py "$(VIDEO)" -o "$(OUTPUT)" -i $(INTERVAL) -t $(THRESHOLD) -e $(ENGINE)

extract: setup ## Extract frames only (skip OCR)
	$(PYTHON) src/pipeline.py "$(VIDEO)" -o "$(OUTPUT)" -i $(INTERVAL) -t $(THRESHOLD) --skip-ocr

hash: setup ## Show video hash prefix
	$(PYTHON) src/video_hash.py "$(VIDEO)"

dedup: setup ## Run dedup on existing frames (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make dedup HASHDIR=output/<hash>"; exit 1; }
	$(PYTHON) src/deduplicate.py "$(HASHDIR)/frames" -o "$(HASHDIR)/pages" -t $(THRESHOLD)

preprocess: setup ## Preprocess pages (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make preprocess HASHDIR=output/<hash>"; exit 1; }
	$(PYTHON) src/preprocess.py "$(HASHDIR)/pages" -o "$(HASHDIR)/preprocessed"

detect: setup ## Detect figures/tables/formulas (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make detect HASHDIR=output/<hash>"; exit 1; }
	$(PYTHON) src/detect_figures.py "$(HASHDIR)/pages" -o "$(HASHDIR)"

ocr: setup ## Run OCR on preprocessed pages (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make ocr HASHDIR=output/<hash>"; exit 1; }
	$(PYTHON) src/ocr.py "$(HASHDIR)/preprocessed" -o "$(HASHDIR)/book.txt" -e $(ENGINE)

run-v2: setup ## Run v2 pipeline (Tesseract OCR + VLM figure description)
	$(PYTHON) src_v2/pipeline.py "$(VIDEO)" -o "$(OUTPUT)" -i $(INTERVAL) -t $(THRESHOLD) --model $(MODEL) --vlm-url $(VLM_URL)

describe-figures: setup ## Describe figures with VLM (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make describe-figures HASHDIR=output/<hash>"; exit 1; }
	$(PYTHON) -c "from src_v2.describe_figures import describe_figures; describe_figures('$(HASHDIR)/book.txt', '$(HASHDIR)/book.md', '$(HASHDIR)/figures', model='$(MODEL)', base_url='$(VLM_URL)')"

run-v3: setup ## Run v3 pipeline (DeepSeek-OCR + VLM figure description)
	$(PYTHON) src_v3/pipeline.py "$(VIDEO)" -o "$(OUTPUT)" -i $(INTERVAL) -t $(THRESHOLD) --vlm-model $(MODEL) --ollama-url $(VLM_URL)

ocr-v3: setup ## Run DeepSeek-OCR on pages (requires HASHDIR)
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required. Usage: make ocr-v3 HASHDIR=output/<hash>"; exit 1; }
	$(PYTHON) src_v3/ocr_deepseek.py "$(HASHDIR)/pages" -o "$(HASHDIR)/book.txt"

clean: ## Remove output files (keep venv)
	rm -rf $(OUTPUT)

clean-all: clean ## Remove output and venv
	rm -rf $(VENV)

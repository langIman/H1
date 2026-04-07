# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UAV intelligence contradiction detection using NLI (Natural Language Inference). Uses the `cross-encoder/nli-deberta-v3-large` pre-trained model to detect logical contradictions between multi-UAV intelligence report pairs. Each pair is classified via NLI into contradiction, entailment, or neutral, then thresholded on contradiction probability for binary detection.

## Running the Pipeline

```bash
# Step 1: Generate datasets (each produces 1000 balanced samples in data/)
python DataGen.py              # Simple Chinese
python DataGen_complex.py      # Complex Chinese
python DataGen_en_easy.py      # Simple English
python DataGen_en_complex.py   # Complex English

# Step 2: Run NLI inference and multi-threshold evaluation
# First set DATASET_TYPE in DeBV3L_detect.py: "easy" | "complex" | "en_easy" | "en_complex"
python DeBV3L_detect.py

# Step 3: Visualize results
# Set DATASET_TYPE in Draw_Roc.py to match
python Draw_Roc.py             # Single-dataset ROC curve
python Draw_Summary.py         # Comparative visualization across datasets
```

No build system, package manager config, or test suite exists. Dependencies: `torch`, `transformers`, `sklearn`, `numpy`, `matplotlib`, `tqdm`.

## Architecture

Three-stage pipeline with JSON files as the interface between stages:

```
DataGen*.py  -->  data/*.json  -->  DeBV3L_detect.py  -->  results/{type}/*.json  -->  Draw_*.py  -->  results/*.png
(generate)        (datasets)        (infer+evaluate)       (metrics+probabilities)     (visualize)     (plots)
```

**Data generators** (`DataGen*.py`): Template-based generation of premise-hypothesis pairs across 7 contradiction types (location, status, direction, altitude, weather, time, existence). Simple variants use single-field sentences; complex variants use multi-field sentences with 4-6 attributes. All use `random.seed(42)` and deduplication.

**Inference engine** (`DeBV3L_detect.py`): Loads model, runs batched GPU/CPU inference once, then evaluates across multiple thresholds in parallel using `ThreadPoolExecutor` (8 workers). Outputs are appended to `nli_test_record.json` (metrics per threshold) and written to `nli_inference_detail.json` (per-sample probabilities).

**Visualization** (`Draw_Roc.py`, `Draw_Summary.py`): Reads inference detail JSON, computes ROC/PR curves, finds optimal F1 threshold, renders annotated plots.

## Configuration

All configuration is inline in script variables (no config files):

- `DeBV3L_detect.py`: `DATASET_TYPE`, `MODEL_NAME`, `BATCH_SIZE` (default 16), `DEVICE` (auto CUDA/CPU), `THRESHOLDS` list
- `Draw_Roc.py`: `DATASET_TYPE` (must match inference run)
- `Draw_Summary.py`: Dataset path mappings (lines 18-27)

## Data Format

Each dataset sample: `{"premise": "UAV-A report", "hypothesis": "UAV-B report", "label": 0|1}` where 1=contradiction, 0=non-contradiction.

Results are stored under `results/{easy,complex,en_easy,en_complex}/`.

## Key Design Decisions

- Contradiction probability threshold (not argmax) is used for binary classification, enabling threshold sweep analysis
- Inference runs once; threshold evaluation is decoupled and parallelized on CPU
- Results files use append mode (`nli_test_record.json`) to preserve history across runs
- The project is bilingual (Chinese/English) with simple/complex variants to study how sentence complexity affects NLI performance

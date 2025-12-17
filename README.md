# Public Opinion Analyzer for YouTube Comments
(Capstone Project – FactLink)

---

## Project Title

Public Opinion Analyzer AI  
Automated Sociolinguistic Classification of YouTube Comments using Large Language Models

---

## Project Description

This project implements a Python-based analysis platform that automatically classifies YouTube comments according to a predefined sociolinguistic labeling framework. The primary use case is the analysis of public opinion and discourse patterns in politically or socially relevant YouTube videos.

The system ingests YouTube video links, retrieves comments, enriches them with contextual video summaries, and applies multiple Large Language Models (LLMs) to perform structured, multi-label classification. Outputs are strictly schema-enforced JSON and exported as XLSX files for further statistical analysis.

The project addresses the scalability and reproducibility problems of manual discourse analysis by providing a configurable, model-agnostic analysis pipeline.

NOTE: This project is still a prototype and various issues still exist and certain features are not implemented yet.

---

## Getting Started

### Prerequisites

- Python 3.12 (tested; other versions may work but are not guaranteed)
- pip
- Virtual environment support (venv)
- API access to at least one LLM provider (OpenAI, Google Gemini, or LM Studio)

### Installation

1. Clone the repository:
   git clone <repository-url>
   cd <repository-name>

2. Create and activate a virtual environment:
   python3.12 -m venv .venv
   source .venv/bin/activate

3. Install dependencies:
   pip install -r requirements.txt

4. Create a .env file and configure API key (or alternatively insert API key in "Settings" tab):
   OPENAI_API_KEY=...
   GEMINI_API_KEY=...
   OLLAMA_BASE_URL=...

5. Start the application:
   python main.py

6. Open IP Adress provided in terminal

---

## File Structure

### Main / Dev Branch (Application Code)

This branch contains the full application codebase, UI, and runtime logic. It represents the actively developed version of the system and is the foundation for all experiments.

```text
.
├── controllers/                                                    High-level orchestration logic
│ ├── analysis_controller.py                                        Analysis flows (end-to-end runs)
│ ├── app_controller.py                                             App lifecycle and routing
│ ├── classification_controller.py                                  Classification selection/management
│ ├── prompt_template_controller.py                                 Template selection/management
│ └── settings_controller.py                                        Settings selection/management
│
├── services/                                                       Core logic: fetching, models, analysis
│ ├── content_fetchers/                                             Content ingestion (YouTube)
│ │ ├── base_fetcher.py
│ │ └── youtube_fetcher.py
│ ├── model_providers/                                              LLM providers (adapters)
│ │ ├── base_provider.py
│ │ ├── openai_provider.py
│ │ ├── google_provider.py
│ │ └── lmstudio_provider.py
│ └── video_analysis/                                               Video metadata/summary adapters
│   ├── base_adapter.py
│   └── google_adapter.py
│
├── models/                                                         Domain and view models
│ ├── domain/                                                       Core entities (videos, comments, labels)
│ │ ├── classification_group_model.py
│ │ ├── classification_model.py
│ │ ├── comment_model.py
│ │ ├── content_analysis_model.py
│ │ ├── content_item_model.py
│ │ ├── label_model.py
│ │ ├── llm_model_info_model.py
│ │ ├── model_run_progress_model.py
│ │ ├── prompt_template_model.py
│ │ └── video_model_info_model.py
│ └── view_models/                                                  UI-facing models
│   ├── analysis/
│   ├── classification/
│   ├── prompt_template/
│   └── settings/
│
├── repositories/                                                   Data access (prompt templates, classifications)
│ ├── classification_repository.py
│ └── prompt_template_repository.py
│
├── mappers/                                                        Transformations between domain/view models
│ ├── analysis_mapper.py
│ └── classification_mapper.py
│
├── nodes/                                                          Pipeline nodes/tasks
│ └── comment_classification_node.py
│
├── views/                                                          Gradio UI components
│ ├── analysis_view.py
│ ├── classification_view.py
│ ├── prompt_template_view.py
│ ├── settings_view.py
│ └── shared_components.py
│
├── enums/                                                          Shared enumerations
│ ├── classification_output_enum.py
│ ├── placeholder_enum.py
│ ├── platform_enum.py
│ ├── provider_enum.py
│ ├── sort_by_enum.py
│ ├── sort_dir_enum.py
│ └── task_status_enum.py
│
├── Prompt_Templates/                                               Persistence - Prompt templates (JSON)
│ ├── youtube/
│ │ ├── youtube_default.json
│ │ ├── youtube_default_V2.json
│ │ └── metadata.json
│ └── tiktok/
│
├── Classifications/                                                Persistence - Label sets and groups (JSON)
│ ├── Default/
│ │ ├── anti_china.json
│ │ └── pro_taiwan.json
│ └── Group_2/
│ └── anti_china.json
│
├── Content_Archive/                                                Archived raw content
│ └── youtube/
│   ├── _temp/
│   ├── Outcast_UCcJIrU7TjidDiYnRWaMZ1hQ/
│   └── Conscious Awakening_UCkIXApx-EwR5RkUbqWPK77Q/
│
├── exports/                                                        Generated outputs
│ └── youtube/
│ └── Y0_XNg6-HkA/
│
├── config.py                                                       Application configuration
├── main.py                                                         Application entry point (Gradio UI)
├── requirements.txt                                                Runtime dependencies
├── requirements-dev.txt                                            Dev/test tooling
└── README.md                                                       Project overview and usage
│
.
```


### experiment-accuracy Branch (Evaluation & Metrics)

This branch isolates all resources required for systematic accuracy evaluation against manually labeled ground truth data. No UI logic is modified in this branch; changes focus on reproducible evaluation.

.
└── datasets/                                                       Research datasets and evaluation assets
  └── yt_factlink/                                                  FactLink yt dataset
    |                                               
    ├── 00_base_data/                                               Manually labeled source data
    │ └── (original XLSX/CSV, labeling notes)
    |
    ├── 01_conversion/                                              Data conversion to JSONL
    │ ├── 01_scripts/                                               Conversion notebooks and helpers
    │ │ ├── create_splits.ipynb
    │ │ └── xlsx_to_data_jsonl.ipynb
    │ ├── 02_outputs/                                                  Converted artifacts (JSONL)
    │ │ └── manual_labels_386_v2.data.jsonl
    │ └── 03_splits/                                                     Train/test splits with fixed seeds
    │   ├── split_v1_seed42/
    │   ├── split_manifest.json
    │   ├── train.data.jsonl
    │   └── test.data.jsonl
    |
    ├── 02_prompts/                                                    Prompt templates for experiments
    │ ├── all_at_once/                                                 Single-pass multi-label prompts
    │ │ ├── system.txt
    │ │ └── user.txt
    │ └── single_class/                                                Per-class prompt variants
    │ ├── C1/                                                          Class 1 prompt
    │ │ ├── system.txt
    │ │ └── user.txt
    │ ├── C2/
    │ ├── C3/
    │ ├── C4/
    │ └── C6/
    │
    └── 03_accuracy_testing/                                           Evaluation runs and metrics
      ├──accuracy_overview.html                                         Summary of evaluation runs
      └──summarize_accuracy_runs.py                                     Aggregation and reporting script
      ├── all_at_once/                                                   Multi-label in one pass
      │ ├── local/                                                       Local models (LM Studio/Ollama)
      │ │ └── deepseek-llm-7b/
      │ │ └── runs/                                                      Example run outputs
      │ └── openai/                                                      OpenAI models
      │  ├── run_accuracy.ipynb                                            Provider-specific run_accuracy.ipynb notebook
      │  └── gpt-5-2025-08-07/                                            Example model folder
      │  └── runs/                                                        Timestamped run directories
      │  ├── .gitkeep
      │  └── 2025-12-12T062423Z_openai_gpt-5-2025-08-07_all_at_once_split_v1_seed42/
      │  ├── 01_inputs/                                                   Prompt and evaluation inputs
      │  │ ├── system.txt
      │  │ ├── user.txt
      │  │ └── eval_file.txt
      │  ├── 02_outputs/                                                  Run artifacts and predictions
      │  │ ├── metrics.json                                               Aggregate metrics (e.g., accuracy/F1)
      │  │ ├── run_config.json                                            Model/run configuration snapshot
      │  │ └── preds.jsonl                                                Model predictions for test set
      │  └── 03_snapshots/                                                Reference notebook and snapshots
      │  │ └── run_accuracy.ipynb                                           Snapshot of run_accuracy.ipynb that was onces for that run
      │  └── .gitkeep
      └── single_class/                                                  Per-class evaluations
           ├── google/
           └── openai/
.

This branch ensures that evaluation results are reproducible and comparable across models and prompt versions.

---

### experiment-finetuning Branch (Supervised Fine-Tuning)

This branch contains all artifacts required for supervised fine-tuning of LLMs using manually labeled YouTube comments. It builds directly on the dataset preparation from the accuracy branch.

datasets/
├── yt_factlink/
│ ├── 01_conversion/
│ │ ├── train.openai.jsonl                                          Training dataset
│ │ └── test.openai.jsonl                                           Held-out evaluation dataset
│
experiments/
├── finetuning/
│ ├── configs/                                                      Fine-tuning hyperparameters
│ ├── jobs/                                                         Fine-tuning job definitions
│ ├── logs/                                                         Training and validation logs
│ └── evaluations/                                                  Post-fine-tuning performance comparisons

Fine-tuning results are compared against base model performance using the same evaluation pipeline to ensure fair comparison.


---

## Analysis

### Dev Branch (Application Pipeline)

The dev branch implements the full end-to-end analysis pipeline used by the interactive application.

1. YouTube comment retrieval using yt-dlp.
2. Context enrichment via manual or LLM-generated video summaries.
3. Runtime prompt construction using placeholders such as [VIDEOCONTEXT].
4. Parallel classification with multiple LLM providers.
5. Strict JSON validation using Pydantic schemas.
6. Export of structured results as XLSX files for external analysis.

This branch focuses on correctness, modularity, and usability rather than quantitative evaluation.

---

### experiment-accuracy Branch (Evaluation Pipeline)

The experiment-accuracy branch isolates the evaluation logic to assess model performance against manually labeled ground truth data.

1. Conversion of manually labeled comments into structured JSONL datasets.
2. Deterministic train/test splits using fixed random seeds.
3. Execution of classification runs across multiple models and prompt variants.
4. Collection of raw model predictions.
5. Computation of per-label and macro metrics, including accuracy, precision, recall, and F1 score.

All evaluation steps are designed to be reproducible and comparable across experiments.

---

### experiment-finetuning Branch (Training Pipeline)

The experiment-finetuning branch extends the evaluation pipeline with supervised fine-tuning.

1. Preparation of training and test datasets in provider-specific JSONL formats.
2. Execution of supervised fine-tuning jobs using manually labeled data.
3. Logging of training progress and validation results.
4. Post-training evaluation using the same metric pipeline as the accuracy branch.

This ensures fair comparison between base models and fine-tuned models.

---

## Results

### Dev Branch (Functional Outcomes)

- The application reliably enforces structured JSON outputs across different LLM providers.
- The modular architecture allows flexible configuration of prompts, classification groups, and models.
- Results can be exported in a consistent format suitable for downstream statistical analysis.

These outcomes validate the system design and practical usability of the application.

---

### experiment-accuracy Branch (Quantitative Evaluation)

- Model performance varies significantly across labels, particularly for low-frequency categories.
- Overall accuracy can be misleading in imbalanced settings; macro F1 provides a more informative measure.
- Certain labels exhibit high true-negative rates but low recall, highlighting class imbalance effects.

These findings demonstrate the necessity of label-wise and macro-level evaluation.

---

### experiment-finetuning Branch (Training Effects)

- Fine-tuning improves schema adherence and output consistency.
- Moderate gains are observed for some labels, while others remain data-limited.
- The small dataset size (386 manually labeled comments) constrains achievable improvements.

Overall, fine-tuning provides incremental benefits but does not fully overcome data sparsity.


---

## Contributors

蒙西 Simon Hinterreiter  
Project Lead

劉鎮宇 Zhen-Yu Liu  
Support with project development, accuracy testing, and fine-tuning

陳秋天 Ratchadaporn Leungphetngam  
Prompt design, accuracy testing, fine-tuning, and poster design

翟苡薰 Zoe Chai  
Manual labeling and accuracy testing

陳以勤 Yi-Qin Chen  
Manual labeling and accuracy testing

包承翰 Marc Bustamante  
Labeling framework design, prompt design, accuracy testing, and fine-tuning


---

## Acknowledgments

FactLink – Project partner and problem provider  
National Chengchi University (NCCU) – Academic supervision by Chung-pei Pien
Open-source contributors of LangChain, LangGraph, Gradio, and yt-dlp

---

## References

-

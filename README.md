# RVP Průzkumník

Interactive Shiny app for exploring the Czech Framework Educational Programme (RVP ZV) learning outcomes.

## Features

- **Semantic map** — UMAP visualisation of learning outcomes embedded with sentence-BERT; click any point to select it
- **Similar outcomes** — ranked table of the 15 most semantically similar outcomes, optionally filtered to other subjects
- **Detail panel** — wording, "Splněno" level description, and links to the official RVP card and methodical support page

## Project structure

```
shiny_app/
├── app.py                          # Shiny application
├── export.ps1                      # Export + patch script for Shinylive
├── Planet-01-256.png               # Favicon source (copied to docs/ on export)
├── precompute_embeddings.py        # One-time script to build processed/ files
├── requirements.txt
├── processed/
│   ├── learning_outcomes.csv       # Parsed OVU data with UMAP coordinates
│   ├── embeddings.npy              # Sentence-BERT embeddings
│   ├── similarity_matrix.npy       # Pairwise cosine similarity
│   └── umap_projections.npy
└── docs/                           # Shinylive export (served via GitHub Pages)
```

## Prerequisites

- **conda** (Miniconda or Anaconda) for environment management
- **Python 3.12** (installed inside the conda env — matches the Pyodide runtime used by Shinylive)
- ~1 GB free disk space (sentence-transformers model + cached wheels)

## 1. Create the conda environment

```bash
conda create -n sbert python=3.12 -y
conda activate sbert
```

Re-activate with `conda activate sbert` in any new shell before running the app.

## 2. Install dependencies

```bash
conda install -c conda-forge --file requirements.txt
```

## 3. Prepare the data

If the `processed/` directory is already present and populated, you can skip this step.

Otherwise, regenerate it from the raw RVP XML:

```bash
python precompute_embeddings.py data_final_rvp_zv_full_mp_20250821.xml
```

## 4. Run the app locally

There are two ways to run the app:

### A) Native Python — live dev server (recommended for development)

Runs `app.py` directly with Python + Shiny, with hot-reload on file changes.

```bash
shiny run --reload --launch-browser app.py
```

Default URL: <http://localhost:8000>. Use `--port 8001` to pick a different port.

This mode requires the runtime dependencies from step 2 and an existing `processed/` directory.

### B) Static Shinylive build — runs entirely in the browser (no Python server)

Once you have produced a `docs/` build (see step 5), you can preview it locally with any static file server. The simplest option uses Python's built-in HTTP server:

```bash
python -m http.server --directory docs --bind localhost 8008
```

Then open <http://localhost:8008>.

Note: in this mode Python and Shiny run **inside the browser** via Pyodide/WebAssembly — there is no live reload, and the first load is slower while the WASM bundle initialises.

## 5. Export to Shinylive (static site)

To rebuild `docs/` from `app.py`:

```bash
conda install -c conda-forge shinylive
```

```bash
# Windows (PowerShell) — uses the provided helper script
powershell -ExecutionPolicy Bypass -File .\export.ps1
```
## 6. Deploy

The `docs/` directory is a self-contained static site. Push it to any static host (GitHub Pages, Netlify, S3, …). For GitHub Pages, enable Pages on the repo and point it at the `docs/` folder of your default branch.


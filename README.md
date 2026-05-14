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

## Running locally

```bash
conda activate sbert
python -m http.server --directory <dir> --bind localhost 8008
```

Then open [http://localhost:8008](http://localhost:8008).

## Exporting to Shinylive

```bash
conda activate sbert
powershell -ExecutionPolicy Bypass -File "<dir>export.ps1"
```

The script runs `shinylive export`, copies the favicon, and patches `docs/index.html` with the correct page title and favicon link.

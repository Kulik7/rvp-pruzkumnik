"""
Preprocessing script: Extract data, compute embeddings, and save to files.
Run this once to generate the data files for the Shiny app.
"""

import argparse
from lxml import etree
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import umap
import pickle
from pathlib import Path

ROOT_DIR = Path(__file__).parent


def main():
    parser = argparse.ArgumentParser(description="Precompute embeddings from RVP XML.")
    parser.add_argument("xml_path", type=Path, help="Path to the RVP XML file")
    args = parser.parse_args()

    RVP_XML_PATH = args.xml_path
    OUTPUT_DIR = ROOT_DIR / "processed"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading XML data...")
    tree = etree.parse(RVP_XML_PATH)
    root = tree.getroot()

    strukturovana_data = []
    obory = root.xpath("//vzdelavaciObor")

    for obor in obory:
        nazev_oboru = obor.findtext("nazev").strip()

        obor_info = {"obor_nazev": nazev_oboru, "vysledky": []}

        vysledky_uzly = obor.xpath(".//ocekavanyVysledekUceni")

        for vysledek in vysledky_uzly:
            kod = vysledek.get("kod")
            zneni = "".join(vysledek.xpath("./zneni//text()")).strip()

            char_raw = vysledek.xpath(
                ".//urovenMetodickePodpory[@nazev='Splněno']/charakteristika/text()"
            )

            char_clean = ""
            if char_raw:
                soup = BeautifulSoup(char_raw[0], "html.parser").get_text(separator=" ")
                char_clean = (
                    soup.replace("\xa0", " ")
                    .replace("\n", " ")
                    .replace("\u202f", " ")
                    .strip()
                )

            obor_info["vysledky"].append(
                {"kod": kod, "zneni": zneni, "charakteristika": char_clean}
            )

        strukturovana_data.append(obor_info)

    flat_data = []
    for obor in strukturovana_data:
        for v in obor["vysledky"]:
            plny_popis = f"{v['zneni']} {v['charakteristika']}".strip()

            flat_data.append(
                {
                    "kod": v["kod"],
                    "obor": obor["obor_nazev"],
                    "zneni": v["zneni"],
                    "charakteristika": v["charakteristika"],
                    "popis": plny_popis,
                }
            )

    df = pd.DataFrame(flat_data)

    df["zkratka"] = df["kod"].apply(lambda x: x.split("-")[1] if "-" in str(x) else x)

    print(f"Loaded {len(df)} learning outcomes")

    print("Computing SBERT embeddings...")
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = model.encode(df["popis"].tolist(), show_progress_bar=True)
    print(f"Embeddings shape: {embeddings.shape}")

    print("Computing similarity matrix...")
    sim_matrix = cosine_similarity(embeddings)

    print("Computing UMAP projections...")
    reducer = umap.UMAP(n_neighbors=2, min_dist=0.3, metric="cosine", random_state=42)
    projections = reducer.fit_transform(embeddings)

    df["umap_x"] = projections[:, 0]
    df["umap_y"] = projections[:, 1]

    print("Saving data...")

    df.to_csv(OUTPUT_DIR / "learning_outcomes.csv", index=False)
    np.save(OUTPUT_DIR / "embeddings.npy", embeddings)
    np.save(OUTPUT_DIR / "similarity_matrix.npy", sim_matrix)
    np.save(OUTPUT_DIR / "umap_projections.npy", projections)

    with open(OUTPUT_DIR / "metadata.pkl", "wb") as f:
        pickle.dump(
            {
                "n_items": len(df),
                "embedding_dim": embeddings.shape[1],
                "model_name": "paraphrase-multilingual-MiniLM-L12-v2",
            },
            f,
        )

    print(f"Data saved to {OUTPUT_DIR}")
    print(f"  - learning_outcomes.csv: {len(df)} rows")
    print(f"  - embeddings.npy: {embeddings.shape}")
    print(f"  - similarity_matrix.npy: {sim_matrix.shape}")
    print(f"  - umap_projections.npy: {projections.shape}")


if __name__ == "__main__":
    main()

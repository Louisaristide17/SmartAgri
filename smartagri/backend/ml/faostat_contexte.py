"""
Source de données RÉELLE : FAOSTAT (FAO) — domaine « Utilisation des terres » (RL), Côte d'Ivoire, 2020-2025.
Fichier : ml/data/faostat_ci_utilisation_terres.csv (téléchargé sur fao.org/faostat le 13/11/2026).
Ce script en extrait le contexte agricole du pays (surfaces, cultures permanentes, forêts, irrigation) et le
sauvegarde dans ml/faostat_contexte.json + ml/figures/faostat_terres.png.
NB : ce domaine ne contient PAS de rendements par culture ; les rendements d'entraînement restent simulés
(voir ml/README.md). Pour des rendements réels, utiliser le domaine FAOSTAT « Cultures » (QCL).
"""
import json
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ICI = Path(__file__).resolve().parent
df = pd.read_csv(ICI / "data" / "faostat_ci_utilisation_terres.csv")
df = df[df["Unité"] == "1000 ha"]
piv = df.pivot_table(index="Année", columns="Produit", values="Valeur", aggfunc="first")

def serie(nom): return {int(a): float(v) for a, v in piv[nom].dropna().items()}
contexte = {
    "source": "FAOSTAT — Utilisation des terres (RL), Côte d'Ivoire",
    "unite": "milliers d'hectares",
    "terres_agricoles": serie("Terres agricoles"),
    "terres_en_culture": serie("Terres en culture"),
    "cultures_permanentes": serie("Cultures permanentes (cacao, café, hévéa…)") if "Cultures permanentes (cacao, café, hévéa…)" in piv else serie("Cultures permanentes"),
    "terres_forestieres": serie("Terres forestières"),
    "irrigation": serie("Superficie équipée de systèmes d'irrigation"),
}
(ICI / "faostat_contexte.json").write_text(json.dumps(contexte, ensure_ascii=False, indent=2), encoding="utf-8")

(ICI / "figures").mkdir(exist_ok=True)
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ann = [2020, 2021, 2022, 2023, 2024]
for nom, lab in [("Terres en culture", "En culture"), ("Cultures permanentes", "Cultures permanentes"), ("Cultures temporaires", "Cultures temporaires")]:
    ax[0].plot(ann, [piv.loc[a, nom] / 1000 for a in ann], marker="o", label=lab)
ax[0].set_title("Surfaces cultivées (millions ha)"); ax[0].legend(); ax[0].set_xticks(ann)
f = piv["Terres forestières"].dropna()
ax[1].bar(f.index.astype(str), f.values / 1000, color="#2c5f2d")
ax[1].set_title("Terres forestières (millions ha)"); ax[1].set_ylim(3.5, 4.3)
fig.suptitle("Côte d'Ivoire — FAOSTAT (données réelles)"); fig.tight_layout()
fig.savefig(ICI / "figures" / "faostat_terres.png", dpi=130)
print(json.dumps({k: v for k, v in contexte.items() if k != "source"}, ensure_ascii=False)[:600])

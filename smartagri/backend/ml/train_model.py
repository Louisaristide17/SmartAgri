"""
Pipeline ML SmartAgri : génération du jeu de données -> nettoyage -> analyse -> entraînement -> évaluation.
Lancer :  python ml/train_model.py     (écrit ml/model.joblib, ml/metrics.json, ml/figures/*.png, ml/dataset_clean.csv)

HONNÊTETÉ : il n'existe pas de jeu de données ivoirien public de rendements parcelle par parcelle.
Le jeu est donc SIMULÉ à partir du référentiel agronomique (referentiel_ci.py) + bruit aléatoire
(météo, pratiques, mesures) + valeurs manquantes. Le modèle apprend ce référentiel ; à remplacer
par de vraies données (ANADER, enquêtes) dès qu'elles sont disponibles.
"""
import json, sys, pathlib
import numpy as np, pandas as pd, joblib
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.compose import TransformedTargetRegressor
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.preprocessing import OneHotEncoder

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from referentiel_ci import CULTURES, SOLS, ZONES

rng = np.random.default_rng(42)
N = 6000

# ───────── 1. Formule agronomique de référence (identique à l'API) ─────────
def formule(culture, sol, zone, pluie, temp, engrais):
    c = CULTURES[culture]
    dp = abs(pluie - c["pluv"]) / c["pluv"]; fp = max(0.3, 1 - dp * 0.7)
    dt = abs(temp - c["temp"]) / 18;        ft = max(0.4, 1 - dt)
    fe = min(1.4, 0.65 + engrais / 150 * 0.75)
    az = c["zones"].get(zone, 1.0)
    return max(0.1, c["base"] * SOLS[sol]["coeff"] * fp * ft * fe * az)

# climat typique par zone (moyenne, écart-type)
CLIMAT = {"sud": (1900, 250, 27.0, 1.0), "foret": (1500, 250, 26.5, 1.2),
          "centre": (1150, 200, 27.5, 1.3), "nord": (1000, 200, 28.5, 1.5)}

# ───────── 2. Génération du jeu brut (simulé) ─────────
rows = []
cultures, sols, zones = list(CULTURES), list(SOLS), list(ZONES)
for _ in range(N):
    z = rng.choice(zones); cu = rng.choice(cultures); so = rng.choice(sols)
    pm, ps, tm, ts = CLIMAT[z]
    pluie = float(np.clip(rng.normal(pm, ps), 300, 2500))
    temp = float(np.clip(rng.normal(tm, ts), 18, 38))
    eng = float(np.clip(rng.gamma(2.0, 40.0), 0, 300))
    y = formule(cu, so, z, pluie, temp, eng) * rng.lognormal(0, 0.08)     # bruit 8 %
    rows.append(dict(culture=cu, type_sol=so, zone=z, pluviometrie=pluie, temperature=temp, engrais_kg=eng, rendement=y))
raw = pd.DataFrame(rows)
# imperfections réalistes d'une collecte terrain : manquants, doublons, aberrations
idx = rng.choice(N, int(N * 0.03), replace=False); raw.loc[idx, "pluviometrie"] = np.nan
idx = rng.choice(N, int(N * 0.02), replace=False); raw.loc[idx, "temperature"] = np.nan
idx = rng.choice(N, 40, replace=False);            raw.loc[idx, "temperature"] = 99.0       # capteur en panne
raw = pd.concat([raw, raw.sample(60, random_state=1)], ignore_index=True)                   # doublons
stats = {"lignes_brutes": int(len(raw)), "manquants_pluie": int(raw.pluviometrie.isna().sum()),
         "manquants_temp": int(raw.temperature.isna().sum()), "doublons": int(raw.duplicated().sum()),
         "temperatures_aberrantes": int((raw.temperature > 40).sum())}

# ───────── 3. Nettoyage ─────────
df = raw.drop_duplicates().copy()
df.loc[df.temperature > 40, "temperature"] = np.nan                       # valeurs hors plage CI (15–40 °C)
for col in ["pluviometrie", "temperature"]:
    df[col] = df[col].fillna(df.groupby("zone")[col].transform("median"))  # imputation par médiane de zone
df = df.dropna()
stats["lignes_propres"] = int(len(df))
df.to_csv(HERE / "dataset_clean.csv", index=False)

# ───────── 4. Analyse + figures ─────────
fig_dir = HERE / "figures"; fig_dir.mkdir(exist_ok=True)
G, G2, ORG = "#2D6A4F", "#74C69D", "#F4A261"
cacao = df[df.culture == "cacao"].groupby("zone").rendement.mean().reindex(["sud", "foret", "centre", "nord"])
stats["cacao_rendement_moyen_par_zone"] = {k: round(float(v), 3) for k, v in cacao.items()}
corr = df[["pluviometrie", "temperature", "engrais_kg", "rendement"]].corr()["rendement"].drop("rendement")
stats["correlation_rendement"] = {k: round(float(v), 3) for k, v in corr.items()}
mean_cult = df.groupby("culture").rendement.mean().sort_values()
stats["rendement_moyen_par_culture"] = {k: round(float(v), 2) for k, v in mean_cult.items()}

plt.figure(figsize=(6, 3.6)); cacao.plot.bar(color=[G, G, G2, ORG]); plt.ylabel("t/ha"); plt.title("Cacao : rendement moyen par zone")
plt.xticks(rotation=0); plt.tight_layout(); plt.savefig(fig_dir / "cacao_zone.png", dpi=200); plt.close()

# ───────── 5. Entraînement ─────────
X = df[["culture", "type_sol", "zone", "pluviometrie", "temperature", "engrais_kg"]]; y = df.rendement
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
stats["train"], stats["test"] = int(len(Xtr)), int(len(Xte))
pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), ["culture", "type_sol", "zone"])],
                        remainder="passthrough")
LOG = lambda m: TransformedTargetRegressor(regressor=m, func=np.log, inverse_func=np.exp)   # cible en log : erreur relative
cands = {"Régression linéaire": LOG(LinearRegression()),
         "Random Forest": LOG(RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1)),
         "Gradient Boosting": LOG(GradientBoostingRegressor(random_state=42))}
res = {}
for name, m in cands.items():
    p = Pipeline([("pre", pre), ("m", m)]).fit(Xtr, ytr); pr = p.predict(Xte)
    res[name] = dict(MAPE=float(mean_absolute_percentage_error(yte, pr)*100), MAE=float(mean_absolute_error(yte, pr)), RMSE=float(mean_squared_error(yte, pr) ** 0.5), R2=float(r2_score(yte, pr)))
    print(name, res[name])

# amélioration : réglage du meilleur arbre par validation croisée
best_name = max(res, key=lambda k: res[k]["R2"])
grid = GridSearchCV(Pipeline([("pre", pre), ("m", LOG(GradientBoostingRegressor(random_state=42)))]),
                    {"m__regressor__n_estimators": [200, 400], "m__regressor__max_depth": [3, 5], "m__regressor__learning_rate": [0.05, 0.1]},
                    cv=3, scoring="neg_mean_absolute_percentage_error", n_jobs=-1).fit(Xtr, ytr)
tuned = grid.best_estimator_; pr = tuned.predict(Xte)
res["Gradient Boosting réglé"] = dict(MAPE=float(mean_absolute_percentage_error(yte, pr)*100), MAE=float(mean_absolute_error(yte, pr)), RMSE=float(mean_squared_error(yte, pr) ** 0.5), R2=float(r2_score(yte, pr)))
stats["meilleurs_parametres"] = grid.best_params_
final_name = max(res, key=lambda k: res[k]["R2"])
final = tuned if final_name == "Gradient Boosting réglé" else Pipeline([("pre", pre), ("m", cands[final_name])]).fit(Xtr, ytr)
cv = cross_val_score(final, X, y, cv=5, scoring="r2")
stats.update(resultats=res, modele_retenu=final_name, cv_r2_moyen=float(cv.mean()), cv_r2_ecart=float(cv.std()))

# figures d'évaluation
names = list(res); mae = [res[n]["MAE"] for n in names]
plt.figure(figsize=(6.5, 3.6)); plt.barh(names, [res[n]["MAPE"] for n in names], color=[ORG, G2, G2, G]); plt.xlabel("Erreur relative moyenne (%) — plus petit = meilleur")
plt.title("Comparaison des modèles"); plt.tight_layout(); plt.savefig(fig_dir / "comparaison.png", dpi=200); plt.close()
pr = final.predict(Xte); plt.figure(figsize=(4.2, 4.2))
plt.scatter(yte, pr, s=4, alpha=.4, color=G); m = max(yte.max(), pr.max()); plt.plot([0, m], [0, m], color=ORG)
plt.xlabel("Rendement réel (t/ha)"); plt.ylabel("Rendement prédit"); plt.title("Prédit vs réel (jeu de test)")
plt.tight_layout(); plt.savefig(fig_dir / "pred_vs_reel.png", dpi=200); plt.close()

# ───────── 6. Utilisation sur de nouvelles données + sauvegarde ─────────
nouveau = pd.DataFrame([dict(culture="cacao", type_sol="ferrallitique", zone="foret", pluviometrie=1600, temperature=26, engrais_kg=100)])
stats["exemple_nouvelle_prediction"] = {"entree": nouveau.iloc[0].to_dict(), "modele": round(float(final.predict(nouveau)[0]), 3),
                                        "formule": round(formule("cacao", "ferrallitique", "foret", 1600, 26, 100), 3)}
joblib.dump(final, HERE / "model.joblib")
json.dump(stats, open(HERE / "metrics.json", "w"), indent=2, ensure_ascii=False, default=str)
print(json.dumps(stats, indent=2, ensure_ascii=False, default=str))

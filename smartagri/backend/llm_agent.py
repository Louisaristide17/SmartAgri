"""
Agent IA réel (LLM) — AgriBot via l'API Groq (compatible OpenAI), avec appel d'outils.

Le modèle de langage CHOISIT lui-même l'outil à appeler (function calling), reçoit le résultat,
puis rédige la réponse en français courtois. La clé est lue dans la variable d'environnement
DEEPSEEK_API_KEY / GROQ_API_KEY / ANTHROPIC_API_KEY (jamais dans le code). Sans clé ou en cas d'erreur -> l'appelant se replie sur
l'agent à règles (agent_tools.run_agent), donc l'application ne tombe jamais en panne.
"""
import os, json
from typing import List, Optional, Tuple
import httpx
from sqlalchemy.orm import Session

from models import User
from referentiel_ci import CULTURES, ZONES, SOLS, zone_depuis_ville
import agent_tools as T
import savoir

# Fournisseurs compatibles OpenAI (même format d'appel d'outils). Ordre = ordre d'essai ;
# LLM_PROVIDER=groq|deepseek force celui à essayer en premier.
def _fournisseurs():
    liste = [
        ("deepseek", "https://api.deepseek.com/chat/completions", os.getenv("DEEPSEEK_MODEL", "deepseek-chat"), os.getenv("DEEPSEEK_API_KEY", "")),
        ("groq", "https://api.groq.com/openai/v1/chat/completions", os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"), os.getenv("GROQ_API_KEY", "")),
    ]
    liste.append(("claude", "https://api.anthropic.com/v1/messages", os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5"), os.getenv("ANTHROPIC_API_KEY", "")))
    liste = [f for f in liste if f[3]]
    prefere = os.getenv("LLM_PROVIDER", "").lower()
    return sorted(liste, key=lambda f: f[0] != prefere)
MAX_TOURS = 3

SYSTEM = """Tu es AgriBot, assistant agricole expert de la Côte d'Ivoire, intégré à l'application SmartAgri.
RÔLE : conseiller les agriculteurs ivoiriens (cultures, sols, zones agro-écologiques, engrais, irrigation, maladies, calendrier).
OUTILS : utilise-les dès que la question porte sur les parcelles de l'utilisateur, ses prédictions, un calcul de rendement,
les cultures adaptées à une ville/zone, ou la fiche d'un sol/d'une culture. N'invente JAMAIS un chiffre de rendement : appelle predire_rendement.
STYLE : français simple, vouvoiement, très poli et chaleureux ; réponds d'abord précisément à la question posée (si on parle d'UN sol ou d'UNE culture,
ne parle que de celui-ci), puis propose ton aide en une phrase. Réponse concise (moins de 150 mots).
LIMITES : tu ne parles que d'agriculture. Refuse poliment les sujets médicaux, juridiques ou hors-sujet, et les pesticides non homologués en Côte d'Ivoire
(oriente vers l'ANADER). Si une information manque (culture, ville), pose UNE question de précision."""

OUTILS = [
    {"type": "function", "function": {"name": "mes_parcelles", "description": "Liste les parcelles de l'utilisateur connecté.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "mes_predictions", "description": "Donne les dernières prédictions de rendement de l'utilisateur.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "predire_rendement",
        "description": "Prédit le rendement (t/ha) avec le modèle de machine learning entraîné sur la Côte d'Ivoire.",
        "parameters": {"type": "object", "properties": {
            "culture": {"type": "string", "enum": list(CULTURES)},
            "ville": {"type": "string", "description": "Ville ivoirienne (ex: Daloa, Korhogo)"},
            "sol": {"type": "string", "enum": list(SOLS)},
            "engrais_kg": {"type": "number", "description": "kg/ha d'engrais, défaut 80"}},
            "required": ["culture"]}}},
    {"type": "function", "function": {"name": "cultures_de_la_zone", "description": "Cultures les mieux adaptées à une zone agro-écologique.",
        "parameters": {"type": "object", "properties": {"zone": {"type": "string", "enum": list(ZONES)}}, "required": ["zone"]}}},
    {"type": "function", "function": {"name": "sols_de_la_ville", "description": "Sols d'une ville ivoirienne (types, praticabilité, cultures adaptées, conseils). À utiliser dès qu'on parle des sols/terres d'une ville.",
        "parameters": {"type": "object", "properties": {"ville": {"type": "string", "description": "Ville ivoirienne, ex: Man"}}, "required": ["ville"]}}},
    {"type": "function", "function": {"name": "fiche_sol", "description": "Fiche détaillée d'UN type de sol.",
        "parameters": {"type": "object", "properties": {"sol": {"type": "string", "enum": list(SOLS)}}, "required": ["sol"]}}},
    {"type": "function", "function": {"name": "fiche_culture", "description": "Fiche détaillée d'UNE culture.",
        "parameters": {"type": "object", "properties": {"culture": {"type": "string", "enum": list(CULTURES)}}, "required": ["culture"]}}},
]


def disponible() -> bool:
    return bool(_fournisseurs())


def _executer(nom: str, args: dict, db: Session, user: User) -> str:
    try:
        if nom == "mes_parcelles":
            return T.mes_parcelles(db, user)
        if nom == "mes_predictions":
            return T.mes_predictions(db, user)
        if nom == "predire_rendement":
            culture = args.get("culture")
            if culture not in CULTURES:
                return "Culture inconnue en Côte d'Ivoire."
            sol = args.get("sol") if args.get("sol") in SOLS else "ferrallitique"
            return T.predire_rendement(culture, args.get("ville"), sol, float(args.get("engrais_kg") or 80))
        if nom == "cultures_de_la_zone":
            return T.cultures_de_la_zone(args["zone"]) if args.get("zone") in ZONES else "Zone inconnue."
        if nom == "sols_de_la_ville":
            v = T.normaliser(args.get("ville", "")).strip().replace(" ", "-")
            z = zone_depuis_ville(v)
            return savoir.fiche_sols_ville(v, z) if z else "Ville inconnue dans notre référentiel."
        if nom == "fiche_sol":
            return savoir.fiche_sol(args.get("sol", ""))
        if nom == "fiche_culture":
            return savoir.fiche_culture(args.get("culture", ""))
    except Exception as exc:
        return f"Erreur de l'outil : {exc}"
    return "Outil inconnu."


def _boucle_claude(url, modele, cle, message, db, user, history):
    """Même boucle agent avec l'API Messages d'Anthropic (format d'outils différent)."""
    outils = [{"name": o["function"]["name"], "description": o["function"]["description"],
               "input_schema": o["function"]["parameters"]} for o in OUTILS]
    msgs = []
    for h in history[-10:]:
        msgs.append({"role": h["role"], "content": h["content"][:1200]})
    while msgs and msgs[0]["role"] != "user":                 # l'API Claude exige de commencer par un message « user »
        msgs.pop(0)
    msgs.append({"role": "user", "content": message})
    utilises: List[str] = []
    with httpx.Client(timeout=25) as client:
        for _ in range(MAX_TOURS):
            r = client.post(url, headers={"x-api-key": cle, "anthropic-version": "2023-06-01"},
                            json={"model": modele, "max_tokens": 600, "temperature": 0.3,
                                  "system": SYSTEM + f"\nL'utilisateur s'appelle {T._prenom(user)}.",
                                  "tools": outils, "messages": msgs})
            r.raise_for_status()
            blocs = r.json().get("content", [])
            appels = [b for b in blocs if b.get("type") == "tool_use"]
            if not appels:
                return "".join(b.get("text", "") for b in blocs if b.get("type") == "text").strip() or None, utilises
            msgs.append({"role": "assistant", "content": blocs})
            resultats = []
            for a in appels:
                utilises.append(a["name"] + (" (modèle ML)" if a["name"] == "predire_rendement" else ""))
                resultats.append({"type": "tool_result", "tool_use_id": a["id"],
                                  "content": _executer(a["name"], a.get("input") or {}, db, user)})
            msgs.append({"role": "user", "content": resultats})
    return None, utilises


def _boucle(nom_fournisseur, url, modele, cle, message, db, user, history):
    """Boucle agent : LLM -> outils -> LLM, pour UN fournisseur. Lève une exception en cas d'échec."""
    if nom_fournisseur == "claude":
        return _boucle_claude(url, modele, cle, message, db, user, history)
    msgs = [{"role": "system", "content": SYSTEM + f"\nL'utilisateur s'appelle {T._prenom(user)}."}]
    for h in history[-10:]:                                   # mémoire de la conversation
        msgs.append({"role": h["role"], "content": h["content"][:1200]})
    msgs.append({"role": "user", "content": message})
    utilises: List[str] = []
    with httpx.Client(timeout=25) as client:
        for _ in range(MAX_TOURS):
            r = client.post(url, headers={"Authorization": f"Bearer {cle}"},
                            json={"model": modele, "messages": msgs, "tools": OUTILS,
                                  "tool_choice": "auto", "temperature": 0.3, "max_tokens": 600})
            r.raise_for_status()
            msg = r.json()["choices"][0]["message"]
            appels = msg.get("tool_calls") or []
            if not appels:
                return (msg.get("content") or "").strip() or None, utilises
            msgs.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": appels})
            for a in appels:
                nom = a["function"]["name"]
                try:
                    args = json.loads(a["function"].get("arguments") or "{}")
                except Exception:
                    args = {}
                utilises.append(nom + (" (modèle ML)" if nom == "predire_rendement" else ""))
                msgs.append({"role": "tool", "tool_call_id": a["id"], "name": nom,
                             "content": _executer(nom, args, db, user)})
    return None, utilises


def run_llm_agent(message: str, db: Session, user: User, history: List[dict]) -> Tuple[Optional[str], List[str]]:
    """Essaie chaque fournisseur configuré (DeepSeek, Groq) ; (None, []) si aucun ne répond -> repli sur les règles."""
    for nom, url, modele, cle in _fournisseurs():
        try:
            rep, outils = _boucle(nom, url, modele, cle, message, db, user, history)
            if rep:
                return rep, outils
        except Exception as exc:
            print(f"[SmartAgri] {nom} indisponible ({exc}) -> essai suivant / repli sur l'agent à règles")
    return None, []
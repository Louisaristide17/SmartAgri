"""
Route AgriBot — assistant IA agricole.
Utilise OpenAI GPT si la clé est configurée, sinon une base de règles locale.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os, re

from database import get_db
from models import Conversation, User
from schemas import MessageIn, MessageOut
from auth import get_current_user

router = APIRouter(prefix="/api/agribot", tags=["AgriBot"])

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

# ─── Base de connaissances locales ───────────────────────────────
KNOWLEDGE_BASE = [
    {
        "patterns": [r"rende?ment", r"production", r"récolte"],
        "response": (
            "📊 **Rendements moyens indicatifs au Sénégal :**\n\n"
            "| Culture    | Rendement moyen |\n"
            "|------------|-----------------|\n"
            "| Maïs       | 2.5 – 4.0 t/ha  |\n"
            "| Riz        | 3.5 – 5.0 t/ha  |\n"
            "| Arachide   | 1.5 – 2.5 t/ha  |\n"
            "| Mil        | 0.8 – 1.5 t/ha  |\n"
            "| Sorgho     | 1.0 – 2.0 t/ha  |\n\n"
            "💡 Utilisez l'outil **Prédiction** pour un calcul personnalisé à votre parcelle."
        )
    },
    {
        "patterns": [r"engrais", r"fertilisant", r"azote", r"NPK"],
        "response": (
            "🌿 **Recommandations en engrais :**\n\n"
            "• **Maïs** : Urée (46-0-0) à 50 kg/ha au stade V6, NPK 15-15-15 au semis\n"
            "• **Riz** : DAP au semis + urée en fractionnement (tallage + montaison)\n"
            "• **Arachide** : Peu d'azote (fixation symbiotique) — apporter phosphore et soufre\n\n"
            "⚠️ Respectez les doses agronomiques pour éviter la pollution des nappes phréatiques."
        )
    },
    {
        "patterns": [r"irrigation", r"eau", r"arrosage", r"pluviom"],
        "response": (
            "💧 **Besoins en eau des cultures :**\n\n"
            "• **Maïs** : 450-600 mm/saison — critique au stade floraison\n"
            "• **Riz irrigué** : 800-1200 mm/saison\n"
            "• **Arachide** : 300-500 mm/saison\n"
            "• **Mil/Sorgho** : 300-400 mm (très résistants à la sécheresse)\n\n"
            "🌧️ Consultez la météo dans le menu pour planifier vos irrigations."
        )
    },
    {
        "patterns": [r"semis", r"planter", r"planting", r"période", r"quand"],
        "response": (
            "📅 **Calendrier cultural (Sénégal) :**\n\n"
            "• **Mil/Sorgho** : juin – juillet (hivernage)\n"
            "• **Maïs** : juillet – août\n"
            "• **Arachide** : juin – juillet\n"
            "• **Riz pluvial** : juillet – août\n"
            "• **Riz irrigué** (vallée du fleuve) : mars – avril ou octobre – novembre\n\n"
            "📍 Les dates varient selon votre zone agro-écologique."
        )
    },
    {
        "patterns": [r"maladie", r"parasite", r"ravageur", r"insecte", r"champignon"],
        "response": (
            "🦠 **Principales maladies et ravageurs :**\n\n"
            "• **Maïs** : Striga (adventice), foreur des tiges, rouille\n"
            "• **Riz** : Pyriculariose, panachure jaune, borer\n"
            "• **Arachide** : Rosette (virus), cercosporiose, aflatoxine\n\n"
            "🔬 En cas de doute, prenez une photo de vos plantes et consultez un technicien agricole local."
        )
    },
    {
        "patterns": [r"sol", r"terre", r"argile", r"sableux", r"fertilit"],
        "response": (
            "🌍 **Types de sols au Sénégal :**\n\n"
            "• **Sol sableux (Dior)** : facile à travailler, faible rétention d'eau — bon pour arachide et mil\n"
            "• **Sol argileux (Deck)** : forte rétention d'eau — excellent pour riz et maraîchage\n"
            "• **Sol limoneux** : polyvalent, bon pour maïs et légumineuses\n"
            "• **Sol latéritique** : peu fertile, nécessite amendements organiques\n\n"
            "💡 Un test de sol en laboratoire coûte ~5 000 FCFA et peut doubler votre rendement."
        )
    },
    {
        "patterns": [r"météo", r"pluie", r"saison", r"hivernage", r"température"],
        "response": (
            "🌦️ **Consultez la section Météo** pour les prévisions en temps réel.\n\n"
            "Au Sénégal, on distingue :\n"
            "• **Saison des pluies (hivernage)** : juin – octobre\n"
            "• **Saison sèche froide** : novembre – février\n"
            "• **Saison sèche chaude** : mars – juin\n\n"
            "La variabilité climatique actuelle rend la prévision météo indispensable."
        )
    },
    {
        "patterns": [r"bonjour", r"salut", r"hello", r"bonsoir", r"hi"],
        "response": (
            "👋 **Bonjour ! Je suis AgriBot, votre assistant agricole.**\n\n"
            "Je peux vous aider sur :\n"
            "• 🌾 Les cultures et leurs besoins\n"
            "• 💧 L'irrigation et la pluviométrie\n"
            "• 🌿 Les engrais et la fertilité des sols\n"
            "• 📅 Les calendriers de semis\n"
            "• 🦠 Les maladies et ravageurs\n\n"
            "Posez-moi votre question !"
        )
    },
    {
        "patterns": [r"merci", r"thank", r"parfait", r"super", r"bravo"],
        "response": "😊 Avec plaisir ! N'hésitez pas si vous avez d'autres questions agricoles. Bonne récolte ! 🌾"
    },
]


def get_bot_response(message: str) -> str:
    """Retourne une réponse basée sur les règles locales."""
    msg_lower = message.lower()
    for item in KNOWLEDGE_BASE:
        for pattern in item["patterns"]:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                return item["response"]

    return (
        "🤔 Je n'ai pas de réponse précise à cette question.\n\n"
        "Essayez de me poser des questions sur :\n"
        "**engrais, irrigation, semis, maladies, rendement, sols, météo**\n\n"
        "Pour des conseils spécialisés, contactez un technicien agricole de votre région."
    )


async def get_openai_response(messages: list, user_message: str) -> str:
    """Appel OpenAI GPT-4 si la clé est disponible."""
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=OPENAI_KEY)

        system_prompt = """Tu es AgriBot, un assistant agricole expert spécialisé sur l'Afrique de l'Ouest.
Tu aides les agriculteurs avec des conseils pratiques sur les cultures, les sols, l'irrigation,
les engrais, les maladies et le calendrier cultural. Réponds en français, sois précis et bienveillant.
Ne donne pas de conseils sur les pesticides non homologués."""

        history = [{"role": "system", "content": system_prompt}]
        for msg in messages[-10:]:  # Garder les 10 derniers messages
            history.append({"role": msg["role"], "content": msg["content"]})
        history.append({"role": "user", "content": user_message})

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=history,
            max_tokens=800,
            temperature=0.7,
        )
        return response.choices[0].message.content

    except Exception as e:
        return get_bot_response(user_message)


@router.post("/message", response_model=MessageOut, summary="Envoyer un message à AgriBot")
async def send_message(
    payload: MessageIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Sauvegarder le message utilisateur
    user_msg = Conversation(
        user_id = current_user.id,
        role    = "user",
        content = payload.content,
    )
    db.add(user_msg)
    db.flush()

    # Récupérer l'historique récent
    history = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .limit(20)
        .all()
    )
    history_list = [{"role": m.role, "content": m.content} for m in reversed(history)]

    # Générer la réponse
    if OPENAI_KEY:
        response_text = await get_openai_response(history_list, payload.content)
    else:
        response_text = get_bot_response(payload.content)

    # Sauvegarder la réponse
    bot_msg = Conversation(
        user_id = current_user.id,
        role    = "assistant",
        content = response_text,
    )
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)

    return bot_msg


@router.get("/historique", response_model=List[MessageOut],
            summary="Historique de conversation")
def get_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.asc())
        .limit(limit)
        .all()
    )


@router.delete("/historique", status_code=204, summary="Effacer la conversation")
def clear_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(Conversation).filter(Conversation.user_id == current_user.id).delete()
    db.commit()

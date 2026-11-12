"""
Route AgriBot — assistant IA agricole.
Spécialisé sur l'agriculture en Côte d'Ivoire.
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
            "📊 **Rendements moyens indicatifs en Côte d'Ivoire :**\n\n"
            "| Culture    | Rendement moyen  |\n"
            "|------------|------------------|\n"
            "| Cacao      | 0.5 – 1.2 t/ha   |\n"
            "| Café       | 0.4 – 0.8 t/ha   |\n"
            "| Maïs       | 1.5 – 3.5 t/ha   |\n"
            "| Riz        | 2.0 – 4.5 t/ha   |\n"
            "| Manioc     | 8.0 – 15.0 t/ha  |\n"
            "| Igname     | 5.0 – 12.0 t/ha  |\n"
            "| Banane     | 10.0 – 25.0 t/ha |\n"
            "| Coton      | 1.0 – 2.0 t/ha   |\n\n"
            "💡 Utilisez l'outil **Prédiction** pour un calcul personnalisé à votre parcelle."
        )
    },
    {
        "patterns": [r"engrais", r"fertilisant", r"azote", r"NPK"],
        "response": (
            "🌿 **Recommandations en engrais pour la Côte d'Ivoire :**\n\n"
            "• **Cacao** : NPK 10-18-18 + magnésie, 300–500 kg/ha/an en 2 apports\n"
            "• **Maïs** : NPK 15-15-15 au semis (200 kg/ha) + urée au stade V6\n"
            "• **Riz** : DAP au semis + urée en 2 fractions (tallage et épiaison)\n"
            "• **Manioc** : NPK 13-13-21 (potassium élevé) pour améliorer les tubercules\n"
            "• **Igname** : Fumure organique privilégiée + NPK en complément\n\n"
            "⚠️ Respectez les doses recommandées par l'ANADER pour éviter la pollution des sols ivoiriens."
        )
    },
    {
        "patterns": [r"irrigation", r"eau", r"arrosage", r"pluviom"],
        "response": (
            "💧 **Besoins en eau des cultures en Côte d'Ivoire :**\n\n"
            "• **Cacao** : 1 200–2 000 mm/an — zones forestières humides\n"
            "• **Maïs** : 500–800 mm/saison — critique à la floraison\n"
            "• **Riz pluvial** : 800–1 200 mm/saison\n"
            "• **Manioc** : 750–1 000 mm/an — résistant à la sécheresse\n"
            "• **Coton** (Nord CI) : 700–1 000 mm/saison\n\n"
            "🌧️ Le Sud reçoit 1 400–2 500 mm/an (2 saisons), le Nord 900–1 200 mm (1 saison).\n"
            "Consultez la météo dans le menu pour planifier vos irrigations."
        )
    },
    {
        "patterns": [r"semis", r"planter", r"planting", r"période", r"quand", r"calendrier"],
        "response": (
            "📅 **Calendrier cultural en Côte d'Ivoire :**\n\n"
            "**Zone Sud (forêt, 2 saisons des pluies) :**\n"
            "• Grande saison : mars – juillet\n"
            "• Petite saison : septembre – novembre\n"
            "• **Cacao/Café** : entretien toute l'année, récolte oct – mars\n"
            "• **Maïs** : semis mars-avril (1ère saison) ou sept (2ème saison)\n"
            "• **Riz pluvial** : avril – mai\n\n"
            "**Zone Centre/Nord (savane, 1 saison) :**\n"
            "• Saison des pluies : mai – octobre\n"
            "• **Maïs** : semis mai – juin\n"
            "• **Coton** : semis juin – juillet\n"
            "• **Igname** : planting mars – avril\n\n"
            "📍 Consultez l'ANADER de votre région pour les recommandations locales."
        )
    },
    {
        "patterns": [r"maladie", r"parasite", r"ravageur", r"insecte", r"champignon", r"virus"],
        "response": (
            "🦠 **Principales maladies et ravageurs en Côte d'Ivoire :**\n\n"
            "• **Cacao** : Pourriture brune (Phytophthora), Swollen Shoot (virus), mirides (capsides)\n"
            "• **Café** : Scolyte des baies, anthracnose, rouille orangée\n"
            "• **Maïs** : Foreur des tiges (Busseola), Fall Armyworm (Spodoptera), Striga\n"
            "• **Riz** : Pyriculariose, borer du riz, virus de la panachure jaune\n"
            "• **Manioc** : Cochenille farineuse, mosaïque du manioc (CMD), bactériose\n\n"
            "🔬 En cas de doute, contactez l'ANADER (Agence Nationale d'Appui au Développement Rural)."
        )
    },
    {
        "patterns": [r"sol", r"terre", r"argile", r"sableux", r"fertilit", r"latérit"],
        "response": (
            "🌍 **Types de sols en Côte d'Ivoire :**\n\n"
            "• **Sol ferrallitique** (dominant, 70%) : bon pour cacao, café, hévéa — pH acide à corriger\n"
            "• **Sol hydromorphe** (bas-fonds) : excellent pour le riz irrigué\n"
            "• **Sol sableux côtier** : idéal pour cocotier, palmier à huile, maraîchage\n"
            "• **Sol gravillonnaire** (Nord) : pauvre, nécessite amendements — adapté au coton\n"
            "• **Sol alluvionnaire** (vallées) : très fertile, polyvalent\n\n"
            "💡 Un test de sol coûte ~15 000–30 000 FCFA à l'ANADER. Il peut doubler votre rendement."
        )
    },
    {
        "patterns": [r"météo", r"pluie", r"saison", r"climat", r"température", r"sécheresse"],
        "response": (
            "🌦️ **Consultez la section Météo** pour les prévisions en temps réel.\n\n"
            "**Climat de la Côte d'Ivoire :**\n"
            "• **Zone Sud (côtière)** : 2 saisons sèches / 2 saisons des pluies\n"
            "  - Grande saison des pluies : avril – juillet\n"
            "  - Petite saison sèche : août\n"
            "  - Petite saison des pluies : sept – novembre\n"
            "  - Grande saison sèche : décembre – mars\n\n"
            "• **Zone Nord (savane)** : 1 saison des pluies (mai–oct) + harmattan (nov–mars)\n\n"
            "La variabilité climatique est forte : utilisez la météo pour planifier vos travaux."
        )
    },
    {
        "patterns": [r"cacao", r"café", r"hévéa", r"palmier", r"anacarde", r"cajou"],
        "response": (
            "🍫 **Cultures de rente en Côte d'Ivoire :**\n\n"
            "• **Cacao** : 1er producteur mondial — Centre-Ouest, Sud-Ouest (Soubré, Daloa, San-Pédro)\n"
            "• **Café** : Centre et Ouest — variétés Robusta principalement\n"
            "• **Anacarde (cajou)** : Nord (Korhogo, Bondoukou) — 2ème producteur mondial\n"
            "• **Hévéa** : Centre et Sud-Ouest — caoutchouc naturel en forte expansion\n"
            "• **Palmier à huile** : Sud — huile de palme et palmiste\n\n"
            "🌱 Contactez le FIRCA ou votre coopérative locale pour les intrants subventionnés."
        )
    },
    {
        "patterns": [r"bonjour", r"salut", r"hello", r"bonsoir", r"hi"],
        "response": (
            "👋 **Bonjour ! Je suis AgriBot, votre assistant agricole pour la Côte d'Ivoire.**\n\n"
            "Je peux vous aider sur :\n"
            "• 🍫 Le cacao, café, anacarde et autres cultures ivoiriennes\n"
            "• 🌾 Le maïs, riz, manioc, igname\n"
            "• 💧 L'irrigation et la pluviométrie locale\n"
            "• 🌿 Les engrais et la fertilité des sols\n"
            "• 📅 Les calendriers culturaux (Sud, Centre, Nord)\n"
            "• 🦠 Les maladies et ravageurs\n\n"
            "Posez-moi votre question !"
        )
    },
    {
        "patterns": [r"anader", r"firca", r"coopérative", r"subvention", r"aide"],
        "response": (
            "🏛️ **Structures d'appui agricole en Côte d'Ivoire :**\n\n"
            "• **ANADER** : Agence Nationale d'Appui au Développement Rural — conseils techniques gratuits\n"
            "• **FIRCA** : Fonds Interprofessionnel pour la Recherche et le Conseil Agricoles\n"
            "• **CCC** : Conseil du Coton et de l'Anacarde (Nord)\n"
            "• **CGFCC** : Conseil Café-Cacao — régulation de la filière\n"
            "• **COOPAGRI CI** : réseau de coopératives agricoles\n\n"
            "📞 ANADER : +225 27 22 48 36 00 — présent dans toutes les régions."
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

        system_prompt = """Tu es AgriBot, un assistant agricole expert spécialisé sur la Côte d'Ivoire.
Tu aides les agriculteurs ivoiriens avec des conseils pratiques sur les cultures locales (cacao, café,
anacarde, maïs, riz, manioc, igname, coton, palmier à huile, hévéa), les sols, l'irrigation,
les engrais, les maladies et le calendrier cultural ivoirien. Cite les structures locales (ANADER,
FIRCA, CCC, CGFCC) quand c'est utile. Réponds en français, sois précis et bienveillant.
Ne donne pas de conseils sur les pesticides non homologués en Côte d'Ivoire."""

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

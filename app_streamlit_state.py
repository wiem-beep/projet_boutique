
"""
Interface Streamlit — version avec state.

L'historique, les actions en attente et le journal
sont lus directement dans l'état du graphe (app.get_state).

Lancement :
uv run streamlit run app_streamlit_state.py
"""

import uuid
from pathlib import Path

import streamlit as st

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from agent_boutique_state import app
from outils_base import creer_base


# ---------- Configuration ----------
st.set_page_config(
    page_title="Service client boutique",
    page_icon="🛒",
    layout="wide"
)


# ---------- Initialisation de la base ----------
@st.cache_resource
def initialiser_base():
    creer_base()


initialiser_base()


# ---------- Initialisation de la conversation ----------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

config = {
    "configurable": {
        "thread_id": st.session_state.thread_id
    }
}

# Récupération de l'état du graphe
snapshot = app.get_state(config)

etat = snapshot.values or {}

# Vérifier si le graphe est en pause pour une validation humaine
actions = (
    snapshot.interrupts[0].value
    if snapshot.interrupts
    else None
)

# Variable pour savoir quelle action envoyer au graphe
envoi_au_graphe = None


# ---------- Barre latérale ----------
with st.sidebar:

    st.header("🛒 Boutique")

    st.caption(
        "Agent LangGraph : RAG + SQL + validation humaine"
    )

    # Nouvelle conversation
    if st.button(
        "Nouvelle conversation",
        use_container_width=True
    ):
        creer_base()

        st.session_state.clear()

        st.rerun()

    # Affichage du graphe de l'agent
    with st.expander("Graphe de l'agent"):

        chemin_image = Path(__file__).parent / "graphe_agent.png"

        if chemin_image.exists():
            st.image(
                str(chemin_image),
                caption="Architecture de l'agent LangGraph",
                use_container_width=True
            )
        else:
            st.warning(
                "Image graphe_agent.png introuvable. "
                "Place cette image dans le dossier du projet."
            )

    # État du graphe
    st.subheader("État du graphe")

    st.metric(
        "Appels au LLM",
        etat.get("nb_appels_llm", 0)
    )

    # Journal des validations
    st.markdown("**Journal des validations**")

    journal = etat.get("journal", [])

    if journal:
        for ligne in journal:
            st.markdown(f"- {ligne}")
    else:
        st.caption("Aucune action sensible.")

    # Questions proposées
    st.subheader("Questions à essayer")

    st.markdown(
        "- Quels sont les délais de livraison ?\n"
        "- Où en est la commande 1002 ?\n"
        "- Annule ma commande 1001\n"
        "- J'ai reçu la commande 1003 mais la souris "
        "ne marche pas, je peux la retourner ?\n"
        "- Je veux retourner la commande 1004, "
        "le casque ne me plaît plus."
    )


# ---------- Conversation ----------
st.title("🛒 Service client boutique")

st.caption(
    "Posez vos questions à notre assistant intelligent."
)

# Lire et afficher les messages enregistrés dans le graphe
for message in etat.get("messages", []):

    if message.type == "human":
        role = "user"

    elif message.type == "ai":
        role = "assistant"

    else:
        continue

    contenu = getattr(message, "content", "")

    # Ignorer les messages vides (appels d'outils)
    if contenu:
        with st.chat_message(role):
            st.markdown(str(contenu))


# ---------- Validation humaine ----------
if actions:

    st.warning("⚠️ Une validation humaine est requise.")

    st.markdown("**Détails de l'action à valider :**")

    if isinstance(actions, (list, tuple)):
        for action in actions:
            st.markdown(f"- `{action}`")
    else:
        st.markdown(f"- `{actions}`")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "✅ Valider",
            use_container_width=True
        ):
            envoi_au_graphe = Command(resume="oui")

    with col2:
        if st.button(
            "❌ Refuser",
            use_container_width=True
        ):
            envoi_au_graphe = Command(resume="non")


# ---------- Saisie de la question ----------
question = st.chat_input(
    "Votre question...",
    disabled=bool(actions)
)

if question:

    with st.chat_message("user"):
        st.markdown(question)

    envoi_au_graphe = {
        "messages": [
            HumanMessage(content=question)
        ]
    }


# ---------- Exécution du graphe ----------
if envoi_au_graphe is not None:

    with st.spinner("L'agent réfléchit..."):

        # Exécuter le graphe ou reprendre après validation
        app.invoke(
            envoi_au_graphe,
            config=config
        )

    # Actualiser l'interface avec le nouvel état
    st.rerun()

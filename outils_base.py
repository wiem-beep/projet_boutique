import sqlite3
from langchain_core.tools import tool
BASE = "boutique.db"

def creer_base():
    """(Re)crée la base avec quelques commandes de démonstration."""
    con = sqlite3.connect(BASE)
    con.executescript(
        """
        DROP TABLE IF EXISTS retours;
        DROP TABLE IF EXISTS commandes;
        CREATE TABLE commandes (
        id INTEGER PRIMARY KEY,
        client TEXT,
        produit TEXT,
        montant REAL,
        statut TEXT,
        date_livraison TEXT
        );
        CREATE TABLE retours (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        commande_id INTEGER REFERENCES commandes(id),
        motif TEXT,
        date_demande TEXT DEFAULT (date('now'))
        );
        INSERT INTO commandes VALUES
        (1001, 'Amine Trabelsi', 'Clavier mécanique', 120.0, 'en
        préparation', NULL),
        (1002, 'Sarra Ben Ali', 'Écran 24 pouces', 450.0,
        'expédiée', NULL),
        (1003, 'Yassine Kammoun', 'Souris sans fil', 35.0,
        'livrée', date('now', '-10 days')),
        (1004, 'Mariem Gargouri', 'Casque audio', 89.0,
        'livrée', date('now', '-30 days'));
        """
    )
    con.commit()
    con.close()

@tool
def consulter_commande(numero: int) -> str:
    """Donne le client, le produit, le montant, le statut et la date de
    livraison d'une commande."""
    con = sqlite3.connect(BASE)
    ligne = con.execute(
        "SELECT id, client, produit, montant, statut, date_livraison, "
        "CAST(julianday('now') - julianday(date_livraison) AS INTEGER) "
        "FROM commandes WHERE id = ?",
        (numero,),
    ).fetchone()
    con.close()
    if ligne is None:
     return f"Aucune commande n° {numero}."
    texte = (f"Commande {ligne[0]} : client {ligne[1]}, produit{ligne[2]}, "
        f"montant {ligne[3]:.3f} DT, statut '{ligne[4]}'")
    if ligne[5]:
        texte += f", livrée le {ligne[5]} (il y a {ligne[6]} jours)"
    return texte + "."


@tool
def annuler_commande(numero: int) -> str:
    """Annule une commande. Possible seulement si son statut est 'en
    préparation'."""
    con = sqlite3.connect(BASE)
    ligne = con.execute("SELECT statut FROM commandes WHERE id = ?",
    (numero,)).fetchone()
    if ligne is None:
        con.close()
        return f"Aucune commande n° {numero}."
    if ligne[0] != "en préparation":
        con.close()
        return f"Impossible : la commande {numero} a le statut'{ligne[0]}'."
    con.execute("UPDATE commandes SET statut = 'annulée' WHERE id = ?",
    (numero,))
    con.commit()
    con.close()
    return f"La commande {numero} a été annulée."

@tool
def creer_retour(numero: int, motif: str) -> str:
    """Enregistre une demande de retour pour une commande livrée, avec le
    motif du client."""
    con = sqlite3.connect(BASE)
    ligne = con.execute("SELECT statut FROM commandes WHERE id = ?",
    (numero,)).fetchone()
    if ligne is None:
        con.close()
        return f"Aucune commande n° {numero}."
    if ligne[0] != "livrée":
        con.close()
        return f"Impossible : la commande {numero} a le statut'{ligne[0]}'."
    con.execute("INSERT INTO retours (commande_id, motif) VALUES (?, ?)",
    (numero, motif))
    con.execute("UPDATE commandes SET statut = 'retour demandé' WHERE id =?", (numero,))
    con.commit()
    con.close()
    return f"Demande de retour enregistrée pour la commande {numero}(motif : {motif})."
OUTILS_SQL = [consulter_commande, annuler_commande, creer_retour]
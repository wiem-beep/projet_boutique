
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Charger les variables du fichier .env
load_dotenv()

FICHIER_PDF = os.getenv("FICHIER_PDF", "politique_boutique.pdf")
EMBEDDINGS = os.getenv("EMBEDDINGS", "gemini-embedding-001")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
COLLECTION = os.getenv("COLLECTION", "politique_boutique")


def connecter_chroma():
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDINGS)

    return Chroma(
        collection_name=COLLECTION,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )


if __name__ == "__main__":

    # 1. CHARGEMENT DU PDF
    docs = PyPDFLoader(FICHIER_PDF).load()
    print("Pages chargées :", len(docs))

    # 2. DÉCOUPAGE (CHUNKING)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(docs)
    print("Chunks :", len(chunks))

    # 3. EMBEDDINGS GEMINI + 4. STOCKAGE CHROMADB
    db = connecter_chroma()

    # Vider la collection avant de créer un nouvel index
    db.reset_collection()

    db.add_documents(chunks)

    print(
        f"Index ChromaDB créé : {len(chunks)} chunks "
        f"dans '{COLLECTION}' ({CHROMA_DIR})"
    )

    # 5. TEST RAPIDE DU RETRIEVER
    question = "Puis-je retourner un produit après 20 jours ?"

    print(f"\nTest : {question}")

    for doc in db.similarity_search(question, k=2):
        print(" •", doc.page_content.replace("\n", " ")[:120], "...")

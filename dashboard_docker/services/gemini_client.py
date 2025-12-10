import os
from google import genai


def get_gemini_client():
    """
    Client Gemini initialisé avec la clé GEMINI_API_KEY.
    Couche 'infrastructure', aucune logique métier ici.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("La variable d'environnement GEMINI_API_KEY n'est pas définie.")

    client = genai.Client(api_key=api_key)
    return client

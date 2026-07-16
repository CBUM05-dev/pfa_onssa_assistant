# ONSSA Chat Demo

Demo frontend isolee pour presenter le vertical slice RAG sans modifier l'architecture backend.

## Lancer le backend

Depuis la racine du projet:

```powershell
$env:ONSSA_QDRANT_HOST="127.0.0.1"
$env:ONSSA_GROQ_API_KEY="..."
$env:PYTHONPATH="src"
uvicorn onssa_ai.api.app:app --reload
```

## Lancer la demo

Dans un deuxieme terminal:

```powershell
python demo/onssa-chat/server.py
```

Ouvrir:

```text
http://127.0.0.1:5500
```

La page appelle le backend via le proxy local:

```text
/api/rag/answer -> http://127.0.0.1:8000/api/v1/rag/answer
```

Si le backend n'est pas disponible, l'interface affiche une reponse exemple pour permettre la demonstration visuelle.

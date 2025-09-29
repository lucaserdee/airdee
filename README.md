# airdee – EMG AI Tooling

Deze repository bevat referentiecode en documentatie voor het bouwen van een
AI-assistent die uitsluitend antwoord geeft op basis van content uit de
Weaviate-vector database van de Erdee Media Groep (EMG). De oplossing combineert
Weaviate, Azure OpenAI en een n8n workflow.

## Inhoud

- `src/airdee/` – Python helpers om data veilig uit Weaviate te halen en de
  Azure OpenAI agent aan te sturen.
- `docs/` – Architectuuroverzicht en stap-voor-stap uitleg voor de n8n
  workflow.
- `workflows/` – Importeerbaar n8n workflow bestand dat de volledige
  interactie automatiseert.
- `.env.example` – Voorbeeld van de omgevingvariabelen (inclusief Weaviate API-key)
  die n8n en de Python scripts nodig hebben.

Lees `docs/workflow_setup.md` voor de installatie-instructies van de n8n
workflow en `docs/architecture.md` voor het overzicht van de componenten.

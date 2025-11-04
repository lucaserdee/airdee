# n8n Workflow Setup

Volg onderstaande stappen om de workflow `EMG AI Agent` in n8n te installeren
en te configureren.

## 1. Voorbereiding

1. Zorg dat n8n draait met toegang tot de omgeving waar Weaviate en Azure
   OpenAI bereikbaar zijn.
2. Maak in n8n twee credentials aan:
   - **WEAVIATE_API_KEY**: HTTP Header authenticatie met `X-API-Key` en de
     token uit Weaviate.
   - **AZURE_OPENAI**: Azure OpenAI credential met endpoint, API-key en
     standaard `gpt-4o` of `gpt-35-turbo` deployment.
3. Zet de volgende environment variables in n8n (bijv. via `.env` of docker
   `-e`):

   | Variable | Betekenis |
   | --- | --- |
   | `WEAVIATE_URL` | Base URL van de Weaviate instance, bijv. `https://weaviate.example.com` |
   | `WEAVIATE_COLLECTION` | Naam van de collection/class waar artikelen in staan |
   | `WEAVIATE_API_KEY` | API key voor authenticatie tegen Weaviate (wordt meegegeven als `X-API-Key`) |
   | `WEAVIATE_TRAILING_METADATA` | Aantal extra waarden aan het einde van de vector die verwijderd moeten worden (standaard `2`) |
   | `WEAVIATE_EXPECTED_VECTOR_SIZE` | Optioneel, aantal waarden dat na het knippen moet overblijven |
   | `AZURE_OPENAI_DEPLOYMENT` | Naam van de Azure OpenAI deployment |

## 2. Workflow importeren

1. Download `workflows/n8n_emg_ai_agent.json` uit deze repository.
2. Ga in n8n naar **Workflows → Import from File** en selecteer het JSON-bestand.
3. Controleer of de nodes correct gekoppeld zijn en wijs de aangemaakte
   credentials toe aan de juiste nodes.

## 3. Werking van de workflow

1. **Chat webhook**: ontvangt een POST met ten minste `question` en
   `articleUuid`.
2. **Select article**: valideert dat de UUID aanwezig is en zet het door naar
   Weaviate.
3. **Fetch article**: doet een `GET` request naar Weaviate om de properties en
   vector op te halen. Zorg dat `include=vector` in de dataset geactiveerd is.
4. **Normalise vector**: verwijdert de twee extra waarden die tijdens de import
   zijn toegevoegd en controleert het uiteindelijke formaat.
5. **AI Agent**: roept Azure OpenAI aan met de aangeleverde context en vraag.
6. **Return answer**: stuurt het antwoord terug naar de webhook caller.

## 4. Payload voorbeeld

```json
{
  "question": "Wat is de kern van het artikel?",
  "articleUuid": "d3f99d18-0f7b-4c3a-9a2f-ef8d0a6c1234"
}
```

De response bevat standaard het antwoord van het taalmodel en kan indien nodig
met extra metadata uitgebreid worden.

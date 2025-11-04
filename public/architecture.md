# EMG AI Tool Architectuur

Deze repository bevat een referentie-implementatie voor een AI-hulpmiddel dat
vragen van redacteuren beantwoordt op basis van content in de Erdee Media Groep
(EMG) kennisbank. De oplossing bestaat uit drie hoofdonderdelen:

1. **Weaviate vector database** – Bevat de artikelen en hun bijbehorende
   embeddings. De `WeaviateRetriever` in `src/airdee/weaviate_retriever.py`
   haalt veilig zowel de artikeltekst als de vector op en verwijdert eventuele
   meta-informatie die tijdens het importeren aan het einde van de vector werd
   toegevoegd.
2. **Azure OpenAI** – Leverancier van de taalmodellen die de vragen
   beantwoorden. De `ArticleAnsweringAgent` in `src/airdee/ai_agent.py` maakt
   een `chat completion`-aanvraag met een systeemprompt die expliciet vermeldt
   dat antwoorden uitsluitend uit de Weaviate-bron komen.
3. **n8n workflow** – Orkestreert de interactie tussen de chat-interface,
   Weaviate en Azure OpenAI. Het JSON-bestand in `workflows/n8n_emg_ai_agent.json`
   kan geïmporteerd worden in n8n om de nodes en datastromen direct
   beschikbaar te maken.

Het geheel ziet er als volgt uit:

```text
Gebruiker -> n8n Trigger -> WeaviateRetriever -> Azure OpenAI -> Antwoord
```

Elke component is modulair opgezet zodat authenticatiegegevens en modellen
kunnen worden verwisseld zonder de hoofdlogica aan te passen.

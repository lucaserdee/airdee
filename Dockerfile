FROM python:3.12-slim
WORKDIR /app

# kopieer webserver en frontend
COPY app_stdlib.py ./app_stdlib.py
COPY public ./public

# standaardvariabelen
ENV PORT=6789
ENV N8N_WEBHOOK_URL="http://n8n.rd.local/webhook/ai-chatbot"

EXPOSE 6789
CMD ["python", "app_stdlib.py"]

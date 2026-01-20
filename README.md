# FinanceMail — Classificador de E-mails (MVP)

O **FinanceMail** é um MVP que classifica e-mails automaticamente como **produtivo** (demanda financeira/documental) ou **improdutivo** (social/conversa), calcula **confiança**, sugere uma **resposta pronta** e coleta **feedback** do usuário para evoluir o modelo.

> **Objetivo:** reduzir ruído em caixas de entrada e acelerar a triagem de mensagens ligadas a **pagamento, boleto, DANFE, nota fiscal, vencimento, valor, PIX**, etc.

---

## ✨ Funcionalidades

- **Classificação**: `produtivo` vs `improdutivo`
- **Confiança**: score numérico + nível (baixa / média / alta)
- **Resposta sugerida** (gerada por LLM)
- **Feedback do usuário** gravado em arquivo `.jsonl`
- **Histórico local (últimos 10)** no navegador (`localStorage`)
- **UI simples e “demo-ready”** (React + Vite)

---

## 🧠 Como funciona (arquitetura)

Frontend (React + Vite)
└── chama /api/*
(proxy do Vite evita CORS em dev)
↓
Backend (FastAPI)
├── Modelo local (TF-IDF + Logistic Regression)
│ └── categoria + confiança
├── (opcional) LLM como “segunda opinião”
│ └── usado apenas quando a confiança é baixa
├── LLM gera a resposta sugerida
└── Feedback → grava em feedback/feedback.jsonl



---

## 🧰 Stack

### Backend
- FastAPI
- scikit-learn (TF-IDF + Logistic Regression)
- joblib (artefatos do modelo)
- HuggingFace Hub (`InferenceClient`) para LLM
- python-dotenv

### Frontend
- React + Vite
- Fetch API
- localStorage

---

## 📁 Estrutura do projeto


FinanceMail/
├── backend/
│ ├── app/
│ │ ├── main.py
│ │ ├── rl_model.py
│ │ ├── ai_client.py
│ │ ├── feedback_store.py
│ │ ├── text_rules.py
│ │ └── sample_training_data.py
│ ├── requirements.txt
│ ├── feedback/
│ │ └── feedback.jsonl # gerado em runtime
│ └── artifacts/ # modelos e pipeline
└── frontend/
├── src/
│ ├── App.jsx
│ ├── api.js
│ └── ...
└── vite.config.js




---

## ▶️ Rodando localmente

### 1) Backend (FastAPI)

```bash
cd backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

# Crie o .env com o token do HuggingFace (necessário para o LLM)
echo "HF_TOKEN=SEU_TOKEN_AQUI" > .env

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

---

Backend

Health: http://127.0.0.1:8000/status

Swagger: http://127.0.0.1:8000/docs

2) Frontend (React + Vite)
cd ../frontend
npm install
npm run dev


Frontend

http://localhost:5173

Em desenvolvimento, o frontend chama o backend via proxy:
/api → http://127.0.0.1:8000 (sem problemas de CORS).

🔑 Variáveis de ambiente
Backend (backend/.env)

HF_TOKEN — token do HuggingFace para chamar o LLM
(geração de resposta e/ou segunda opinião conforme regra do backend)

Frontend (opcional)

VITE_API_BASE — por padrão o app usa "/api"

🔌 API (principais endpoints)
POST /classificar

Classifica um texto de e-mail e devolve categoria, confiança e resposta sugerida.

Request

{
  "texto": "Segue boleto e DANFE para pagamento. Valor 430, vencimento 20/01."
}


Response (exemplo)

{
  "categoria": "produtivo",
  "confianca": 0.65,
  "fonte": "modelo",
  "resposta": "Prezado(a), ...",
  "categoria_modelo": "produtivo",
  "confianca_modelo": 0.65
}

POST /feedback

Grava um feedback do usuário para uso futuro.

Request

{
  "texto": "Teste UI",
  "previsto": "produtivo",
  "correto": "improdutivo"
}


Response

{ "ok": true }


Arquivo gerado

backend/feedback/feedback.jsonl

🧪 Teste rápido (curl)
curl -X POST "http://127.0.0.1:8000/classificar" \
  -H "Content-Type: application/json" \
  -d '{"texto":"Feliz natal! Obrigado pelo atendimento :)"}'

curl -X POST "http://127.0.0.1:8000/feedback" \
  -H "Content-Type: application/json" \
  -d '{"texto":"Teste UI","previsto":"produtivo","correto":"improdutivo"}'

📌 Decisões de produto (MVP)

Modelo local faz a classificação (rápido e barato)

LLM é usado para:

gerar a resposta sugerida

atuar como “validação” apenas quando faz sentido (regra no backend)

Feedback é salvo em .jsonl para evolução e retreino posterior

⚠️ Limitações (atuais)

Dataset inicial é pequeno → casos ambíguos podem errar

Feedback ainda não está automatizado em um pipeline de retreino

Não processa anexos (PDF/DANFE) — apenas texto (por enquanto)

🛣️ Roadmap (próximos passos)

Retreino periódico usando feedback.jsonl

Dashboard de métricas (acurácia, matriz de confusão, drift)

Upload de PDF/anexo e extração de texto

Regras melhores para reduzir falsos positivos

Deploy público (backend + frontend)

🚀 Deploy (visão geral)
Backend (Render — Web Service)

Variável de ambiente: HF_TOKEN

Start command:

uvicorn app.main:app --host 0.0.0.0 --port 10000

Frontend (Vercel ou Render — Static Site)

Build:

npm run build


Output: dist

📄 Licença

Projeto de demonstração / MVP.


---

Se quiser, no próximo passo eu posso:
- adicionar **seção “Impacto / Resultados” (estilo recrutador)**  
- escrever o **roteiro do vídeo de apresentação (3–5 minutos)**  
- ou adaptar o README para **vaga de trainee/júnior** com linguagem estratégica para RH e tech lead.

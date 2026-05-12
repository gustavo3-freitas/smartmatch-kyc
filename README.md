# SmartMatch KYC

Plataforma de compliance financeiro com dois módulos integrados:
- **KYC** — deduplicação de cadastros de clientes com NLP e matching aproximado
- **CSAT** — análise de feedback e cálculo automático de NPS

Desenvolvido como solução end-to-end: pipeline de dados em Python, API REST com FastAPI e dashboard em React.

---

## Arquitetura

React Dashboard
↓ HTTP POST
FastAPI (REST API)
↓
NLP Pipeline (spaCy + NLTK)
↓
Matching Engine (Levenshtein + Blocking)
↓
Resultados + Métricas
↓
AWS S3 (storage + audit trail)

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python, FastAPI, uvicorn |
| NLP | spaCy, NLTK |
| Matching | python-levenshtein |
| Dados | Pandas, NumPy |
| Frontend | React |
| Cloud | AWS S3, boto3 |
| Documentação | Swagger (automático via FastAPI) |

---

## Módulos

### 1. KYC — Deduplicação de Clientes

Detecta registros duplicados em bases de clientes financeiros.

**Pipeline:**
1. Normalização de nomes com spaCy (lematização, remoção de stopwords, acentos)
2. Blocking por prefixo — reduz comparações de O(n²) para O(k)
3. Distância de Levenshtein para similaridade entre pares
4. Threshold configurável (padrão: 82%)

**Métricas no dataset de 5.237 registros:**
- Precision: 79.1%
- Recall: 61.8%
- F1 Score: 69.4%

**Decisão técnica:** Levenshtein foi escolhido sobre embeddings porque o problema é correspondência de nomes com erros de digitação e abreviações — não similaridade semântica. Para o volume atual, blocking + Levenshtein é mais preciso e 10x mais rápido.

### 2. CSAT — NPS Analytics

Analisa feedback textual de clientes e calcula NPS automaticamente.

**Pipeline:**
1. Classificação de sentimento com NLTK (positivo / neutro / negativo)
2. Cálculo de NPS Score (promotores - detratores / total × 100)
3. Extração de temas por frequência de tokens
4. Segmentação por canal e produto

**Contexto real:** pipeline desenvolvido com base na experiência de análise de CSAT na Claro, onde dados originados na AWS são processados via Oracle e analisados em Python.

---

## Como Rodar

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m spacy download pt_core_news_sm
python -m spacy download en_core_web_sm
python -m uvicorn main:app --reload
```
API disponível em: `http://localhost:8000`
Documentação Swagger: `http://localhost:8000/docs`

### Frontend
```bash
cd frontend
npm install
npm start
```
Dashboard disponível em: `http://localhost:3000`

---

## Endpoints

| Método | Endpoint | Descrição |
|---|---|---|
| GET | /health | Status da API |
| POST | /match | Deduplicação KYC |
| POST | /match/export | Resultado como CSV |
| POST | /csat | Análise NPS/CSAT |
| POST | /stats | Estatísticas do dataset |
| POST | /match/s3 | Match com upload para S3 |

---

## Contexto Financeiro

Em ambiente bancário internacional, cada componente tem papel regulatório:

- **S3 + versionamento** — durabilidade de documentos KYC exigida por regulação
- **KMS encryption** — criptografia em repouso (LGPD, GDPR)
- **CloudTrail** — audit trail de todas as operações
- **VPC** — isolamento de rede para dados sensíveis
- **IAM Roles** — controle de acesso sem credenciais hardcoded

---

## Dataset

Dataset sintético de 5.237 registros gerado com 19 tipos de ruído real:
abreviações, erros de digitação, transposição de letras, encoding quebrado,
acentos trocados, prefixos, hifenização, conectivos e truncamento.
Distribuído em 5 países: BR, US, GB, DE, ES.
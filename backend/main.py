# %% Imports
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import json

from nlp_pipeline import preprocessar
from matching import encontrar_duplicatas, avaliar_pipeline

# %% App

app = FastAPI(
    title="SmartMatch KYC API",
    description="Pipeline de deduplicação de clientes para compliance financeiro.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# %% Health check

@app.get("/health", tags=["Sistema"])
def health():
    """Verifica se a API está rodando."""
    return {"status": "ok", "version": "1.0.0"}

# %% Endpoint principal — match

@app.post("/match", tags=["Matching"])
async def match_records(
    file: UploadFile = File(..., description="CSV com colunas: id, name, country, document"),
    threshold: float = Query(default=0.82, ge=0.0, le=1.0, description="Similaridade mínima (0.0 a 1.0)")
):
    """
    Recebe um CSV de clientes e retorna pares de duplicatas detectados.
    
    - **threshold**: 0.82 é o padrão. Aumentar reduz falsos positivos. Diminuir aumenta recall.
    """
    # Lê o arquivo
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))

    # Valida colunas obrigatórias
    required = {"id", "name", "country"}
    missing = required - set(df.columns)
    if missing:
        return {"error": f"Colunas obrigatórias ausentes: {missing}"}

    # Preprocessa
    registros = []
    for _, row in df.iterrows():
        registros.append({
            "id":             int(row["id"]),
            "name":           str(row["name"]),
            "name_processed": preprocessar(str(row["name"]), str(row.get("country", "US"))),
            "country":        str(row.get("country", "US")),
            "document":       str(row.get("document", "")),
            "cluster_id":     int(row.get("cluster_id", 0)),
            "is_duplicate":   int(row.get("is_duplicate", 0)),
        })

    # Matching
    matches = encontrar_duplicatas(registros, threshold=threshold)

    # Métricas (só se tiver ground truth)
    metricas = None
    if "is_duplicate" in df.columns and "cluster_id" in df.columns:
        metricas = avaliar_pipeline(df, matches)

    return {
        "summary": {
            "total_records":    len(registros),
            "threshold":        threshold,
            "matches_found":    len(matches),
        },
        "metrics":  metricas,
        "matches":  matches[:200],  # Limita resposta a 200 matches
    }

# %% Endpoint — estatísticas do dataset

@app.post("/stats", tags=["Dados"])
async def dataset_stats(
    file: UploadFile = File(...)
):
    """Retorna estatísticas descritivas do dataset enviado."""
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))

    stats = {
        "total_records": len(df),
        "columns":       list(df.columns),
        "countries":     df["country"].value_counts().to_dict() if "country" in df.columns else {},
        "duplicates":    int(df["is_duplicate"].sum()) if "is_duplicate" in df.columns else None,
        "missing_names": int(df["name"].isna().sum()) if "name" in df.columns else 0,
        "sample":        df.head(5).to_dict(orient="records"),
    }
    return stats


# %% Endpoint - CSAT

# %% Endpoint CSAT
from csat_pipeline import analisar_csat

@app.post("/csat", tags=["CSAT"])
async def analisar_feedback(
    file: UploadFile = File(..., description="CSV com colunas: comentario, nps_score, canal, produto")
):
    """
    Analisa feedback de clientes e calcula NPS.
    Retorna sentimentos, temas de insatisfação e NPS por canal.
    """
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))

    colunas_necessarias = {"comentario", "nps_score"}
    faltando = colunas_necessarias - set(df.columns)
    if faltando:
        return {"error": f"Colunas ausentes: {faltando}"}

    resultado = analisar_csat(df)
    return resultado

# %% Endpoint — integração S3
from s3_integration import upload_arquivo, listar_uploads

@app.post("/match/s3", tags=["AWS S3"])
async def match_com_s3(
    file: UploadFile = File(...),
    threshold: float = Query(default=0.82, ge=0.0, le=1.0)
):
    """
    Versão produção: salva o arquivo no S3 antes de processar.
    Garante rastreabilidade e audit trail para compliance financeiro.
    """
    contents = await file.read()

    # 1. Salva no S3 (audit trail)
    s3_info = upload_arquivo(contents, file.filename, tipo="kyc")

    # 2. Processa igual ao endpoint /match
    df = pd.read_csv(io.BytesIO(contents))
    registros = []
    for _, row in df.iterrows():
        registros.append({
            "id":             int(row["id"]),
            "name":           str(row["name"]),
            "name_processed": preprocessar(str(row["name"]), str(row.get("country", "US"))),
            "country":        str(row.get("country", "US")),
            "document":       str(row.get("document", "")),
            "cluster_id":     int(row.get("cluster_id", 0)),
            "is_duplicate":   int(row.get("is_duplicate", 0)),
        })

    matches = encontrar_duplicatas(registros, threshold=threshold)
    metricas = None
    if "is_duplicate" in df.columns and "cluster_id" in df.columns:
        metricas = avaliar_pipeline(df, matches)

    return {
        "s3":      s3_info,
        "summary": {
            "total_records": len(registros),
            "matches_found": len(matches),
            "threshold":     threshold,
        },
        "metrics": metricas,
        "matches": matches[:200],
    }

# %% Endpoint — exportar resultado como CSV

@app.post("/match/export", tags=["Matching"])
async def match_and_export(
    file: UploadFile = File(...),
    threshold: float = Query(default=0.82, ge=0.0, le=1.0)
):
    """Roda o matching e retorna um CSV com os resultados para download."""
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))

    registros = []
    for _, row in df.iterrows():
        registros.append({
            "id":             int(row["id"]),
            "name":           str(row["name"]),
            "name_processed": preprocessar(str(row["name"]), str(row.get("country", "US"))),
            "country":        str(row.get("country", "US")),
            "document":       str(row.get("document", "")),
            "cluster_id":     int(row.get("cluster_id", 0)),
            "is_duplicate":   int(row.get("is_duplicate", 0)),
        })

    matches = encontrar_duplicatas(registros, threshold=threshold)
    df_matches = pd.DataFrame(matches)

    # Retorna como CSV para download
    output = io.StringIO()
    df_matches.to_csv(output, index=False)
    output.seek(0)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=matches.csv"}
    )
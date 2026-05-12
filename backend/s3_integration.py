import boto3
import os
from datetime import datetime

# ─── Configuração ─────────────────────────────────────────────────────────────
# Em produção: variáveis de ambiente ou IAM Role (nunca hardcoded)
# AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY via .env ou role attached

BUCKET_NAME = "smartmatch-kyc-uploads"
REGION      = "us-east-1"

def get_s3_client():
    """
    Em produção financeira usa IAM Role — sem credenciais hardcoded.
    Localmente usa variáveis de ambiente.
    """
    return boto3.client("s3", region_name=REGION)

def upload_arquivo(file_bytes: bytes, filename: str, tipo: str = "kyc") -> dict:
    """
    Faz upload de arquivo para S3.
    
    Estrutura de pastas:
    - kyc/2024-01-15/customers.csv
    - csat/2024-01-15/feedback.csv
    
    Em ambiente financeiro real:
    - Server-side encryption com KMS
    - Versionamento ativado
    - CloudTrail para audit log
    """
    s3 = get_s3_client()
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    s3_key = f"{tipo}/{data_hoje}/{filename}"

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=file_bytes,
        # Em produção financeira adicionaria:
        # ServerSideEncryption="aws:kms",
        # SSEKMSKeyId="arn:aws:kms:...",
        Metadata={
            "tipo":      tipo,
            "data":      data_hoje,
            "filename":  filename,
        }
    )

    return {
        "bucket":   BUCKET_NAME,
        "key":      s3_key,
        "url":      f"s3://{BUCKET_NAME}/{s3_key}",
        "regiao":   REGION,
    }

def listar_uploads(tipo: str = "kyc") -> list[dict]:
    """Lista arquivos já processados no bucket."""
    s3 = get_s3_client()
    response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=f"{tipo}/"
    )
    arquivos = []
    for obj in response.get("Contents", []):
        arquivos.append({
            "key":            obj["Key"],
            "tamanho_bytes":  obj["Size"],
            "ultima_modificacao": obj["LastModified"].strftime("%Y-%m-%d %H:%M"),
        })
    return arquivos

def baixar_arquivo(s3_key: str) -> bytes:
    """Baixa arquivo do S3 para processamento."""
    s3 = get_s3_client()
    response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
    return response["Body"].read()
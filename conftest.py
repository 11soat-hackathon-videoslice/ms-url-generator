"""Configurações e fixtures compartilhadas para os testes"""
import pytest
import sys
import os
from pathlib import Path

os.environ.setdefault('AWS_REGION', 'us-east-1')
os.environ.setdefault('S3_BUCKET_NAME', 'test-bucket-url-generator')
os.environ.setdefault('S3_URL_DOWNLOAD_EXPIRATION', '3600')
os.environ.setdefault('S3_URL_UPLOAD_EXPIRATION', '900')
os.environ.setdefault('S3_BUCKET_DIR_UPLOADS', 'uploads/')
os.environ.setdefault('S3_BUCKET_DIR_FINISHED', 'finished/')

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

@pytest.fixture
def mock_aws_env(monkeypatch):
    """Fixture para configurar variáveis de ambiente AWS para testes"""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCOUNT_ID", "123456789012")
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket-url-generator")
    monkeypatch.setenv("S3_URL_DOWNLOAD_EXPIRATION", "3600")
    monkeypatch.setenv("S3_URL_UPLOAD_EXPIRATION", "900")
    monkeypatch.setenv("S3_BUCKET_DIR_UPLOADS", "uploads/")
    monkeypatch.setenv("S3_BUCKET_DIR_FINISHED", "finished/")

import logging
import boto3
from botocore.config import Config

from core.dtos.url_dto import UrlRequestDto, UrlResponseDto
from core.interfaces.url.url_datasource_interface import UrlDataSourceInterface

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class S3Repository(UrlDataSourceInterface):

    def __init__(self, config: dict):
        self.config = config
        self.s3_client = boto3.client('s3',config=Config(signature_version=config['signature_version'],region_name=config['aws_region']))
        self.bucket_name = self.config.get('bucket_name', 'vdsc-prd-s3-videos')

    def generate_download_presigned_url(self, request: UrlRequestDto) -> UrlResponseDto:
        return self._generate_presigned_url(request)

    def generate_upload_presigned_url(self, request: UrlRequestDto) -> UrlResponseDto:
        return self._generate_presigned_url(request)

    def _generate_presigned_url(self, request: UrlRequestDto) -> UrlResponseDto:
        method = self.config['client_methods'][request.action]
        expiration = self.config['expiration'][request.action]
        key = f"{self.config['directories'][request.action]}{request.file_name}"
        try:

            response = self.s3_client.generate_presigned_url(
                ClientMethod=method,
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            params = {
                "expireIn": expiration,
                "s3Key": key
            }
            return UrlResponseDto(
                url_endpoint=response,
                file_name=request.file_name,
                action=request.action,
                method=method,
                fields=params
            )

        except Exception as e:
            logger.error(f"Erro ao gerar URL pré-assinada: {e}", exc_info=True)
            raise e


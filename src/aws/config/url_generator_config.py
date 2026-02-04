import os
from aws.datasource.storage.s3_repository import S3Repository
from core.adapters.url.url_controller import UrlController

class UrlConfig():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UrlConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.s3 = {
            'bucket_name': os.getenv('S3_BUCKET_NAME', 'vdsc-prd-s3-videos'),
            'expiration': {
                'download': int(os.getenv('S3_URL_DOWNLOAD_EXPIRATION', '180')),
                'upload': int(os.getenv('S3_URL_UPLOAD_EXPIRATION', '900')),
            },
            'directories':{
                'upload': os.getenv('S3_BUCKET_DIR_UPLOADS', 'uploads/'),
                'download': os.getenv('S3_BUCKET_DIR_FINISHED', 'finished/')
            },
            'client_methods': {
                'download': 'get_object',
                'upload': 'put_object'
            }
        }

# Criar instâncias globais após a definição da classe
config = UrlConfig()
database = S3Repository(config.s3)
controller = UrlController(database)

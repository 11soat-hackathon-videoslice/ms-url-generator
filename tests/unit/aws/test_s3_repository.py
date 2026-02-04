import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

import pytest
from unittest.mock import Mock, patch
from moto import mock_aws
import boto3


@pytest.fixture
def s3_config():
    """Fixture com configuração válida do S3"""
    return {
        'bucket_name': 'test-bucket',
        'expiration': {
            'download': 3600,
            'upload': 900
        },
        'directories': {
            'upload': 'uploads/',
            'download': 'finished/'
        },
        'client_methods': {
            'download': 'get_object',
            'upload': 'put_object'
        }
    }


@pytest.fixture
def mock_url_request_dto():
    """Fixture para criar UrlRequestDto mock"""
    def _create_dto(file_name='test.mp4', action='download'):
        dto = Mock()
        dto.file_name = file_name
        dto.action = action
        return dto
    return _create_dto


@pytest.mark.unit
class TestS3Repository:
    """Testes para S3Repository"""

    @mock_aws
    def test_successfully_generates_download_presigned_url(self, s3_config, mock_url_request_dto):
        """Testa geração bem-sucedida de URL pré-assinada para download"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        from aws.datasource.storage.s3_repository import S3Repository
        repository = S3Repository(s3_config)
        request = mock_url_request_dto('video123.mp4', 'download')

        result = repository.generate_download_presigned_url(request)

        assert result.url_endpoint is not None
        assert result.file_name == 'video123.mp4'
        assert result.action == 'download'
        assert result.method == 'get_object'
        assert result.fields['expireIn'] == 3600

    @mock_aws
    def test_successfully_generates_upload_presigned_url(self, s3_config, mock_url_request_dto):
        """Testa geração bem-sucedida de URL pré-assinada para upload"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        from aws.datasource.storage.s3_repository import S3Repository
        repository = S3Repository(s3_config)
        request = mock_url_request_dto('video456.mp4', 'upload')

        result = repository.generate_upload_presigned_url(request)

        assert result.url_endpoint is not None
        assert result.file_name == 'video456.mp4'
        assert result.action == 'upload'
        assert result.method == 'put_object'
        assert result.fields['expireIn'] == 900

    @mock_aws
    def test_generates_correct_key_with_download_directory(self, s3_config, mock_url_request_dto):
        """Testa geração de key correto com diretório de download"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        from aws.datasource.storage.s3_repository import S3Repository
        repository = S3Repository(s3_config)
        request = mock_url_request_dto('test.mp4', 'download')

        with patch.object(repository.s3_client, 'generate_presigned_url', wraps=repository.s3_client.generate_presigned_url) as mock_method:
            repository.generate_download_presigned_url(request)

            mock_method.assert_called_once()
            call_args = mock_method.call_args
            assert call_args[1]['Params']['Key'] == 'finished/test.mp4'

    @mock_aws
    def test_generates_correct_key_with_upload_directory(self, s3_config, mock_url_request_dto):
        """Testa geração de key correto com diretório de upload"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        from aws.datasource.storage.s3_repository import S3Repository
        repository = S3Repository(s3_config)
        request = mock_url_request_dto('test.mp4', 'upload')

        with patch.object(repository.s3_client, 'generate_presigned_url', wraps=repository.s3_client.generate_presigned_url) as mock_method:
            repository.generate_upload_presigned_url(request)

            mock_method.assert_called_once()
            call_args = mock_method.call_args
            assert call_args[1]['Params']['Key'] == 'uploads/test.mp4'

    @mock_aws
    def test_uses_correct_bucket_name_from_config(self, s3_config, mock_url_request_dto):
        """Testa uso correto do nome do bucket da configuração"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        from aws.datasource.storage.s3_repository import S3Repository
        repository = S3Repository(s3_config)
        request = mock_url_request_dto('test.mp4', 'download')

        with patch.object(repository.s3_client, 'generate_presigned_url', wraps=repository.s3_client.generate_presigned_url) as mock_method:
            repository.generate_download_presigned_url(request)

            call_args = mock_method.call_args
            assert call_args[1]['Params']['Bucket'] == 'test-bucket'

    @mock_aws
    def test_uses_default_bucket_when_config_is_empty(self):
        """Testa uso do bucket padrão quando configuração está vazia"""
        from aws.datasource.storage.s3_repository import S3Repository
        repository = S3Repository({})

        assert repository.bucket_name == 'vdsc-prd-s3-videos'

    @mock_aws
    def test_uses_default_bucket_when_config_is_none(self):
        """Testa uso do bucket padrão quando configuração é None"""
        from aws.datasource.storage.s3_repository import S3Repository
        repository = S3Repository(None)

        assert repository.bucket_name == 'vdsc-prd-s3-videos'

    @mock_aws
    def test_raises_error_when_s3_client_fails(self, s3_config, mock_url_request_dto):
        """Testa erro quando cliente S3 falha"""
        from aws.datasource.storage.s3_repository import S3Repository
        repository = S3Repository(s3_config)
        request = mock_url_request_dto('test.mp4', 'download')

        with patch.object(repository.s3_client, 'generate_presigned_url', side_effect=Exception('S3 Error')):
            with pytest.raises(Exception, match='S3 Error'):
                repository.generate_download_presigned_url(request)

    @mock_aws
    def test_handles_filename_with_special_characters(self, s3_config, mock_url_request_dto):
        """Testa manipulação de nome de arquivo com caracteres especiais"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        from aws.datasource.storage.s3_repository import S3Repository
        repository = S3Repository(s3_config)
        request = mock_url_request_dto('file with spaces & special.mp4', 'download')

        result = repository.generate_download_presigned_url(request)

        assert result.file_name == 'file with spaces & special.mp4'
        assert result.url_endpoint is not None

    @mock_aws
    def test_handles_filename_with_subdirectories(self, s3_config, mock_url_request_dto):
        """Testa manipulação de nome de arquivo com subdiretórios"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        from aws.datasource.storage.s3_repository import S3Repository
        repository = S3Repository(s3_config)
        request = mock_url_request_dto('user123/videos/file.mp4', 'upload')

        with patch.object(repository.s3_client, 'generate_presigned_url', wraps=repository.s3_client.generate_presigned_url) as mock_method:
            result = repository.generate_upload_presigned_url(request)

            call_args = mock_method.call_args
            assert call_args[1]['Params']['Key'] == 'uploads/user123/videos/file.mp4'
            assert result.file_name == 'user123/videos/file.mp4'

    @mock_aws
    def test_uses_correct_expiration_time_for_download(self, s3_config, mock_url_request_dto):
        """Testa uso correto do tempo de expiração para download"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        from aws.datasource.storage.s3_repository import S3Repository
        repository = S3Repository(s3_config)
        request = mock_url_request_dto('test.mp4', 'download')

        with patch.object(repository.s3_client, 'generate_presigned_url', wraps=repository.s3_client.generate_presigned_url) as mock_method:
            result = repository.generate_download_presigned_url(request)

            call_args = mock_method.call_args
            assert call_args[1]['ExpiresIn'] == 3600
            assert result.fields['expireIn'] == 3600

    @mock_aws
    def test_uses_correct_expiration_time_for_upload(self, s3_config, mock_url_request_dto):
        """Testa uso correto do tempo de expiração para upload"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        from aws.datasource.storage.s3_repository import S3Repository
        repository = S3Repository(s3_config)
        request = mock_url_request_dto('test.mp4', 'upload')

        with patch.object(repository.s3_client, 'generate_presigned_url', wraps=repository.s3_client.generate_presigned_url) as mock_method:
            result = repository.generate_upload_presigned_url(request)

            call_args = mock_method.call_args
            assert call_args[1]['ExpiresIn'] == 900
            assert result.fields['expireIn'] == 900

    @mock_aws
    def test_uses_correct_client_method_for_download(self, s3_config, mock_url_request_dto):
        """Testa uso correto do método do cliente para download"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        from aws.datasource.storage.s3_repository import S3Repository
        repository = S3Repository(s3_config)
        request = mock_url_request_dto('test.mp4', 'download')

        with patch.object(repository.s3_client, 'generate_presigned_url', wraps=repository.s3_client.generate_presigned_url) as mock_method:
            result = repository.generate_download_presigned_url(request)

            call_args = mock_method.call_args
            assert call_args[1]['ClientMethod'] == 'get_object'
            assert result.method == 'get_object'

    @mock_aws
    def test_uses_correct_client_method_for_upload(self, s3_config, mock_url_request_dto):
        """Testa uso correto do método do cliente para upload"""
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket='test-bucket')

        from aws.datasource.storage.s3_repository import S3Repository
        repository = S3Repository(s3_config)
        request = mock_url_request_dto('test.mp4', 'upload')

        with patch.object(repository.s3_client, 'generate_presigned_url', wraps=repository.s3_client.generate_presigned_url) as mock_method:
            result = repository.generate_upload_presigned_url(request)

            call_args = mock_method.call_args
            assert call_args[1]['ClientMethod'] == 'put_object'
            assert result.method == 'put_object'

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

import pytest
import json
from unittest.mock import patch, MagicMock
from moto import mock_aws


@pytest.fixture
def lambda_context():
    """Gera um mock do contexto da Lambda"""
    context = MagicMock()
    context.function_name = "test-function"
    context.function_version = "1"
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
    context.memory_limit_in_mb = 128
    context.aws_request_id = "test-request-id"
    return context


@pytest.fixture
def valid_download_event():
    """Fixture com evento válido para download"""
    return {
        'path': '/download/video123.mp4',
        'httpMethod': 'GET',
        'pathParameters': {
            'fileName': 'video123.mp4'
        }
    }


@pytest.fixture
def valid_upload_event():
    """Fixture com evento válido para upload"""
    return {
        'path': '/upload/video456.mp4',
        'httpMethod': 'POST',
        'pathParameters': {
            'fileName': 'video456.mp4'
        }
    }


@pytest.mark.unit
class TestLambdaHandler:
    """Testes para o lambda_handler principal"""

    def test_successfully_generates_download_presigned_url(self, valid_download_event, lambda_context):
        """Testa geração bem-sucedida de URL pré-assinada para download"""
        with patch('app.controller.generate_presigned_url') as mock_controller:
            mock_controller.return_value = {
                'url_endpoint': 'https://s3.amazonaws.com/test-bucket/finished/video123.mp4',
                'file_name': 'video123.mp4',
                'action': 'download',
                'method': 'get_object',
                'fields': {'expireIn': 3600}
            }

            from app import lambda_handler
            result = lambda_handler(valid_download_event, lambda_context)

            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['file_name'] == 'video123.mp4'
            assert body['action'] == 'download'
            assert 'url_endpoint' in body

    def test_successfully_generates_upload_presigned_url(self, valid_upload_event, lambda_context):
        """Testa geração bem-sucedida de URL pré-assinada para upload"""
        with patch('app.controller.generate_presigned_url') as mock_controller:
            mock_controller.return_value = {
                'url_endpoint': 'https://s3.amazonaws.com/test-bucket/uploads/video456.mp4',
                'file_name': 'video456.mp4',
                'action': 'upload',
                'method': 'put_object',
                'fields': {'expireIn': 900}
            }

            from app import lambda_handler
            result = lambda_handler(valid_upload_event, lambda_context)

            assert result['statusCode'] == 200
            body = json.loads(result['body'])
            assert body['file_name'] == 'video456.mp4'
            assert body['action'] == 'upload'
            assert 'url_endpoint' in body

    def test_returns_error_when_filename_missing_in_path_parameters(self, lambda_context):
        """Testa erro quando fileName está ausente nos pathParameters"""
        event = {
            'path': '/download/test.mp4',
            'httpMethod': 'GET',
            'pathParameters': {}
        }

        from app import _extract_file_name

        with pytest.raises(ValueError, match="fileName não encontrado"):
            _extract_file_name(event)

    def test_returns_error_when_path_parameters_missing(self, lambda_context):
        """Testa erro quando pathParameters está ausente no evento"""
        event = {
            'path': '/download/test.mp4',
            'httpMethod': 'GET'
        }

        from app import _extract_file_name

        with pytest.raises(ValueError, match="fileName não encontrado"):
            _extract_file_name(event)

    def test_returns_error_when_action_path_is_invalid(self, lambda_context):
        """Testa erro quando o caminho não contém ação válida"""
        event = {
            'path': '/invalid/test.mp4',
            'httpMethod': 'GET',
            'pathParameters': {
                'fileName': 'test.mp4'
            }
        }

        from app import _extract_action_type

        with pytest.raises(ValueError, match="Ação inválida"):
            _extract_action_type(event)

    def test_returns_error_when_controller_raises_exception(self, valid_download_event, lambda_context):
        """Testa erro quando controller lança exceção"""
        with patch('app.controller.generate_presigned_url', side_effect=Exception('Erro no S3')):
            from app import lambda_handler
            result = lambda_handler(valid_download_event, lambda_context)

            assert result['statusCode'] == 500
            body = json.loads(result['body'])
            assert 'error' in body

    def test_lambda_handler_returns_error_when_extract_file_name_fails(self, lambda_context):
        """Testa que lambda_handler retorna erro 500 quando extração de fileName falha"""
        event = {
            'path': '/download/test.mp4',
            'httpMethod': 'GET',
            'pathParameters': {}
        }

        from app import lambda_handler
        result = lambda_handler(event, lambda_context)

        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert 'error' in body

    def test_lambda_handler_returns_error_when_extract_action_fails(self, lambda_context):
        """Testa que lambda_handler retorna erro 500 quando extração de action falha"""
        event = {
            'path': '/invalid/test.mp4',
            'httpMethod': 'GET',
            'pathParameters': {
                'fileName': 'test.mp4'
            }
        }

        from app import lambda_handler
        result = lambda_handler(event, lambda_context)

        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert 'error' in body

    def test_handles_filename_with_special_characters(self, lambda_context):
        """Testa manipulação de nome de arquivo com caracteres especiais"""
        event = {
            'path': '/download/video%20with%20spaces.mp4',
            'httpMethod': 'GET',
            'pathParameters': {
                'fileName': 'video with spaces.mp4'
            }
        }

        with patch('app.controller.generate_presigned_url') as mock_controller:
            mock_controller.return_value = {
                'url_endpoint': 'https://s3.amazonaws.com/test-bucket/finished/video%20with%20spaces.mp4',
                'file_name': 'video with spaces.mp4',
                'action': 'download',
                'method': 'get_object',
                'fields': {'expireIn': 3600}
            }

            from app import lambda_handler
            result = lambda_handler(event, lambda_context)

            assert result['statusCode'] == 200

    def test_handles_filename_with_subdirectories(self, lambda_context):
        """Testa manipulação de nome de arquivo com subdiretórios"""
        event = {
            'path': '/upload/user123/videos/test.mp4',
            'httpMethod': 'POST',
            'pathParameters': {
                'fileName': 'user123/videos/test.mp4'
            }
        }

        with patch('app.controller.generate_presigned_url') as mock_controller:
            mock_controller.return_value = {
                'url_endpoint': 'https://s3.amazonaws.com/test-bucket/uploads/user123/videos/test.mp4',
                'file_name': 'user123/videos/test.mp4',
                'action': 'upload',
                'method': 'put_object',
                'fields': {'expireIn': 900}
            }

            from app import lambda_handler
            result = lambda_handler(event, lambda_context)

            assert result['statusCode'] == 200


@pytest.mark.unit
class TestExtractFileName:
    """Testes para a função _extract_file_name"""

    def test_successfully_extracts_filename_from_valid_event(self):
        """Testa extração bem-sucedida de fileName de evento válido"""
        from app import _extract_file_name
        event = {
            'pathParameters': {
                'fileName': 'test.mp4'
            }
        }

        result = _extract_file_name(event)
        assert result == 'test.mp4'

    def test_raises_error_when_filename_is_empty_string(self):
        """Testa erro quando fileName é string vazia"""
        from app import _extract_file_name
        event = {
            'pathParameters': {
                'fileName': ''
            }
        }

        with pytest.raises(ValueError, match="fileName não encontrado"):
            _extract_file_name(event)

    def test_raises_error_when_filename_key_missing(self):
        """Testa erro quando chave fileName está ausente"""
        from app import _extract_file_name
        event = {
            'pathParameters': {}
        }

        with pytest.raises(ValueError, match="fileName não encontrado"):
            _extract_file_name(event)

    def test_raises_error_when_path_parameters_missing(self):
        """Testa erro quando pathParameters está ausente"""
        from app import _extract_file_name
        event = {}

        with pytest.raises(ValueError, match="fileName não encontrado"):
            _extract_file_name(event)

    def test_handles_filename_with_various_extensions(self):
        """Testa extração de nomes de arquivo com várias extensões"""
        from app import _extract_file_name

        filenames = ['video.mp4', 'audio.mp3', 'document.pdf', 'image.png', 'archive.zip']

        for filename in filenames:
            event = {
                'pathParameters': {
                    'fileName': filename
                }
            }
            result = _extract_file_name(event)
            assert result == filename


@pytest.mark.unit
class TestExtractActionType:
    """Testes para a função _extract_action_type"""

    def test_successfully_extracts_download_action(self):
        """Testa extração bem-sucedida de ação download"""
        from app import _extract_action_type
        event = {
            'path': '/download/video.mp4'
        }

        result = _extract_action_type(event)
        assert result == 'download'

    def test_successfully_extracts_upload_action(self):
        """Testa extração bem-sucedida de ação upload"""
        from app import _extract_action_type
        event = {
            'path': '/upload/video.mp4'
        }

        result = _extract_action_type(event)
        assert result == 'upload'

    def test_raises_error_when_action_is_invalid(self):
        """Testa erro quando ação é inválida"""
        from app import _extract_action_type
        event = {
            'path': '/delete/video.mp4'
        }

        with pytest.raises(ValueError, match="Ação inválida"):
            _extract_action_type(event)

    def test_raises_error_when_path_is_empty(self):
        """Testa erro quando path está vazio"""
        from app import _extract_action_type
        event = {
            'path': ''
        }

        with pytest.raises(ValueError, match="Ação inválida"):
            _extract_action_type(event)

    def test_raises_error_when_path_key_missing(self):
        """Testa erro quando chave path está ausente"""
        from app import _extract_action_type
        event = {}

        with pytest.raises(ValueError, match="Ação inválida"):
            _extract_action_type(event)

    def test_handles_path_with_trailing_slash(self):
        """Testa manipulação de path com barra final"""
        from app import _extract_action_type

        event = {'path': '/download/'}
        result = _extract_action_type(event)
        assert result == 'download'

        event = {'path': '/upload/'}
        result = _extract_action_type(event)
        assert result == 'upload'

    def test_handles_path_with_subdirectories(self):
        """Testa manipulação de path com subdiretórios"""
        from app import _extract_action_type

        event = {'path': '/download/user123/videos/file.mp4'}
        result = _extract_action_type(event)
        assert result == 'download'

        event = {'path': '/upload/user456/docs/file.pdf'}
        result = _extract_action_type(event)
        assert result == 'upload'

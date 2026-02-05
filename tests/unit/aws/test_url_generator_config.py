import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

import pytest


@pytest.fixture
def mock_env_variables(monkeypatch):
    """Fixture para configurar variáveis de ambiente para testes"""
    monkeypatch.setenv('S3_BUCKET_NAME', 'test-bucket-config')
    monkeypatch.setenv('S3_URL_DOWNLOAD_EXPIRATION', '7200')
    monkeypatch.setenv('S3_URL_UPLOAD_EXPIRATION', '1800')
    monkeypatch.setenv('S3_BUCKET_DIR_UPLOADS', 'test-uploads/')
    monkeypatch.setenv('S3_BUCKET_DIR_FINISHED', 'test-finished/')
    monkeypatch.setenv('AWS_REGION', 'us-east-1')
    monkeypatch.setenv('S3_SIGNATURE_VERSION', 's3v4')


@pytest.mark.unit
class TestUrlConfig:
    """Testes para UrlConfig"""

    def test_is_singleton_instance(self):
        """Testa que UrlConfig é uma instância singleton"""
        from aws.config.url_generator_config import UrlConfig

        config1 = UrlConfig()
        config2 = UrlConfig()

        assert config1 is config2

    def test_loads_bucket_name_from_environment(self, mock_env_variables):
        """Testa carregamento do nome do bucket das variáveis de ambiente"""
        import importlib
        import aws.config.url_generator_config as config_module
        importlib.reload(config_module)

        from aws.config.url_generator_config import UrlConfig
        config = UrlConfig()

        assert config.s3['bucket_name'] == 'test-bucket-config'

    def test_uses_default_bucket_name_when_env_not_set(self, monkeypatch):
        """Testa uso do nome do bucket padrão quando variável de ambiente não está definida"""
        monkeypatch.delenv('S3_BUCKET_NAME', raising=False)

        import importlib
        import aws.config.url_generator_config as config_module
        importlib.reload(config_module)

        from aws.config.url_generator_config import UrlConfig
        config = UrlConfig()

        assert config.s3['bucket_name'] == 'vdsc-prd-s3-videos'

    def test_loads_download_expiration_from_environment(self, mock_env_variables):
        """Testa carregamento do tempo de expiração de download das variáveis de ambiente"""
        import importlib
        import aws.config.url_generator_config as config_module
        importlib.reload(config_module)

        from aws.config.url_generator_config import UrlConfig
        config = UrlConfig()

        assert config.s3['expiration']['download'] == 7200

    def test_loads_upload_expiration_from_environment(self, mock_env_variables):
        """Testa carregamento do tempo de expiração de upload das variáveis de ambiente"""
        import importlib
        import aws.config.url_generator_config as config_module
        importlib.reload(config_module)

        from aws.config.url_generator_config import UrlConfig
        config = UrlConfig()

        assert config.s3['expiration']['upload'] == 1800

    def test_uses_default_download_expiration_when_env_not_set(self, monkeypatch):
        """Testa uso do tempo de expiração padrão de download quando variável não está definida"""
        monkeypatch.delenv('S3_URL_DOWNLOAD_EXPIRATION', raising=False)

        import importlib
        import aws.config.url_generator_config as config_module
        importlib.reload(config_module)

        from aws.config.url_generator_config import UrlConfig
        config = UrlConfig()

        assert config.s3['expiration']['download'] == 180

    def test_uses_default_upload_expiration_when_env_not_set(self, monkeypatch):
        """Testa uso do tempo de expiração padrão de upload quando variável não está definida"""
        monkeypatch.delenv('S3_URL_UPLOAD_EXPIRATION', raising=False)

        import importlib
        import aws.config.url_generator_config as config_module
        importlib.reload(config_module)

        from aws.config.url_generator_config import UrlConfig
        config = UrlConfig()

        assert config.s3['expiration']['upload'] == 900

    def test_loads_upload_directory_from_environment(self, mock_env_variables):
        """Testa carregamento do diretório de upload das variáveis de ambiente"""
        import importlib
        import aws.config.url_generator_config as config_module
        importlib.reload(config_module)

        from aws.config.url_generator_config import UrlConfig
        config = UrlConfig()

        assert config.s3['directories']['upload'] == 'test-uploads/'

    def test_loads_download_directory_from_environment(self, mock_env_variables):
        """Testa carregamento do diretório de download das variáveis de ambiente"""
        import importlib
        import aws.config.url_generator_config as config_module
        importlib.reload(config_module)

        from aws.config.url_generator_config import UrlConfig
        config = UrlConfig()

        assert config.s3['directories']['download'] == 'test-finished/'

    def test_uses_default_upload_directory_when_env_not_set(self, monkeypatch):
        """Testa uso do diretório padrão de upload quando variável não está definida"""
        monkeypatch.delenv('S3_BUCKET_DIR_UPLOADS', raising=False)

        import importlib
        import aws.config.url_generator_config as config_module
        importlib.reload(config_module)

        from aws.config.url_generator_config import UrlConfig
        config = UrlConfig()

        assert config.s3['directories']['upload'] == 'uploads/'

    def test_uses_default_download_directory_when_env_not_set(self, monkeypatch):
        """Testa uso do diretório padrão de download quando variável não está definida"""
        monkeypatch.delenv('S3_BUCKET_DIR_FINISHED', raising=False)

        import importlib
        import aws.config.url_generator_config as config_module
        importlib.reload(config_module)

        from aws.config.url_generator_config import UrlConfig
        config = UrlConfig()

        assert config.s3['directories']['download'] == 'finished/'

    def test_contains_correct_client_methods_mapping(self):
        """Testa que o mapeamento de métodos do cliente está correto"""
        from aws.config.url_generator_config import UrlConfig
        config = UrlConfig()

        assert config.s3['client_methods']['download'] == 'get_object'
        assert config.s3['client_methods']['upload'] == 'put_object'

    def test_expiration_values_are_integers(self):
        """Testa que os valores de expiração são inteiros"""
        from aws.config.url_generator_config import UrlConfig
        config = UrlConfig()

        assert isinstance(config.s3['expiration']['download'], int)
        assert isinstance(config.s3['expiration']['upload'], int)

    def test_creates_global_config_instance(self):
        """Testa que a instância global de config é criada"""
        from aws.config.url_generator_config import config

        assert config is not None
        assert hasattr(config, 's3')

    def test_creates_global_database_instance(self):
        """Testa que a instância global de database é criada"""
        from aws.config.url_generator_config import database

        assert database is not None

    def test_creates_global_controller_instance(self):
        """Testa que a instância global de controller é criada"""
        from aws.config.url_generator_config import controller

        assert controller is not None

    def test_reinitializing_does_not_create_new_instance(self):
        """Testa que reinicializar não cria nova instância"""
        from aws.config.url_generator_config import UrlConfig

        config1 = UrlConfig()
        initial_id = id(config1)

        config2 = UrlConfig()

        assert id(config2) == initial_id
        assert config1.s3 is config2.s3

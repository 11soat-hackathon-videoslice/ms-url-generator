import json
import logging
from typing import Dict, Any

from aws.config.url_generator_config import UrlConfig, controller
from core.dtos.url_dto import UrlRequestDto

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = UrlConfig()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handler principal da Lambda para geração de URLs pré-assinadas."""

    logger.info("=== Iniciando Lambda Handler ===")
    logger.info(f"Recebido novo evento: {json.dumps(event)}")

    try:
        file_name = _extract_file_name(event)
        action_type = _extract_action_type(event)
        logger.info(f"Arquivo do caminho: {file_name} | Ação: {action_type}")
        request = UrlRequestDto(file_name=file_name, action=action_type)

        response = controller.generate_presigned_url(request)
        logger.info(f"URL pré-assinada gerada com sucesso para o arquivo {request.file_name}")
        return {'statusCode': 200, 'body': json.dumps(response)}

    except Exception as e:
        logger.error(f"Erro ao gerar url pré-assinada: {e}", exc_info=True)
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}


def _extract_file_name(event) -> str:
    """Extrai o nome do arquivo para geração de url pré-assinada."""
    file_name = event.get('pathParameters', {}).get('fileName',{})
    if not file_name:
        raise ValueError("fileName não encontrado nos parâmetros do caminho.")
    return file_name

def _extract_action_type(event) -> str:
    """Extrai o tipo de ação (upload/download) para geração de url pré-assinada."""
    action = event.get('path',{})
    if '/upload/' in action:
        return 'upload'
    elif '/download/' in action:
        return 'download'
    else:
        raise ValueError("Ação inválida. Use '/upload/' ou '/download/' no caminho.")




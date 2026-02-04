import sys
import os
import json

print("=== Iniciando script generate_url_manual.py ===")

# Adicionar path do src do ms-video-url-generator
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

print(f"Path do src adicionado: {src_path}")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../video-slice-core/src')))


def chamada_url(arquivo_json: str):
    from app import lambda_handler

    # Caminho do arquivo JSON com o evento do DynamoDB
    json_file_path = os.path.join(os.path.dirname(__file__), '..', 'events', arquivo_json)

    # Ler o conteúdo do arquivo JSON
    print(f"Carregando evento do arquivo: {json_file_path}")
    with open(json_file_path, 'r', encoding='utf-8') as file:
        event = json.load(file)

    print("Evento carregado com sucesso!")
    # Simular contexto Lambda (pode ser None ou um objeto mock)
    context = None

    # Chamar o handler com o evento
    print(f"\n{'='*60}")
    print("Iniciando processamento do evento...")
    print(f"{'='*60}\n")

    try:
        result = lambda_handler(event, context)
        print(f"\n{'='*60}")
        print("Processamento finalizado com sucesso!")
        print("="*60)
        if result:
            print(f"Resultado: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"Erro ao processar: {e}")
        print("="*60)
        raise


if __name__ == "__main__":
    files = ['example_api_gateway_download.json','example_api_gateway_upload.json']

    for file in files:
        chamada_url(file)




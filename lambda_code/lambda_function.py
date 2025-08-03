import os
import json
import logging

# --- A SOLUÇÃO ESTÁ AQUI ---
# Força a biblioteca do Kaggle a usar o diretório /tmp, que é gravável
os.environ['KAGGLE_CONFIG_DIR'] = '/tmp/.kaggle'

# Configuração do logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def setup_kaggle_from_env_vars():
    """Configura as credenciais do Kaggle a partir de variáveis de ambiente."""
    try:
        # Ler as credenciais das variáveis de ambiente
        kaggle_username = os.environ.get('KAGGLE_USERNAME')
        kaggle_key = os.environ.get('KAGGLE_KEY')

        if not kaggle_username or not kaggle_key:
            logger.error("As variáveis de ambiente KAGGLE_USERNAME e KAGGLE_KEY não foram definidas.")
            raise ValueError("Credenciais do Kaggle não encontradas nas variáveis de ambiente.")

        # Criar o diretório e o arquivo kaggle.json no /tmp da Lambda
        # O diretório já foi definido pela variável de ambiente KAGGLE_CONFIG_DIR
        kaggle_dir = os.environ['KAGGLE_CONFIG_DIR']
        os.makedirs(kaggle_dir, exist_ok=True) # Garante que o diretório exista
        kaggle_json_path = os.path.join(kaggle_dir, 'kaggle.json')

        # Monta o conteúdo do JSON
        kaggle_content = f'{{"username":"{kaggle_username}","key":"{kaggle_key}"}}'

        # Escreve o arquivo
        with open(kaggle_json_path, 'w') as f:
            f.write(kaggle_content)

        # Define permissões restritas para o arquivo
        os.chmod(kaggle_json_path, 0o600)
        logger.info("Credenciais do Kaggle configuradas com sucesso.")
        return True

    except Exception as e:
        logger.error(f"Erro ao configurar as credenciais do Kaggle: {e}")
        raise e

def lambda_handler(event, context):
    S3_BUCKET_NAME = 'olist-datalake-gustavo-novo' # Verifique se este é o seu bucket
    KAGGLE_DATASET = 'olistbr/brazilian-ecommerce'
    DOWNLOAD_PATH = '/tmp/data'

    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    # 1. Configurar credenciais do Kaggle
    setup_kaggle_from_env_vars()

    # Importa a API do Kaggle APÓS a configuração
    from kaggle.api.kaggle_api_extended import KaggleApi
    import boto3 

    # 2. Baixar os arquivos do dataset
    try:
        api = KaggleApi()
        api.authenticate()
        logger.info(f"Baixando dataset '{KAGGLE_DATASET}' para '{DOWNLOAD_PATH}'...")
        api.dataset_download_files(KAGGLE_DATASET, path=DOWNLOAD_PATH, unzip=True)
        logger.info("Download e descompactação concluídos.")
    except Exception as e:
        logger.error(f"Erro durante o download do Kaggle: {e}")
        raise e

    # 3. Fazer upload dos arquivos para o S3
    s3_client = boto3.client('s3')
    try:
        downloaded_files = os.listdir(DOWNLOAD_PATH)
        for filename in downloaded_files:
            local_file_path = os.path.join(DOWNLOAD_PATH, filename)
            s3_key = f"raw-data/{filename}"
            s3_client.upload_file(local_file_path, S3_BUCKET_NAME, s3_key)
        logger.info(f"Upload de {len(downloaded_files)} arquivos para o S3 concluído.")
    except Exception as e:
        logger.error(f"Erro durante o upload para o S3: {e}")
        raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Processo concluído com sucesso!')
    }
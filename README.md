# Arquitetura de Dados Analíticos para o Case Olist E-commerce na AWS

## 1. Resumo Executivo

Este projeto documenta a concepção e implementação de um pipeline de dados ponta a ponta (end-to-end) na nuvem AWS. A solução foi projetada para ingerir, armazenar, processar e analisar um conjunto de dados público de e-commerce da empresa Olist, demonstrando as melhores práticas de engenharia de dados. A arquitetura emprega um padrão moderno, combinando um Data Lake no Amazon S3, processos de ETL serverless com AWS Glue e um Data Warehouse no Amazon Redshift para análises de alta performance.

## 2. Diagrama da Arquitetura Final

![Diagrama da Arquitetura](Arquiteruta_Pipline_AWS.png)


## 3. Contexto de Negócio

A capacidade de uma empresa de e-commerce tomar decisões baseadas em dados é um diferencial competitivo crítico. O objetivo deste pipeline é estruturar os dados da Olist para responder a perguntas de negócio fundamentais sobre vendas, clientes e logística, criando uma fundação escalável para que analistas, cientistas de dados e gestores possam explorar os dados e extrair insights valiosos.

## 4. Implementação Detalhada do Pipeline

Esta seção descreve o processo prático e os passos técnicos executados para construir a arquitetura no ambiente AWS.

### Fase 1: Ingestão de Dados
O ponto de partida foi a extração automatizada dos dados da API do Kaggle.

* **Serviço Utilizado:** **AWS Lambda**.
* **Implementação:** Uma função Lambda em Python foi desenvolvida para orquestrar a ingestão. Como a biblioteca do Kaggle não é nativa da Lambda, uma **Lambda Layer** foi criada contendo as dependências necessárias. As credenciais da API foram armazenadas de forma segura como **Variáveis de Ambiente**. Ao ser executada, a função autentica na API, baixa o dataset, descompacta os arquivos e os carrega na Zona Bruta do Data Lake. O timeout da função foi ajustado para 5 minutos para garantir a conclusão do processo.

### Fase 2: Armazenamento - O Data Lake
O **Amazon S3** é o pilar da nossa arquitetura de armazenamento, funcionando como um Data Lake centralizado. A estrutura foi organizada em zonas para melhor governança:
* **`raw-data` (Zona Bruta / Bronze):** Repositório para os arquivos CSV originais e imutáveis, depositados pela AWS Lambda.
* **`processed-data` (Zona Processada / Prata):** Repositório para os dados após a limpeza e transformação, armazenados em formato colunar **Parquet** para otimizar a performance das consultas.

### Fase 3: Governança e Processamento (ETL)
O **AWS Glue** foi o serviço central para governança e transformação dos dados.
* **Governança (Crawler e Data Catalog):** Um **AWS Glue Crawler** foi configurado para varrer a Zona Bruta. Para superar um desafio onde o Crawler não identificava os cabeçalhos, um **Classificador Customizado** foi criado, forçando o Crawler a reconhecer a primeira linha como cabeçalho e a popular corretamente o **AWS Glue Data Catalog**. O Catálogo funciona como nosso dicionário de dados técnico central.
* **Processamento (Glue ETL Jobs):** Utilizando o **AWS Glue Studio**, jobs visuais de ETL foram construídos. Estes jobs leem os dados brutos (usando o Data Catalog como fonte), aplicam transformações com o nó **"Change Schema"** (corrigindo tipos de dados de `string` para `timestamp`) e adicionam validações de qualidade (como a remoção de duplicados com **"Drop Duplicates"**). O resultado é salvo na Zona Processada do S3 em formato Parquet, e uma nova tabela "limpa" (ex: `orders_processed`) é criada no Data Catalog.

### Fase 4: Armazenamento - O Data Warehouse
Para análises de BI de alta performance, os dados processados são movidos para um Data Warehouse.
* **Serviço Utilizado:** **Amazon Redshift**.
* **Implementação:** Um cluster Redshift provisionado (nó `ra3.large`) foi criado. A conexão foi estabelecida via **Query Editor v2**, onde a estrutura da tabela de destino (`public.orders`) foi definida com `CREATE TABLE`. A carga de dados foi executada de forma performática com o comando `COPY`, que move os dados em Parquet da Zona Processada do S3 diretamente para o Redshift, utilizando as permissões da `LabRole` do IAM previamente associada ao cluster.

### Fase 5: Consumo e Análise
A arquitetura suporta múltiplos perfis de consumo:
* **Amazon Athena:** Para consultas exploratórias e ad-hoc diretamente sobre os dados no S3.
* **Amazon SageMaker:** Para cientistas de dados acessarem os dados limpos (do S3 ou Redshift) e desenvolverem modelos de Machine Learning.
* **Amazon QuickSight:** (Implementação Conceitual) A camada final de BI, que se conectaria ao Amazon Redshift para criar dashboards e relatórios interativos para usuários de negócio.

## 5. Desafios Técnicos e Soluções

O principal desafio do projeto foi a persistente falha do AWS Glue Crawler em inferir corretamente o esquema dos arquivos CSV. A solução definitiva envolveu a criação de um **Classificador Customizado** no Glue, que explicitamente instruiu o Crawler a tratar a primeira linha como cabeçalho. Adicionalmente, foi validado que a abordagem de **correção manual do esquema dentro do Job de ETL** (usando "Change Schema") é uma alternativa robusta para lidar com fontes de dados inconsistentes, demonstrando uma prática de engenharia de dados resiliente.

## 6. Conclusão e Próximos Passos

O pipeline implementado é uma solução robusta e escalável que transforma dados brutos em um ativo pronto para análise. Como próximos passos, a arquitetura pode ser estendida para incluir automação via agendamento, implementação de regras de qualidade com AWS Glue Data Quality e o desenvolvimento de dashboards completos no QuickSight.


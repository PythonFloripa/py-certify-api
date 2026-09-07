# Certified Builder API

## Descrição

Esta API é responsável por gerenciar a criação, consulta e download de certificados. Ela é construída como uma função Lambda da AWS, utilizando uma arquitetura serverless.

## Tecnologias Utilizadas

- **Python 3.13**
- **AWS Lambda**
- **API Gateway**
- **Boto3**: AWS SDK para Python.
- **Pydantic**: Para validação de dados.
- **Docker**: Para containerização da aplicação.

## Desenvolvimento e Deploy

- **Local**: `docker compose up --build` expõe a Lambda em `http://localhost:9000`.
- **Smoke test**: `python test_local.py` ou `bash test_lambda_container.sh`.
- **Deploy**: o workflow `.github/workflows/workflow_build.yaml` gera um ZIP e atualiza a função `tech-floripa-certificates-api-dev` com `aws lambda update-function-code`.

## Endpoints

A seguir estão os endpoints disponíveis na API.

### Criar Certificado

Cria um novo certificado para um determinado produto.

- **Endpoint:** `POST /v1/certificate/create`
- **Entrada (body):**
  ```json
  {
    "product_id": "string"
  }
  ```
- **Saída (sucesso):**
  ```json
  {
    "certificate_quantity": "integer",
    "existing_orders": ["integer"],
    "new_orders": ["integer"],
    "processing_date": "string"
  }
  ```
- **Saída (erro):**
  ```json
  {
    "status": "integer",
    "message": "string",
    "details": "string"
  }
  ```

### Criar Certificados em Lote

Cria múltiplos certificados a partir de uma lista de dados recebida diretamente.

- **Endpoint:** `POST /v1/certificate/create-batch`
- **Entrada (body):**
  ```json
  {
    "certificates": [
      {
        "order_id": 1234,
        "first_name": "João",
        "last_name": "Silva",
        "email": "joao.silva@example.com",
        "product_id": 5678,
        "product_name": "Workshop de Python Avançado",
        "certificate_details": "In recognition of their participation in the Workshop de Python Avançado, held on January 15, 2025, at IFSC – Câmpus Florianópolis, Brazil, with a total duration of 8 hours.",
        "certificate_logo": "https://example.com/logo.png",
        "certificate_background": "https://example.com/background.png",
        "order_date": "2025-01-10 14:30:00",
        "time_checkin": "2025-01-15 09:00:00"
      },
      {
        "order_id": 1235,
        "first_name": "Maria",
        "last_name": "Santos",
        "email": "maria.santos@example.com",
        "product_id": 5678,
        "product_name": "Workshop de Python Avançado",
        "certificate_details": "In recognition of their participation in the Workshop de Python Avançado, held on January 15, 2025, at IFSC – Câmpus Florianópolis, Brazil, with a total duration of 8 hours.",
        "certificate_logo": "https://example.com/logo.png",
        "certificate_background": "https://example.com/background.png",
        "order_date": "2025-01-10 14:35:00",
        "time_checkin": "2025-01-15 09:05:00"
      }
    ]
  }
  ```
- **Campos obrigatórios:**
  - `order_id`: ID único do pedido (integer)
  - `first_name`: Primeiro nome do participante (string)
  - `last_name`: Sobrenome do participante (string)
  - `email`: Email do participante (string)
  - `product_id`: ID do produto (integer)
  - `product_name`: Nome do produto (string)
  - `certificate_details`: Detalhes do certificado (string)
  - `certificate_logo`: URL do logo do certificado (string)
  - `certificate_background`: URL do background do certificado (string)
  - `order_date`: Data do pedido no formato "YYYY-MM-DD HH:MM:SS" (string)
- **Campos opcionais:**
  - `time_checkin`: Data e hora do check-in no formato "YYYY-MM-DD HH:MM:SS" (string, opcional)
    - **Nota:** Certificados sem `time_checkin` serão marcados como inválidos e não serão processados.
- **Saída (sucesso):**
  ```json
  {
    "certificate_quantity": 2,
    "existing_orders": [],
    "new_orders": [1234, 1235],
    "processing_date": "2025-01-20 10:30:45.123456"
  }
  ```
- **Saída (erro):**
  ```json
  {
    "status": 500,
    "message": "Internal Server Error",
    "details": "string"
  }
  ```

### Consultar Certificado

Consulta certificados com base em diferentes critérios.

- **Endpoint:** `GET /api/v1/certificate/fetch`
- **Entrada (query parameters):**
  - `order_id` (opcional): ID do pedido.
  - `email` (opcional): Email do participante.
  - `product_id` (opcional): ID do produto.
- **Saída (sucesso):**
  ```json
  [
    {
      "id": "string (uuid)",
      "order_id": "integer",
      "product_id": "integer",
      "participant_name": "string",
      "participant_email": "string",
      "certificate_url": "string",
      "created_at": "string",
      "updated_at": "string",
      "success": "boolean",
      "email": "string",
      "product_name": "string",
      "generated_date": "string",
      "time_checkin": "string"
    }
  ]
  ```
- **Saída (erro):**
  ```json
  {
    "status": "integer",
    "message": "string",
    "details": "string"
  }
  ```

### Listar Certificados de um Usuário

Lista os certificados de um usuário a partir do e-mail informado no path.

- **Endpoint:** `GET /api/v1/users/{email}/certificates`
- **Entrada (path parameters):**
  - `email` (obrigatório): e-mail do participante. Suporta URL encoding, por exemplo `user%2Bqa%40example.com`.
- **Entrada (query parameters):**
  - `success` (opcional): `true` para retornar apenas certificados gerados com sucesso ou `false` para retornar apenas falhas.
- **Saída (sucesso):**
  ```json
  {
    "email": "user@example.com",
    "certificates": [
      {
        "id": "string (uuid)",
        "order_id": 123,
        "product_id": 456,
        "participant_name": "string",
        "participant_email": "string",
        "certificate_url": "string",
        "created_at": "2025-01-20T10:30:45",
        "updated_at": "2025-01-20T10:30:45",
        "success": true
      }
    ]
  }
  ```
- **Comportamento para vazio:**
  ```json
  {
    "email": "user@example.com",
    "certificates": []
  }
  ```

### Download do Certificado

Gera uma página para download de um certificado.

- **Endpoint:** `GET /api/v1/certificate/download`
- **Entrada (query parameters):**
  - `id` (obrigatório): UUID do certificado.
- **Saída (sucesso):**
  - Retorna uma página HTML com o link para download do certificado.
- **Saída (erro):**
  - Retorna uma página HTML indicando o erro (certificado não encontrado, UUID inválido, etc.).

## Exemplos Locais

- Listar todos os certificados de um e-mail:
  - `test_list_user_certificates("suzi.harima94@gmail.com")`
- Listar apenas certificados com sucesso:
  - `test_list_user_certificates("suzi.harima94@gmail.com", success="true")`
- Listar apenas certificados com falha:
  - `test_list_user_certificates("suzi.harima94@gmail.com", success="false")`
- Testar e-mail com URL encoding:
  - `test_list_user_certificates("user+qa@example.com")`

## DynamoDB Single-Table Design

Este projeto utiliza o padrão DynamoDB Single-Table Design, onde todas as entidades (Orders, Certificates, Products, Participants) são armazenadas em uma única tabela DynamoDB.

### Estrutura da Tabela

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `PK` | String | Chave de Partição principal |
| `SK` | String | Chave de Ordenação principal |
| `GSI1PK` | String | Chave de Partição do GSI1 |
| `GSI1SK` | String | Chave de Ordenação do GSI1 |
| `GSI2PK` | String | Chave de Partição do GSI2 |
| `GSI2SK` | String | Chave de Ordenação do GSI2 |
| `GSI3PK` | String | Chave de Partição do GSI3 |
| `GSI3SK` | String | Chave de Ordenação do GSI3 |
| `GSI4PK` | String | Chave de Partição do GSI4 |
| `GSI4SK` | String | Chave de Ordenação do GSI4 |
| `EntityType` | String | Tipo da entidade (ORDER, CERTIFICATE, PRODUCT, PARTICIPANT) |

### GSIs (Global Secondary Indexes)

| GSI | Key Schema | Access Pattern |
|-----|------------|----------------|
| GSI1 | `PK: UUID, SK: CERT#` | Certificate by UUID |
| GSI2 | `PK: email, SK: ENTITY#` | Orders, Certificates, Participants by email |
| GSI3 | `PK: product, SK: ENTITY#` | Products by name, Certificates/Orders by product |
| GSI4 | `PK: SUCCESS#Y/N, SK: CERT#` | Successful/Failed certificates |

### Entidades e Keys

#### Certificate
| Key | Value |
|-----|-------|
| PK | `CERTIFICATE#<uuid>` |
| SK | `CERTIFICATE#<uuid>` |
| GSI1PK | `<uuid>` |
| GSI1SK | `CERTIFICATE#<uuid>` |
| GSI2PK | `EMAIL#<normalized_email>` |
| GSI2SK | `CERTIFICATE#<order_id>` |
| GSI3PK | `PRODUCT#<product_id>` |
| GSI3SK | `CERTIFICATE#<order_id>` |
| GSI4PK | `SUCCESS#<true/false>` |
| GSI4SK | `CERTIFICATE#<uuid>` |

#### Order
| Key | Value |
|-----|-------|
| PK | `ORDER#<order_id>` |
| SK | `ORDER#<order_id>` |
| GSI2PK | `EMAIL#<normalized_email>` |
| GSI2SK | `ORDER#<order_id>` |
| GSI3PK | `PRODUCT#<product_id>` |
| GSI3SK | `ORDER#<order_id>` |

#### Product
| Key | Value |
|-----|-------|
| PK | `PRODUCT#<product_id>` |
| SK | `PRODUCT#<product_id>` |
| GSI3PK | `PRODUCT#<product_name>` |
| GSI3SK | `PRODUCT#<product_id>` |

#### Participant
| Key | Value |
|-----|-------|
| PK | `PARTICIPANT#<uuid>` |
| SK | `PARTICIPANT#<uuid>` |
| GSI2PK | `EMAIL#<normalized_email>` |
| GSI2SK | `PARTICIPANT#<uuid>` |

### Normalização de Email

Emails são normalizados para consistência:
- Convertido para minúsculas
- Remoção de pontos antes do `@` (Gmail)
- Remoção de `+` e tudo após

### Repositórios

Cada repositório implementa operações CRUD usando as chaves apropriadas:

- **OrderRepositoryImpl**: GSI2 (email), GSI3 (product)
- **CertificateRepositoryImpl**: GSI1 (UUID), GSI2 (email), GSI3 (product), GSI4 (success)
- **ProductRepositoryImpl**: GSI3 (name)
- **ParticipantRepositoryImpl**: GSI2 (email)

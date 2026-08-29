"""
Limpeza (scrub) de PII já armazenada em itens existentes do DynamoDB.

Remove os atributos de PII que não são mais usados para gerar, entregar ou
validar um certificado. Os nomes dos atributos diferem por tabela:

  - participants:  cpf, phone, city
  - orders:        participant_cpf, participant_phone, participant_city,
                   checkin_latitude, checkin_longitude
  - certificates:  participant_cpf, participant_phone, participant_city

Segurança:
  - Roda em DRY-RUN por padrão (apenas mostra o que faria, não escreve nada).
  - Para aplicar de verdade é preciso passar --apply E o nome explícito de cada
    tabela. NÃO existe default apontando para produção.
  - Deve ser executado DEPOIS de remover os índices cpf/city (ver
    py-certify-infra), pois um GSI exige que o atributo-chave exista nos itens.

Uso:
    # dry-run (padrão) — só participants
    python scripts/scrub_pii.py --participants-table <nome>

    # aplicar de verdade nas três tabelas
    python scripts/scrub_pii.py \
        --participants-table <nome> \
        --orders-table <nome> \
        --certificates-table <nome> \
        --apply
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Optional

logger = logging.getLogger("scrub_pii")

# Atributos de PII a remover, por entidade/tabela.
ATTRS_POR_ENTIDADE: dict[str, list[str]] = {
    "participants": ["cpf", "phone", "city"],
    "orders": [
        "participant_cpf",
        "participant_phone",
        "participant_city",
        "checkin_latitude",
        "checkin_longitude",
    ],
    "certificates": ["participant_cpf", "participant_phone", "participant_city"],
}


def montar_remocao(
    item: dict, atributos_alvo: list[str]
) -> Optional[tuple[str, dict[str, str]]]:
    """
    Monta a UpdateExpression de REMOVE apenas para os atributos-alvo que
    realmente existem no item. Usa ExpressionAttributeNames para evitar
    conflito com palavras reservadas do DynamoDB.

    Retorna (update_expression, expression_attribute_names) ou None se o item
    não tiver nenhum dos atributos-alvo.
    """
    presentes = [attr for attr in atributos_alvo if attr in item]
    if not presentes:
        return None

    nomes = {f"#a{i}": attr for i, attr in enumerate(presentes)}
    update_expression = "REMOVE " + ", ".join(nomes.keys())
    return update_expression, nomes


def _chaves_da_tabela(client, table_name: str) -> list[str]:
    """Retorna os nomes das colunas-chave (hash/range) da tabela."""
    descricao = client.describe_table(TableName=table_name)
    return [k["AttributeName"] for k in descricao["Table"]["KeySchema"]]


def _projecao(chaves: list[str], atributos_alvo: list[str]) -> tuple[str, dict[str, str]]:
    """
    Monta uma ProjectionExpression que busca apenas as chaves + os atributos-alvo
    (evita puxar o item inteiro, minimizando o manuseio de PII).
    """
    campos = list(dict.fromkeys([*chaves, *atributos_alvo]))
    nomes = {f"#p{i}": campo for i, campo in enumerate(campos)}
    return ", ".join(nomes.keys()), nomes


def limpar_tabela(
    client, table_name: str, entidade: str, aplicar: bool, limite: Optional[int]
) -> tuple[int, int]:
    """
    Varre a tabela e remove os atributos de PII dos itens que os possuem.

    Retorna (itens_varridos, itens_afetados).
    """
    atributos_alvo = ATTRS_POR_ENTIDADE[entidade]
    chaves = _chaves_da_tabela(client, table_name)
    proj_expr, proj_nomes = _projecao(chaves, atributos_alvo)

    varridos = 0
    afetados = 0
    paginator = client.get_paginator("scan")
    for pagina in paginator.paginate(
        TableName=table_name,
        ProjectionExpression=proj_expr,
        ExpressionAttributeNames=proj_nomes,
    ):
        for item_dynamo in pagina.get("Items", []):
            varridos += 1
            # item_dynamo vem no formato low-level ({"attr": {"S": "..."}}). Para
            # decidir a presença basta olhar as chaves do dict.
            remocao = montar_remocao(item_dynamo, atributos_alvo)
            if remocao is None:
                continue

            afetados += 1
            update_expression, nomes = remocao
            chave = {k: item_dynamo[k] for k in chaves}
            removidos = list(nomes.values())

            if aplicar:
                client.update_item(
                    TableName=table_name,
                    Key=chave,
                    UpdateExpression=update_expression,
                    ExpressionAttributeNames=nomes,
                )
                logger.info("[%s] removido %s de %s", table_name, removidos, chave)
            else:
                logger.info(
                    "[dry-run][%s] removeria %s de %s", table_name, removidos, chave
                )

            if limite is not None and varridos >= limite:
                return varridos, afetados

    return varridos, afetados


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--participants-table")
    parser.add_argument("--orders-table")
    parser.add_argument("--certificates-table")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-1"))
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica de verdade. Sem esta flag roda em dry-run.",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Para após N itens (para testes)."
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    alvos = {
        "participants": args.participants_table,
        "orders": args.orders_table,
        "certificates": args.certificates_table,
    }
    alvos = {entidade: nome for entidade, nome in alvos.items() if nome}

    if not alvos:
        parser.error(
            "informe ao menos uma tabela (--participants-table / --orders-table "
            "/ --certificates-table). Não há default apontando para produção."
        )

    if args.apply:
        logger.warning(
            "*** MODO --apply: alterações serão gravadas em %s ***", list(alvos.values())
        )
    else:
        logger.info("Modo DRY-RUN (nada será gravado). Use --apply para efetivar.")

    import boto3  # import tardio: mantém as funções puras testáveis sem boto3

    client = boto3.client("dynamodb", region_name=args.region)

    total_varridos = 0
    total_afetados = 0
    for entidade, table_name in alvos.items():
        varridos, afetados = limpar_tabela(
            client, table_name, entidade, args.apply, args.limit
        )
        logger.info(
            "%s: %d itens varridos, %d itens %s",
            table_name,
            varridos,
            afetados,
            "atualizados" if args.apply else "seriam atualizados",
        )
        total_varridos += varridos
        total_afetados += afetados

    logger.info(
        "TOTAL: %d varridos, %d %s",
        total_varridos,
        total_afetados,
        "atualizados" if args.apply else "seriam atualizados",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

import httpx
import logging
from typing import Dict, Any, List
from retry import retry
from src.infrastructure.config.config import config

logger = logging.getLogger(__name__)


class FetchOrderTechFloripa:
    """
    Classe responsável por buscar ordens da API Tech Floripa.
    Implementa retry automático e configurações robustas de timeout.
    """

    def __init__(self):
        self.url = config.URL_SERVICE_TECH
        # Configurações de timeout mais robustas para APIs lentas
        self.timeout_config = httpx.Timeout(
            connect=15.0,  # Timeout para estabelecer conexão (aumentado)
            read=60.0,  # Timeout para ler resposta (aumentado)
            write=15.0,  # Timeout para enviar dados (aumentado)
            pool=60.0,  # Timeout para pool de conexões (aumentado)
        )

        # Headers para simular navegador real e melhorar compatibilidade
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "close",  # Evita keep-alive que pode causar problemas
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

    @retry(
        exceptions=(httpx.RequestError, httpx.HTTPStatusError, httpx.TimeoutException),
        tries=3,
        delay=2,
        backoff=2,
        logger=logger,
    )
    def fetch_orders(self, product_id: str) -> List[Dict[str, Any]]:
        """
        Busca ordens para um product_id específico.

        Args:
            product_id: ID do produto para buscar ordens

        Returns:
            List[Dict[str, Any]]: Lista de ordens encontradas

        Raises:
            Exception: Se falhar após todas as tentativas de retry
        """
        url = f"{self.url}/orders?product_id={product_id}"
        logger.info(f"Buscando ordens da URL: {url}")
        logger.info(
            f"Configurações de timeout: connect={self.timeout_config.connect}s, read={self.timeout_config.read}s"
        )

        try:
            # Configurações mais robustas para o cliente HTTP
            with httpx.Client(
                timeout=self.timeout_config,
                headers=self.headers,
                follow_redirects=True,
                limits=httpx.Limits(
                    max_keepalive_connections=0, max_connections=5
                ),  # Desabilita keep-alive
            ) as client:
                logger.info("Iniciando requisição HTTP...")
                response = client.get(url)
                logger.info(
                    f"Resposta recebida em {response.elapsed.total_seconds():.2f}s"
                )

                # Verifica se a resposta foi bem-sucedida
                response.raise_for_status()

                logger.info(f"Requisição bem-sucedida! Status: {response.status_code}")

                # Processa e retorna os dados
                data = response.json()
                logger.info(
                    f"Recebidas {len(data) if isinstance(data, list) else 1} ordem(s)"
                )

                return data

        except httpx.TimeoutException as e:
            logger.error(f"Timeout na conexão: {e}")
            raise Exception(f"Timeout ao conectar com a API: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP {e.response.status_code}: {e}")
            raise Exception(f"Erro HTTP {e.response.status_code}: {e}")
        except httpx.RequestError as e:
            logger.error(f"Erro de conexão: {e}")
            raise Exception(f"Erro de rede: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar ordens: {e}")
            raise

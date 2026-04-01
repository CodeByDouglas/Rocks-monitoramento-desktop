"""
Cliente de API para comunicação com o servidor
"""

import requests
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging
from config import API_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Classe para representar uma resposta da API"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: int = 0


class APIClient:
    """Cliente para comunicação com a API do servidor"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
    ):
        self.base_url = (base_url or API_CONFIG["base_url"]).rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Rocks-Monitoramento-Desktop/1.0"
        })

    def set_auth_token(self, token: Optional[str]):
        """Atualiza o header Authorization padrão da sessão."""
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        else:
            self.session.headers.pop("Authorization", None)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     timeout: int = 10) -> APIResponse:
        """Faz uma requisição HTTP para a API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=timeout)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, timeout=timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, timeout=timeout)
            else:
                return APIResponse(False, error=f"Método HTTP não suportado: {method}")
            
            # Processar resposta
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    return APIResponse(True, data=response_data, status_code=response.status_code)
                except json.JSONDecodeError:
                    return APIResponse(False, error="Resposta inválida do servidor", 
                                     status_code=response.status_code)
            else:
                error_msg = f"Erro HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg = error_data["message"]
                except json.JSONDecodeError:
                    pass
                
                return APIResponse(False, error=error_msg, status_code=response.status_code)
                
        except requests.exceptions.ConnectionError:
            return APIResponse(False, error="Erro de conexão. Verifique se o servidor está rodando.")
        except requests.exceptions.Timeout:
            return APIResponse(False, error="Timeout na conexão. Tente novamente.")
        except requests.exceptions.RequestException as e:
            return APIResponse(False, error=f"Erro na requisição: {str(e)}")
        except Exception as e:
            logger.error(f"Erro inesperado na requisição: {e}")
            return APIResponse(False, error=f"Erro inesperado: {str(e)}")
    
    def login(self, email: str, password: str, mac_address: str, username: str, operating_system: str) -> APIResponse:
        """Faz login na API"""
        payload = {
            "email": email,
            "password": password,
            "mac_address": mac_address,
            "username": username,
            "c": operating_system
        }
        
        logger.info(f"Tentando login para usuário: {email} - SO: {operating_system}")
        return self._make_request("POST", "/api/login", data=payload)
    
    def send_system_data(self, system_data: Dict[str, Any], auth_token: Optional[str] = None) -> APIResponse:
        """Envia dados do sistema para a API"""
        if auth_token is not None:
            self.set_auth_token(auth_token)

        logger.info("Enviando dados do sistema para a API")
        payload = {"data": system_data}
        return self.update_machine_status(payload)
    
    def health_check(self) -> APIResponse:
        """Verifica se a API está funcionando"""
        return self._make_request("GET", "/api/health")
    
    def update_machine_config(self, config_data: dict, auth_token: Optional[str] = None) -> APIResponse:
        """Atualiza a configuração da máquina"""
        if auth_token is not None:
            self.set_auth_token(auth_token)

        logger.info("Enviando configuração da máquina para a API")
        return self._make_request("POST", "/api/update_confg_maquina", data=config_data)

    def update_machine_status(self, status_data: dict, auth_token: Optional[str] = None) -> APIResponse:
        """Atualiza o status da máquina (dados de monitoramento)"""
        if auth_token is not None:
            self.set_auth_token(auth_token)

        logger.info("Enviando dados de status da máquina para a API")
        return self._make_request("PUT", "/api/maquina/status", data=status_data)

    def get_machine_config(self, mac_address: str, auth_token: Optional[str] = None) -> APIResponse:
        """Obtém configuração da máquina"""
        if auth_token is not None:
            self.set_auth_token(auth_token)

        return self._make_request("GET", f"/api/machine/{mac_address}")

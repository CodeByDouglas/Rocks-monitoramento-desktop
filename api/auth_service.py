"""
Serviço de autenticação para gerenciar credenciais e tokens
"""

import json
import os
import socket
import uuid
import psutil
import platform
import threading
from typing import Dict, Optional
from .api_client import APIClient, APIResponse
from config import FILE_CONFIG, API_CONFIG
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Serviço para gerenciar autenticação e informações da máquina"""

    def __init__(
        self,
        api_client: Optional[APIClient] = None,
        auth_state_file: Optional[str] = None,
    ):
        self.api_client = api_client or APIClient(base_url=API_CONFIG["base_url"])
        self._auth_token: Optional[str] = None
        self._machine_info: Optional[Dict[str, str]] = None
        self._machine_type: Optional[str] = None  # Novo campo para tipo de máquina
        default_state_path = FILE_CONFIG.get(
            "auth_state_file",
            os.path.join("data", "auth_state.json"),
        )
        self._auth_state_file = auth_state_file or default_state_path
        self._state_lock = threading.Lock()

        self._load_persisted_state()
    
    def get_mac_address(self) -> str:
        """Obtém o endereço MAC da primeira interface de rede"""
        try:
            # Obter todas as interfaces de rede
            interfaces = psutil.net_if_addrs()
            
            for interface_name, addresses in interfaces.items():
                for address in addresses:
                    # Procurar por endereço MAC (família AF_LINK no Windows)
                    if hasattr(address, 'family'):
                        if address.family == psutil.AF_LINK:
                            return address.address
                    # Alternativa para diferentes sistemas
                    elif hasattr(address, 'family') and address.family == 17:  # AF_LINK
                        return address.address
            
            # Fallback: usar uuid para obter MAC
            return ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0,2*6,2)][::-1])
        except Exception as e:
            logger.error(f"Erro ao obter MAC address: {e}")
            return "00:00:00:00:00:00"
    
    def get_hostname(self) -> str:
        """Obtém o nome do host da máquina"""
        try:
            return socket.gethostname()
        except Exception as e:
            logger.error(f"Erro ao obter hostname: {e}")
            return "unknown"
    
    def get_operating_system(self) -> str:
        """Obtém informações detalhadas do sistema operacional"""
        try:
            system = platform.system()
            release = platform.release()
            version = platform.version()
            
            # Formatar informações do SO
            if system == "Windows":
                # Para Windows, incluir versão mais detalhada
                win_ver = platform.win32_ver()
                return f"Windows {release} ({win_ver[0]})"
            elif system == "Linux":
                # Para Linux, incluir distribuição se disponível
                try:
                    distro = platform.linux_distribution()
                    if distro[0]:
                        return f"Linux {distro[0]} {distro[1]} ({release})"
                    else:
                        return f"Linux {release}"
                except:
                    return f"Linux {release}"
            elif system == "Darwin":
                # Para macOS
                return f"macOS {release}"
            else:
                return f"{system} {release}"
                
        except Exception as e:
            logger.error(f"Erro ao obter informações do SO: {e}")
            return "Unknown OS"
    
    def get_machine_info(self) -> Dict[str, str]:
        """Obtém informações básicas da máquina"""
        if self._machine_info is None:
            mac_address = self.get_mac_address()
            self._machine_info = {
                "hostname": self.get_hostname(),
                "mac_address": mac_address,
                "operating_system": self.get_operating_system(),
                "mac": mac_address,
            }
        return self._machine_info
    
    def authenticate(self, email: str, password: str) -> APIResponse:
        """Autentica o usuário na API"""
        machine_info = self.get_machine_info()
        
        response = self.api_client.login(
            email=email,
            password=password,
            mac_address=machine_info["mac_address"],
            username=machine_info["hostname"],
            operating_system=machine_info["operating_system"]
        )
        
        if response.success and response.data:
            # Extrair token se disponível
            if "token" in response.data:
                self._auth_token = response.data["token"]
                logger.info("Token de autenticação obtido com sucesso")
                self.api_client.set_auth_token(self._auth_token)
            
            # Extrair tipo de máquina se disponível
            machine_type = None
            
            # Procurar o tipo em diferentes níveis da resposta
            if "type" in response.data:
                machine_type = response.data["type"]
            elif "data" in response.data and "type" in response.data["data"]:
                machine_type = response.data["data"]["type"]
            elif "data" in response.data and "status" in response.data["data"] and "type" in response.data["data"]["status"]:
                machine_type = response.data["data"]["status"]["type"]
            
            if machine_type:
                self._machine_type = machine_type
                logger.info(f"Tipo de máquina identificado: {self._machine_type}")
            else:
                # Valor padrão se não especificado
                self._machine_type = "pc"
                logger.info("Tipo de máquina não especificado, usando padrão: pc")

            self._persist_state()

        return response
    
    def is_authenticated(self) -> bool:
        """Verifica se o usuário está autenticado"""
        return self._auth_token is not None
    
    def get_auth_token(self) -> Optional[str]:
        """Retorna o token de autenticação atual"""
        return self._auth_token
    
    def get_machine_type(self) -> str:
        """Retorna o tipo de máquina (pc ou server)"""
        return self._machine_type or "pc"
    
    def logout(self):
        """Faz logout do usuário"""
        self._auth_token = None
        self.api_client.set_auth_token(None)
        logger.info("Usuário fez logout")
        self._persist_state()
    
    def get_machine_config(self) -> APIResponse:
        """Obtém configuração da máquina atual"""
        if not self.is_authenticated():
            return APIResponse(False, error="Usuário não autenticado")
        
        machine_info = self.get_machine_info()
        return self.api_client.get_machine_config(
            mac_address=machine_info["mac_address"],
            auth_token=self._auth_token
        )
    
    def update_machine_config(self, config: Dict) -> APIResponse:
        """Atualiza configuração da máquina atual"""
        if not self.is_authenticated():
            return APIResponse(False, error="Usuário não autenticado")

        logger.info("Atualizando configuração da máquina com verificação de autenticação")
        return self.update_machine_configuration(config)
    
    def send_system_data(self, system_data: Dict) -> APIResponse:
        """Envia dados do sistema para a API"""
        if not self.is_authenticated():
            return APIResponse(False, error="Usuário não autenticado")

        payload = {"data": system_data}

        return self.api_client.update_machine_status(
            payload,
            auth_token=self._auth_token
        )
    
    def update_machine_configuration(self, config: Dict) -> APIResponse:
        """Atualiza a configuração da máquina"""
        logger.info("Enviando configuração da máquina (sem verificação de token)")
        
        # Obter informações da máquina
        machine_info = self.get_machine_info()
        
        # Preparar dados no formato esperado pelo servidor
        config_data = {
            "data": {
                "Nome": config.get("machine_name", ""),
                "MAC": machine_info["mac_address"],
                "type": self.get_machine_type(),
                "Notificar": config.get("notifications", False),
                "Frequency": config.get("update_frequency", 1),
                "iniciarSO": config.get("start_with_os", False),
                "status": {
                    "DISCO": config.get("monitored_status", {}).get("disco", False),
                    "REDE": config.get("monitored_status", {}).get("rede", False),
                    "RAM": config.get("monitored_status", {}).get("ram", False),
                    "TEMPERATURA": config.get("monitored_status", {}).get("temperatura", False),
                    "PROCESSO": config.get("monitored_status", {}).get("processos", False),
                    "CPU": config.get("monitored_status", {}).get("cpu", False)
                }
            }
        }
        
        logger.info(f"Enviando configuração da máquina: {config_data}")
        return self.api_client.update_machine_config(
            config_data,
            auth_token=self._auth_token
        )

    def _load_persisted_state(self):
        """Carrega token e metadados persistidos em disco, se existirem."""
        try:
            if not os.path.exists(self._auth_state_file):
                return

            with open(self._auth_state_file, "r", encoding="utf-8") as fp:
                data = json.load(fp)

            token = data.get("auth_token")
            machine_type = data.get("machine_type")
            machine_info = data.get("machine_info")

            if token:
                self._auth_token = token
                self.api_client.set_auth_token(token)
                logger.info("Token de autenticação carregado do arquivo")

            if machine_type:
                self._machine_type = machine_type

            if machine_info:
                self._machine_info = machine_info

        except Exception as exc:
            logger.error(f"Não foi possível carregar estado de autenticação: {exc}")

    def _persist_state(self):
        """Persiste token e informações relevantes para uso por outros processos."""
        try:
            os.makedirs(os.path.dirname(self._auth_state_file), exist_ok=True)
            with self._state_lock:
                payload = {
                    "auth_token": self._auth_token,
                    "machine_type": self._machine_type,
                    "machine_info": self._machine_info,
                }

                with open(self._auth_state_file, "w", encoding="utf-8") as fp:
                    json.dump(payload, fp, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.error(f"Não foi possível salvar estado de autenticação: {exc}")

"""
Configurações centralizadas do sistema de monitoramento Rocks
"""

import os
from typing import Dict, Any

# Configurações da API
API_CONFIG = {
    "base_url": os.getenv(
        "ROCKS_API_URL",
        "http://localhost:8000",
    ),
    "timeout": 10,
    "user_agent": "Rocks-Monitoramento-Desktop/1.0"
}

# Configurações de logging
LOGGING_CONFIG = {
    "level": os.getenv("ROCKS_LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": os.path.join("data", "rocks_monitoramento.log"),
    "encoding": "utf-8"
}

# Configurações da interface
UI_CONFIG = {
    "window_size": {
        "login": (400, 600),
        "config": (480, 800)
    },
    "colors": {
        "primary": "#007AFF",
        "background": "#1C1C1E",
        "surface": "#2A2A2A",
        "text": "#FFFFFF",
        "text_secondary": "#8E8E93",
        "error": "#FF3B30",
        "success": "#34C759"
    },
    "fonts": {
        "primary": "SF Pro Display",
        "fallback": "Segoe UI"
    }
}

# Configurações de monitoramento
MONITORING_CONFIG = {
    "default_interval": 5,  # segundos
    "min_interval": 1,
    "max_interval": 10,
    "top_processes_limit": 5
}

# Configurações de autenticação
AUTH_CONFIG = {
    "session_timeout": 3600,  # 1 hora em segundos
    "retry_attempts": 3,
    "retry_delay": 2  # segundos
}

# Configurações de arquivos
FILE_CONFIG = {
    "system_data_file": os.path.join("data", "dados_sistema.json"),
    "log_file": os.path.join("data", "rocks_monitoramento.log"),
    "machine_config_file": os.path.join("data", "configuracao_maquina.json"),
    "background_monitor_script": os.path.join("scripts", "background_monitor.py"),
    "auth_state_file": os.path.join("data", "auth_state.json"),
}

def get_config() -> Dict[str, Any]:
    """Retorna todas as configurações em um dicionário"""
    return {
        "api": API_CONFIG,
        "logging": LOGGING_CONFIG,
        "ui": UI_CONFIG,
        "monitoring": MONITORING_CONFIG,
        "auth": AUTH_CONFIG,
        "files": FILE_CONFIG
    }

#!/usr/bin/env python3
"""
Script para parar o monitoramento em background
"""

import sys
import os
import signal
import subprocess
import logging

# Adicionar o diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import LOGGING_CONFIG

# Configurar logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]),
    format=LOGGING_CONFIG["format"],
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def find_monitor_processes():
    """Encontra processos do monitoramento em background"""
    try:
        # Usar ps para encontrar processos Python rodando background_monitor.py
        if sys.platform.startswith('win'):
            # Windows
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                capture_output=True,
                text=True
            )
            # Processar resultado no Windows seria mais complexo
            return []
        else:
            # Linux/Mac
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )
            
            processes = []
            for line in result.stdout.split('\n'):
                if 'background_monitor.py' in line and 'grep' not in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = int(parts[1])
                        processes.append(pid)
            
            return processes
    except Exception as e:
        logger.error(f"Erro ao encontrar processos: {e}")
        return []


def stop_monitor():
    """Para o monitoramento em background"""
    processes = find_monitor_processes()
    
    if not processes:
        print("✅ Nenhum processo de monitoramento encontrado em execução.")
        return True
    
    print(f"📊 Encontrados {len(processes)} processo(s) de monitoramento:")
    
    stopped = 0
    for pid in processes:
        try:
            # Tentar parar graciosamente primeiro
            os.kill(pid, signal.SIGTERM)
            print(f"   ⏹️  Processo {pid} recebeu sinal de parada (SIGTERM)")
            stopped += 1
        except ProcessLookupError:
            print(f"   ⚠️  Processo {pid} não existe mais")
        except PermissionError:
            print(f"   ❌ Sem permissão para parar processo {pid}")
            print(f"      Tente executar: sudo kill {pid}")
        except Exception as e:
            print(f"   ❌ Erro ao parar processo {pid}: {e}")
    
    if stopped > 0:
        print(f"\n✅ {stopped} processo(s) receberam sinal de parada.")
        print("   Aguarde alguns segundos para o processo finalizar graciosamente.")
        print("   Se não parar, você pode forçar com: kill -9 <PID>")
        return True
    
    return False


def force_stop_monitor():
    """Força a parada do monitoramento (SIGKILL)"""
    processes = find_monitor_processes()
    
    if not processes:
        print("✅ Nenhum processo de monitoramento encontrado em execução.")
        return True
    
    print(f"🛑 Forçando parada de {len(processes)} processo(s):")
    
    stopped = 0
    for pid in processes:
        try:
            os.kill(pid, signal.SIGKILL)
            print(f"   ⛔ Processo {pid} foi finalizado forçadamente")
            stopped += 1
        except ProcessLookupError:
            print(f"   ⚠️  Processo {pid} não existe mais")
        except PermissionError:
            print(f"   ❌ Sem permissão para parar processo {pid}")
            print(f"      Tente executar: sudo kill -9 {pid}")
        except Exception as e:
            print(f"   ❌ Erro ao parar processo {pid}: {e}")
    
    if stopped > 0:
        print(f"\n✅ {stopped} processo(s) foram finalizados.")
        return True
    
    return False


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Para o monitoramento em background do sistema Rocks'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Força a parada imediata (SIGKILL) ao invés de parada graciosa (SIGTERM)'
    )
    
    args = parser.parse_args()
    
    if args.force:
        force_stop_monitor()
    else:
        stop_monitor()


if __name__ == "__main__":
    main()



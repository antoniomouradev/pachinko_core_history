import os
import time
import logging
import colorlog
from pathlib import Path
from logging.handlers import RotatingFileHandler


def silence_external_loggers():
    """Silencia bibliotecas externas barulhentas."""
    logging.getLogger("aiomysql.connection").propagate = False
    for name in logging.root.manager.loggerDict:
        if name.startswith("aiomysql"):
            logging.getLogger(name).setLevel(logging.WARNING)

    for noisy in ["urllib3", "asyncio", "requests", "tornado.access"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def gmt_minus_3(*args):
    """Ajusta timestamps do log para GMT-3."""
    return time.gmtime(time.mktime(time.localtime()) - 3 * 3600)


def create_file_handler(log_file):
    """Cria handler de log para arquivo com rotação."""
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] (%(filename)s:%(funcName)s:%(lineno)d): %(message)s'
    )
    file_formatter.converter = gmt_minus_3

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=50
    )
    file_handler.setFormatter(file_formatter)
    return file_handler


def create_console_handler():
    """Cria handler de log para console com cores."""
    color_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s [%(levelname)s] (%(filename)s:%(funcName)s:%(lineno)d): %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )
    color_formatter.converter = gmt_minus_3

    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(color_formatter)
    return console_handler


def infer_log_folder():
    """Inferir o diretório ideal de logs com base no ambiente."""
    # Se LOG_FOLDER estiver definido no ambiente, usa ele
    if "LOG_FOLDER" in os.environ:
        return Path(os.environ["LOG_FOLDER"])

    # Detectar se está rodando em Docker
    try:
        with open("/proc/1/cgroup", "rt") as f:
            if "docker" in f.read():
                return Path("/log")
    except Exception:
        pass

    # Caso contrário, assume diretório local ./log
    return Path(__file__).resolve().parent.parent / "log"


# Caminhos finais
LOG_FOLDER = infer_log_folder()
LOG_FILE = LOG_FOLDER / "server.log"

# Criar diretório se necessário
os.makedirs(LOG_FOLDER, exist_ok=True)


def start():
    """Inicializa o sistema de logging global."""
    silence_external_loggers()

    file_handler = create_file_handler(str(LOG_FILE))
    console_handler = create_console_handler()

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler, console_handler]
    )

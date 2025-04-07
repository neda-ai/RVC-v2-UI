"""FastAPI server configuration."""

import dataclasses
import logging
import logging.config
import os
import sys
from pathlib import Path

import dotenv
import torch
from singleton import Singleton

dotenv.load_dotenv()

base_dir: Path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str((base_dir / "src").resolve()))


@dataclasses.dataclass
class Settings(metaclass=Singleton):
    """Server config settings."""

    base_dir: Path = base_dir
    rvc_models_dir: Path = base_dir / "rvc_models"
    output_dir: Path = base_dir / "voice_output"
    device: str = "cuda:0" if torch.cuda.is_available() else "cpu"
    is_half: bool = False if device == "cpu" else True

    UFILES_API_KEY: str = os.getenv("UFILES_API_KEY")
    UFILES_BASE_URL: str = os.getenv("UFILES_BASE_URL", "https://media.pixiee.io/v1/f/")

    @classmethod
    def get_log_config(
        cls, console_level: str = "INFO", file_level: str = "INFO", **kwargs
    ):
        log_config = {
            "formatters": {
                "standard": {
                    "format": "[{levelname} : {filename}:{lineno} : {asctime} -> {funcName:10}] {message}",
                    "style": "{",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": console_level,
                    "formatter": "standard",
                },
                "file": {
                    "class": "logging.FileHandler",
                    "level": file_level,
                    "filename": cls.base_dir / "logs" / "info.log",
                    "formatter": "standard",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": True,
                },
                "httpx": {
                    "handlers": ["console", "file"],
                    "level": "WARNING",
                    "propagate": False,
                },
            },
            "version": 1,
        }
        return log_config

    @classmethod
    def config_logger(cls):
        (cls.base_dir / "logs").mkdir(parents=True, exist_ok=True)

        logging.config.dictConfig(cls.get_log_config())

        if cls.device != "cpu":
            logging.info(f"Using GPU: {torch.cuda.get_device_name()}")
            logging.info(
                f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB"
            )

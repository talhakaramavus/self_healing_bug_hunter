"""
logger.py - Self-Healing Bug Hunter Renkli Konsol Loglayıcısı

Bu modül, terminal çıktılarını profesyonel ve renkli bir biçimde biçimlendirir.
"""

import sys

class Logger:
    """Terminal çıktıları için renkli loglayıcı sınıfı."""

    # ANSI Renk Kodları
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def info(message: str):
        print(f"{Logger.OKCYAN}ℹ️  [INFO] {message}{Logger.ENDC}")

    @staticmethod
    def success(message: str):
        print(f"{Logger.OKGREEN}✅ [SUCCESS] {message}{Logger.ENDC}")

    @staticmethod
    def warning(message: str):
        print(f"{Logger.WARNING}⚠️  [WARNING] {message}{Logger.ENDC}")

    @staticmethod
    def error(message: str):
        print(f"{Logger.FAIL}❌ [ERROR] {message}{Logger.ENDC}")

    @staticmethod
    def step(title: str):
        print(f"\n{Logger.BOLD}{Logger.OKBLUE}📌 {title}{Logger.ENDC}")

    @staticmethod
    def banner(title: str):
        border = "=" * 80
        print(f"\n{Logger.BOLD}{Logger.HEADER}{border}\n🚀 {title}\n{border}{Logger.ENDC}\n")

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(__file__))

# Importar a aplicação Flask
from src.main import app as application

if __name__ == "__main__":
    application.run()


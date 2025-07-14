#!/usr/bin/env python3
"""
Script de inicialização do sistema de concessionária
Execute este script após fazer upload para a Hostinger
"""

import os
import sys
import secrets
from datetime import datetime

def generate_secret_key():
    """Gera uma chave secreta segura"""
    return secrets.token_urlsafe(32)

def create_env_file():
    """Cria arquivo .env com configurações seguras"""
    if os.path.exists('.env'):
        print("Arquivo .env já existe. Pulando criação...")
        return
    
    secret_key = generate_secret_key()
    jwt_secret = generate_secret_key()
    
    env_content = f"""# Configurações de Produção - Gerado em {datetime.now()}

# Chaves secretas (geradas automaticamente)
SECRET_KEY={secret_key}
JWT_SECRET_KEY={jwt_secret}

# Ambiente
FLASK_ENV=production
DEBUG=False

# Banco de dados
DATABASE_URL=sqlite:///src/database/app.db

# Upload
MAX_CONTENT_LENGTH=5242880
UPLOAD_FOLDER=uploads

# Configurações de segurança
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✓ Arquivo .env criado com chaves secretas seguras")

def create_directories():
    """Cria diretórios necessários"""
    directories = [
        'uploads',
        'src/database',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Diretório {directory} criado/verificado")

def set_permissions():
    """Define permissões corretas para os arquivos"""
    try:
        # Permissões para diretórios
        os.chmod('uploads', 0o755)
        os.chmod('src', 0o755)
        os.chmod('src/database', 0o755)
        
        # Permissões para arquivos sensíveis
        if os.path.exists('.env'):
            os.chmod('.env', 0o600)
        
        print("✓ Permissões configuradas")
    except Exception as e:
        print(f"⚠ Erro ao configurar permissões: {e}")

def create_htaccess_uploads():
    """Cria .htaccess para proteger diretório de uploads"""
    htaccess_content = """# Permitir apenas imagens
<FilesMatch "\\.(jpg|jpeg|png|webp)$">
    Order allow,deny
    Allow from all
</FilesMatch>

# Negar acesso a outros tipos de arquivo
<FilesMatch "\\.">
    Order allow,deny
    Deny from all
</FilesMatch>

# Desabilitar execução de scripts
Options -ExecCGI
AddHandler cgi-script .php .pl .py .jsp .asp .sh .cgi
"""
    
    uploads_htaccess = os.path.join('uploads', '.htaccess')
    with open(uploads_htaccess, 'w') as f:
        f.write(htaccess_content)
    
    print("✓ Proteção do diretório uploads configurada")

def initialize_database():
    """Inicializa o banco de dados"""
    try:
        # Adicionar o diretório atual ao path
        sys.path.insert(0, os.path.dirname(__file__))
        
        from src.main import app
        from src.models.user import db as user_db, User
        from src.models.vehicle import db as vehicle_db
        
        with app.app_context():
            # Criar tabelas
            user_db.create_all()
            vehicle_db.create_all()
            
            # Verificar se já existe usuário admin
            admin_user = User.query.filter_by(email='admin@concessionaria.com').first()
            if not admin_user:
                admin_user = User(
                    email='admin@concessionaria.com',
                    role='admin'
                )
                admin_user.set_password('admin123')
                user_db.session.add(admin_user)
                user_db.session.commit()
                print("✓ Usuário administrador criado")
                print("  Email: admin@concessionaria.com")
                print("  Senha: admin123")
                print("  ⚠ ALTERE ESTAS CREDENCIAIS IMEDIATAMENTE!")
            else:
                print("✓ Usuário administrador já existe")
        
        print("✓ Banco de dados inicializado")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        return False
    
    return True

def main():
    """Função principal de inicialização"""
    print("=== Inicialização do Sistema de Concessionária ===")
    print()
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('src/main.py'):
        print("❌ Execute este script no diretório raiz do projeto")
        sys.exit(1)
    
    # Executar etapas de inicialização
    create_env_file()
    create_directories()
    set_permissions()
    create_htaccess_uploads()
    
    # Tentar inicializar banco de dados
    if initialize_database():
        print()
        print("✅ Inicialização concluída com sucesso!")
        print()
        print("Próximos passos:")
        print("1. Altere as credenciais do administrador")
        print("2. Configure seu domínio para apontar para este diretório")
        print("3. Ative o certificado SSL")
        print("4. Teste o sistema acessando seu domínio")
        print()
        print("Para suporte, consulte o manual_hostinger.md")
    else:
        print()
        print("❌ Inicialização falhou. Verifique os erros acima.")
        print("Consulte o manual_hostinger.md para solução de problemas.")

if __name__ == "__main__":
    main()


# Sistema de Catálogo de Veículos

Sistema completo para concessionárias com backend Flask seguro e frontend React moderno.

## Características

- ✅ **Backend Flask** com API RESTful segura
- ✅ **Autenticação JWT** com proteção contra ataques
- ✅ **Upload seguro de imagens** com validação rigorosa
- ✅ **Frontend React** responsivo e moderno
- ✅ **Sistema de filtros avançados** para catálogo
- ✅ **Área administrativa** completa com dashboard
- ✅ **Proteção OWASP Top 10** implementada
- ✅ **Rate limiting** e headers de segurança
- ✅ **Banco SQLite** para fácil implantação

## Instalação Rápida

### 1. Desenvolvimento Local

```bash
# Clonar/extrair o projeto
cd concessionaria-backend

# Instalar dependências
pip install -r requirements.txt

# Executar setup inicial
python setup.py

# Iniciar servidor
python src/main.py
```

### 2. Produção na Hostinger

1. Faça upload de todos os arquivos para `public_html`
2. Execute: `python3 setup.py`
3. Configure seu domínio
4. Ative SSL
5. Teste o sistema

Consulte `manual_hostinger.md` para instruções detalhadas.

## Credenciais Padrão

- **Email:** admin@concessionaria.com
- **Senha:** admin123

**⚠️ ALTERE IMEDIATAMENTE EM PRODUÇÃO!**

## Estrutura do Projeto

```
concessionaria-backend/
├── src/
│   ├── main.py              # Aplicação principal
│   ├── models/              # Modelos do banco de dados
│   ├── routes/              # Rotas da API
│   └── static/              # Frontend React (build)
├── uploads/                 # Imagens dos veículos
├── requirements.txt         # Dependências Python
├── setup.py                # Script de inicialização
├── passenger_wsgi.py       # Configuração WSGI
├── .htaccess               # Configuração Apache
└── README.md               # Este arquivo
```

## API Endpoints

### Públicos
- `GET /api/vehicles` - Listar veículos
- `GET /api/vehicles/{id}` - Detalhes do veículo

### Administrativos (requer autenticação)
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Usuário atual
- `POST /api/admin/vehicles` - Criar veículo
- `PUT /api/admin/vehicles/{id}` - Atualizar veículo
- `DELETE /api/admin/vehicles/{id}` - Excluir veículo
- `POST /api/admin/vehicles/{id}/upload` - Upload imagem

## Funcionalidades

### Área Pública
- Catálogo interativo com filtros avançados
- Busca por marca, modelo, ano, preço, categoria
- Detalhes completos dos veículos
- Integração WhatsApp para contato
- Design responsivo

### Área Administrativa
- Dashboard com estatísticas
- CRUD completo de veículos
- Upload múltiplo de imagens
- Sistema de autenticação seguro
- Logs de auditoria

## Segurança

- Autenticação JWT com expiração
- Hash bcrypt para senhas
- Rate limiting em endpoints críticos
- Validação rigorosa de uploads
- Headers de segurança (HSTS, CSP, etc.)
- Proteção contra XSS, CSRF, SQL Injection
- Soft delete para preservar dados

## Suporte

- **Manual completo:** `manual_hostinger.md`
- **Configuração:** `setup.py`
- **Exemplo de produção:** `.env.example`

## Tecnologias

- **Backend:** Flask, SQLAlchemy, JWT, bcrypt
- **Frontend:** React, Tailwind CSS, Radix UI
- **Banco:** SQLite (desenvolvimento) / PostgreSQL (produção)
- **Segurança:** OWASP Top 10, Rate Limiting, CORS

## Licença

Sistema desenvolvido para uso comercial em concessionárias.

---

**Desenvolvido por:** Manus AI  
**Versão:** 1.0  
**Data:** Janeiro 2025


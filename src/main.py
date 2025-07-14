import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import timedelta

# Importar modelos
from src.models.user import db as user_db, User
from src.models.vehicle import db as vehicle_db, Vehicle, VehicleImage

# Importar blueprints
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.vehicles import vehicles_bp
from src.routes.uploads import uploads_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configurações de segurança
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sua-chave-secreta-super-forte-aqui-mude-em-producao')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-chave-secreta-super-forte-aqui-mude-em-producao')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_ALGORITHM'] = 'HS256'

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurações de upload
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

# Inicializar extensões
jwt = JWTManager(app)
cors = CORS(app, origins="*")  # Em produção, especificar domínios específicos

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"]
)

# Inicializar banco de dados
user_db.init_app(app)
vehicle_db.init_app(app)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(vehicles_bp, url_prefix='/api')
app.register_blueprint(uploads_bp, url_prefix='/api')

# Handlers de erro JWT
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token expirado'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Token inválido'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Token de acesso necessário'}), 401

# Rate limiting para login
@limiter.limit("5 per minute")
@app.route('/api/auth/login', methods=['POST'])
def login_rate_limited():
    from src.routes.auth import login
    return login()

# Criar tabelas e usuário admin padrão
with app.app_context():
    user_db.create_all()
    vehicle_db.create_all()
    
    # Criar usuário admin padrão se não existir
    admin_user = User.query.filter_by(email='admin@concessionaria.com').first()
    if not admin_user:
        admin_user = User(
            email='admin@concessionaria.com',
            role='admin'
        )
        admin_user.set_password('admin123')  # MUDE ESTA SENHA EM PRODUÇÃO!
        user_db.session.add(admin_user)
        user_db.session.commit()
        print("Usuário admin criado: admin@concessionaria.com / admin123")

# Rota para servir o frontend React
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

# Headers de segurança
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Tratamento de erros
@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'Arquivo muito grande'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Recurso não encontrado'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

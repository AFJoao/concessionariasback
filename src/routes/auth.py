from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from src.models.user import User, db
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

class LoginSchema(Schema):
    email = fields.Email(required=True, error_messages={'required': 'Email é obrigatório'})
    password = fields.Str(required=True, validate=lambda x: len(x) >= 6, 
                         error_messages={'required': 'Senha é obrigatória'})

@auth_bp.route('/login', methods=['POST'])
def login():
    """Endpoint de login do administrador"""
    try:
        # Validar dados de entrada
        schema = LoginSchema()
        data = schema.load(request.get_json() or {})
        
        email = data['email']
        password = data['password']
        
        # Buscar usuário
        user = User.query.filter_by(email=email, is_active=True).first()
        
        if not user:
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        # Verificar se a conta está bloqueada
        if user.is_locked():
            return jsonify({'error': 'Conta temporariamente bloqueada. Tente novamente em alguns minutos.'}), 423
        
        # Verificar senha
        if not user.check_password(password):
            user.increment_failed_attempts()
            db.session.commit()
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        # Login bem-sucedido
        user.reset_failed_attempts()
        db.session.commit()
        
        # Criar token JWT
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24),
            additional_claims={'role': user.role, 'email': user.email}
        )
        
        return jsonify({
            'message': 'Login realizado com sucesso',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 400
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Retorna informações do usuário logado"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Endpoint de logout (cliente deve descartar o token)"""
    return jsonify({'message': 'Logout realizado com sucesso'}), 200


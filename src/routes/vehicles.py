from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import Schema, fields, ValidationError, validate
from src.models.vehicle import Vehicle, db
from src.models.user import User
from sqlalchemy import or_, and_

vehicles_bp = Blueprint('vehicles', __name__)

class VehicleSchema(Schema):
    marca = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    modelo = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    ano = fields.Int(required=True, validate=validate.Range(min=1900, max=2030))
    preco = fields.Float(required=True, validate=validate.Range(min=0, max=10000000))
    descricao = fields.Str(validate=validate.Length(max=2000))
    combustivel = fields.Str(validate=validate.OneOf(['Gasolina', 'Etanol', 'Flex', 'Diesel', 'Elétrico', 'Híbrido']))
    cambio = fields.Str(validate=validate.OneOf(['Manual', 'Automático', 'CVT', 'Automatizada']))
    cor = fields.Str(validate=validate.Length(max=50))
    quilometragem = fields.Int(validate=validate.Range(min=0, max=1000000))
    categoria = fields.Str(validate=validate.OneOf(['Hatch', 'Sedan', 'SUV', 'Picape', 'Conversível', 'Wagon', 'Coupé']))
    imagens = fields.List(fields.Str())

def require_admin():
    """Decorator para verificar se o usuário é admin"""
    def decorator(f):
        from functools import wraps
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != 'admin':
                return jsonify({'error': 'Acesso negado'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Rotas públicas (sem autenticação)
@vehicles_bp.route('/vehicles', methods=['GET'])
def get_vehicles():
    """Lista veículos ativos com filtros e paginação"""
    try:
        # Parâmetros de filtro
        marca = request.args.get('marca')
        modelo = request.args.get('modelo')
        ano_min = request.args.get('ano_min', type=int)
        ano_max = request.args.get('ano_max', type=int)
        preco_min = request.args.get('preco_min', type=float)
        preco_max = request.args.get('preco_max', type=float)
        combustivel = request.args.get('combustivel')
        categoria = request.args.get('categoria')
        search = request.args.get('search')
        
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 12, type=int), 50)  # Máximo 50 por página
        
        # Query base
        query = Vehicle.query.filter_by(is_active=True)
        
        # Aplicar filtros
        if marca:
            query = query.filter(Vehicle.marca.ilike(f'%{marca}%'))
        if modelo:
            query = query.filter(Vehicle.modelo.ilike(f'%{modelo}%'))
        if ano_min:
            query = query.filter(Vehicle.ano >= ano_min)
        if ano_max:
            query = query.filter(Vehicle.ano <= ano_max)
        if preco_min:
            query = query.filter(Vehicle.preco >= preco_min)
        if preco_max:
            query = query.filter(Vehicle.preco <= preco_max)
        if combustivel:
            query = query.filter(Vehicle.combustivel == combustivel)
        if categoria:
            query = query.filter(Vehicle.categoria == categoria)
        if search:
            search_filter = or_(
                Vehicle.marca.ilike(f'%{search}%'),
                Vehicle.modelo.ilike(f'%{search}%'),
                Vehicle.descricao.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        # Ordenação
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        if hasattr(Vehicle, sort_by):
            if sort_order == 'asc':
                query = query.order_by(getattr(Vehicle, sort_by).asc())
            else:
                query = query.order_by(getattr(Vehicle, sort_by).desc())
        
        # Paginação
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        vehicles = [vehicle.to_dict() for vehicle in pagination.items]
        
        return jsonify({
            'vehicles': vehicles,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@vehicles_bp.route('/vehicles/<int:vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    """Retorna detalhes de um veículo específico"""
    try:
        vehicle = Vehicle.query.filter_by(id=vehicle_id, is_active=True).first()
        
        if not vehicle:
            return jsonify({'error': 'Veículo não encontrado'}), 404
        
        return jsonify({'vehicle': vehicle.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Rotas administrativas (requerem autenticação)
@vehicles_bp.route('/admin/vehicles', methods=['GET'])
@require_admin()
def get_admin_vehicles():
    """Lista todos os veículos (incluindo inativos) para administradores"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        pagination = Vehicle.query.order_by(Vehicle.created_at.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        vehicles = [vehicle.to_dict() for vehicle in pagination.items]
        
        return jsonify({
            'vehicles': vehicles,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@vehicles_bp.route('/admin/vehicles', methods=['POST'])
@require_admin()
def create_vehicle():
    """Cria um novo veículo"""
    try:
        schema = VehicleSchema()
        data = schema.load(request.get_json() or {})
        
        vehicle = Vehicle(
            marca=data['marca'],
            modelo=data['modelo'],
            ano=data['ano'],
            preco=data['preco'],
            descricao=data.get('descricao'),
            combustivel=data.get('combustivel'),
            cambio=data.get('cambio'),
            cor=data.get('cor'),
            quilometragem=data.get('quilometragem', 0),
            categoria=data.get('categoria')
        )
        
        # Definir imagens se fornecidas
        if 'imagens' in data:
            vehicle.set_imagens(data['imagens'])
        
        db.session.add(vehicle)
        db.session.commit()
        
        return jsonify({
            'message': 'Veículo criado com sucesso',
            'vehicle': vehicle.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 400
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@vehicles_bp.route('/admin/vehicles/<int:vehicle_id>', methods=['PUT'])
@require_admin()
def update_vehicle(vehicle_id):
    """Atualiza um veículo existente"""
    try:
        vehicle = Vehicle.query.get(vehicle_id)
        
        if not vehicle:
            return jsonify({'error': 'Veículo não encontrado'}), 404
        
        schema = VehicleSchema()
        data = schema.load(request.get_json() or {})
        
        # Atualizar campos
        vehicle.marca = data['marca']
        vehicle.modelo = data['modelo']
        vehicle.ano = data['ano']
        vehicle.preco = data['preco']
        vehicle.descricao = data.get('descricao')
        vehicle.combustivel = data.get('combustivel')
        vehicle.cambio = data.get('cambio')
        vehicle.cor = data.get('cor')
        vehicle.quilometragem = data.get('quilometragem', 0)
        vehicle.categoria = data.get('categoria')
        
        # Atualizar imagens se fornecidas
        if 'imagens' in data:
            vehicle.set_imagens(data['imagens'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Veículo atualizado com sucesso',
            'vehicle': vehicle.to_dict()
        }), 200
        
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 400
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@vehicles_bp.route('/admin/vehicles/<int:vehicle_id>', methods=['DELETE'])
@require_admin()
def delete_vehicle(vehicle_id):
    """Exclui um veículo (soft delete)"""
    try:
        vehicle = Vehicle.query.get(vehicle_id)
        
        if not vehicle:
            return jsonify({'error': 'Veículo não encontrado'}), 404
        
        # Soft delete
        vehicle.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'Veículo excluído com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@vehicles_bp.route('/admin/dashboard/stats', methods=['GET'])
@require_admin()
def get_dashboard_stats():
    """Retorna estatísticas para o dashboard administrativo"""
    try:
        total_vehicles = Vehicle.query.filter_by(is_active=True).count()
        total_inactive = Vehicle.query.filter_by(is_active=False).count()
        
        # Estatísticas por categoria
        categories = db.session.query(
            Vehicle.categoria, 
            db.func.count(Vehicle.id)
        ).filter_by(is_active=True).group_by(Vehicle.categoria).all()
        
        # Estatísticas por marca
        brands = db.session.query(
            Vehicle.marca, 
            db.func.count(Vehicle.id)
        ).filter_by(is_active=True).group_by(Vehicle.marca).all()
        
        return jsonify({
            'total_vehicles': total_vehicles,
            'total_inactive': total_inactive,
            'categories': [{'name': cat[0], 'count': cat[1]} for cat in categories if cat[0]],
            'brands': [{'name': brand[0], 'count': brand[1]} for brand in brands if brand[0]]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500


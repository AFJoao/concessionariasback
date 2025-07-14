from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt
from werkzeug.utils import secure_filename
from PIL import Image
import magic
import os
import uuid
from datetime import datetime
from src.models.vehicle import Vehicle, VehicleImage, db

uploads_bp = Blueprint('uploads', __name__)

# Configurações de upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_DIMENSION = 2048

# Criar diretório de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image_file(file):
    """Valida o arquivo de imagem"""
    # Verificar tamanho
    file.seek(0, os.SEEK_END)
    size = file.tell()
    if size > MAX_FILE_SIZE:
        raise ValueError(f'Arquivo muito grande. Máximo permitido: {MAX_FILE_SIZE // (1024*1024)}MB')
    
    file.seek(0)
    
    # Verificar tipo MIME
    mime_type = magic.from_buffer(file.read(1024), mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError('Tipo de arquivo não permitido. Use apenas JPEG, PNG ou WebP')
    
    file.seek(0)
    
    # Verificar se é uma imagem válida
    try:
        with Image.open(file) as img:
            # Verificar dimensões
            if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
                raise ValueError(f'Imagem muito grande. Máximo: {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION} pixels')
            
            # Verificar se não é um arquivo malicioso
            img.verify()
    except Exception as e:
        raise ValueError('Arquivo de imagem inválido ou corrompido')
    
    file.seek(0)
    return True

def process_image(file, vehicle_id):
    """Processa e salva a imagem"""
    # Gerar nome único
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.jpg"  # Sempre salvar como JPEG
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # Processar imagem
    with Image.open(file) as img:
        # Converter para RGB se necessário
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionar mantendo proporção se necessário
        if img.width > 1200 or img.height > 800:
            img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
        
        # Salvar com qualidade otimizada
        img.save(filepath, 'JPEG', quality=85, optimize=True)
    
    # Gerar thumbnail
    thumbnail_filename = f"thumb_{filename}"
    thumbnail_path = os.path.join(UPLOAD_FOLDER, thumbnail_filename)
    
    with Image.open(filepath) as img:
        img.thumbnail((300, 200), Image.Resampling.LANCZOS)
        img.save(thumbnail_path, 'JPEG', quality=80, optimize=True)
    
    return filename, thumbnail_filename, os.path.getsize(filepath)

@uploads_bp.route('/admin/vehicles/<int:vehicle_id>/upload', methods=['POST'])
@require_admin()
def upload_vehicle_image(vehicle_id):
    """Upload de imagem para um veículo"""
    try:
        # Verificar se o veículo existe
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({'error': 'Veículo não encontrado'}), 404
        
        # Verificar se há arquivo na requisição
        if 'image' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de arquivo não permitido'}), 400
        
        # Validar arquivo
        validate_image_file(file)
        
        # Processar e salvar imagem
        filename, thumbnail_filename, file_size = process_image(file, vehicle_id)
        
        # Salvar informações no banco
        vehicle_image = VehicleImage(
            vehicle_id=vehicle_id,
            filename=filename,
            original_filename=secure_filename(file.filename),
            file_path=os.path.join(UPLOAD_FOLDER, filename),
            file_size=file_size,
            mime_type='image/jpeg',
            image_order=len(vehicle.vehicle_images)
        )
        
        db.session.add(vehicle_image)
        
        # Atualizar lista de imagens do veículo
        current_images = vehicle.get_imagens()
        current_images.append(f'/api/uploads/{filename}')
        vehicle.set_imagens(current_images)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Imagem enviada com sucesso',
            'image': vehicle_image.to_dict(),
            'url': f'/api/uploads/{filename}',
            'thumbnail_url': f'/api/uploads/{thumbnail_filename}'
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@uploads_bp.route('/admin/images/<int:image_id>', methods=['DELETE'])
@require_admin()
def delete_vehicle_image(image_id):
    """Remove uma imagem de veículo"""
    try:
        vehicle_image = VehicleImage.query.get(image_id)
        if not vehicle_image:
            return jsonify({'error': 'Imagem não encontrada'}), 404
        
        vehicle = vehicle_image.vehicle
        
        # Remover arquivos do disco
        try:
            if os.path.exists(vehicle_image.file_path):
                os.remove(vehicle_image.file_path)
            
            # Remover thumbnail
            thumbnail_path = os.path.join(UPLOAD_FOLDER, f"thumb_{vehicle_image.filename}")
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except OSError:
            pass  # Arquivo pode não existir
        
        # Atualizar lista de imagens do veículo
        current_images = vehicle.get_imagens()
        image_url = f'/api/uploads/{vehicle_image.filename}'
        if image_url in current_images:
            current_images.remove(image_url)
            vehicle.set_imagens(current_images)
        
        # Remover do banco
        db.session.delete(vehicle_image)
        db.session.commit()
        
        return jsonify({'message': 'Imagem removida com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@uploads_bp.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve arquivos de upload"""
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except FileNotFoundError:
        return jsonify({'error': 'Arquivo não encontrado'}), 404

@uploads_bp.route('/admin/vehicles/<int:vehicle_id>/images', methods=['GET'])
@require_admin()
def get_vehicle_images(vehicle_id):
    """Lista imagens de um veículo"""
    try:
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({'error': 'Veículo não encontrado'}), 404
        
        images = VehicleImage.query.filter_by(vehicle_id=vehicle_id).order_by(VehicleImage.image_order).all()
        
        return jsonify({
            'images': [image.to_dict() for image in images]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@uploads_bp.route('/admin/vehicles/<int:vehicle_id>/images/reorder', methods=['PUT'])
@require_admin()
def reorder_vehicle_images(vehicle_id):
    """Reordena imagens de um veículo"""
    try:
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({'error': 'Veículo não encontrado'}), 404
        
        data = request.get_json()
        image_ids = data.get('image_ids', [])
        
        if not isinstance(image_ids, list):
            return jsonify({'error': 'Lista de IDs de imagens inválida'}), 400
        
        # Atualizar ordem das imagens
        for index, image_id in enumerate(image_ids):
            image = VehicleImage.query.filter_by(id=image_id, vehicle_id=vehicle_id).first()
            if image:
                image.image_order = index
        
        # Atualizar lista de URLs no veículo
        images = VehicleImage.query.filter_by(vehicle_id=vehicle_id).order_by(VehicleImage.image_order).all()
        image_urls = [f'/api/uploads/{img.filename}' for img in images]
        vehicle.set_imagens(image_urls)
        
        db.session.commit()
        
        return jsonify({'message': 'Ordem das imagens atualizada com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500


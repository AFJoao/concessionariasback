from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(100), nullable=False)
    modelo = db.Column(db.String(100), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    preco = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.Text)
    combustivel = db.Column(db.String(50))
    cambio = db.Column(db.String(50))
    cor = db.Column(db.String(50))
    quilometragem = db.Column(db.Integer, default=0)
    categoria = db.Column(db.String(50))
    imagens = db.Column(db.Text)  # JSON string com array de URLs
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'marca': self.marca,
            'modelo': self.modelo,
            'ano': self.ano,
            'preco': self.preco,
            'descricao': self.descricao,
            'combustivel': self.combustivel,
            'cambio': self.cambio,
            'cor': self.cor,
            'quilometragem': self.quilometragem,
            'categoria': self.categoria,
            'imagens': json.loads(self.imagens) if self.imagens else [],
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def set_imagens(self, imagens_list):
        """Define as imagens como JSON string"""
        self.imagens = json.dumps(imagens_list) if imagens_list else None
    
    def get_imagens(self):
        """Retorna as imagens como lista"""
        return json.loads(self.imagens) if self.imagens else []

class VehicleImage(db.Model):
    __tablename__ = 'vehicle_images'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    image_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    vehicle = db.relationship('Vehicle', backref=db.backref('vehicle_images', lazy=True, cascade='all, delete-orphan'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'image_order': self.image_order,
            'url': f'/api/uploads/{self.filename}',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


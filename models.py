"""
Modelos do banco de dados (SQLAlchemy).
Cada classe vira uma tabela no SQLite.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Mesa(db.Model):
    """Mesa física do restaurante."""
    __tablename__ = "mesas"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)
    capacidade = db.Column(db.Integer, nullable=False)
    # Status possíveis: livre, ocupada, reservada, limpeza
    status = db.Column(db.String(20), nullable=False, default="livre")
    cliente = db.Column(db.String(120), nullable=True)
    ocupada_em = db.Column(db.DateTime, nullable=True)

    def tempo_ocupacao_min(self):
        """Retorna em minutos quanto tempo a mesa está ocupada."""
        if not self.ocupada_em:
            return 0
        delta = datetime.utcnow() - self.ocupada_em
        return int(delta.total_seconds() // 60)

    def to_dict(self):
        return {
            "id": self.id,
            "numero": self.numero,
            "capacidade": self.capacidade,
            "status": self.status,
            "cliente": self.cliente,
            "ocupada_em": self.ocupada_em.isoformat() if self.ocupada_em else None,
            "tempo_min": self.tempo_ocupacao_min(),
        }


class FilaEspera(db.Model):
    """Cliente aguardando mesa."""
    __tablename__ = "fila"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    pessoas = db.Column(db.Integer, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def tempo_espera_min(self):
        delta = datetime.utcnow() - self.criado_em
        return int(delta.total_seconds() // 60)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "pessoas": self.pessoas,
            "criado_em": self.criado_em.isoformat(),
            "espera_min": self.tempo_espera_min(),
        }

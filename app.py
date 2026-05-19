"""
MesaFlow - Sistema de Gerenciamento e Revezamento de Mesas
-----------------------------------------------------------
Aplicação Flask simples, organizada em rotas REST + páginas HTML.
Banco: SQLite (arquivo instance/mesaflow.db criado automaticamente).

Estrutura das rotas:
  /                      -> Dashboard (visão geral das mesas + fila)
  /mesas                 -> Gestão de mesas (cadastrar, status, revezamento)
  /fila                  -> Gestão da fila de espera
  /api/mesas             -> GET (listar) / POST (criar)
  /api/mesas/<id>/status -> PATCH (mudar status: livre/ocupada/reservada/limpeza)
  /api/mesas/<id>/mover  -> POST (revezar clientes para outra mesa)
  /api/mesas/<id>        -> DELETE (remover mesa)
  /api/fila              -> GET (listar) / POST (adicionar cliente)
  /api/fila/proximo      -> POST (chamar próximo - aloca em mesa livre se houver)
  /api/fila/<id>         -> DELETE (remover da fila)

Para executar localmente:
  1) python -m venv .venv && source .venv/bin/activate   (Linux/Mac)
     python -m venv .venv && .venv\\Scripts\\activate     (Windows)
  2) pip install -r requirements.txt
  3) python app.py
  4) Abra http://127.0.0.1:5000
"""

from datetime import datetime
from flask import Flask, render_template, request, jsonify
from models import db, Mesa, FilaEspera

# ---------------------------------------------------------------------------
# Configuração da aplicação Flask
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mesaflow.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


# ---------------------------------------------------------------------------
# Inicialização do banco com dados de exemplo (apenas na primeira execução)
# ---------------------------------------------------------------------------
def seed():
    """Cria algumas mesas de exemplo se o banco estiver vazio."""
    if Mesa.query.count() == 0:
        exemplos = [
            Mesa(numero=1, capacidade=2, status="livre"),
            Mesa(numero=2, capacidade=4, status="livre"),
            Mesa(numero=3, capacidade=4, status="ocupada",
                 cliente="João", ocupada_em=datetime.utcnow()),
            Mesa(numero=4, capacidade=6, status="reservada", cliente="Família Silva"),
            Mesa(numero=5, capacidade=2, status="limpeza"),
        ]
        db.session.add_all(exemplos)
        db.session.commit()


# ---------------------------------------------------------------------------
# Páginas (renderizam HTML usando Jinja2)
# ---------------------------------------------------------------------------
@app.route("/")
def dashboard():
    return render_template("dashboard.html", active="dashboard")


@app.route("/mesas")
def pagina_mesas():
    return render_template("mesas.html", active="mesas")


@app.route("/fila")
def pagina_fila():
    return render_template("fila.html", active="fila")


# ---------------------------------------------------------------------------
# API JSON - Mesas
# ---------------------------------------------------------------------------
@app.get("/api/mesas")
def listar_mesas():
    mesas = Mesa.query.order_by(Mesa.numero).all()
    return jsonify([m.to_dict() for m in mesas])


@app.post("/api/mesas")
def criar_mesa():
    data = request.get_json() or {}
    numero = data.get("numero")
    capacidade = data.get("capacidade")

    # Validações simples
    if not numero or not capacidade:
        return jsonify({"erro": "numero e capacidade são obrigatórios"}), 400
    if Mesa.query.filter_by(numero=numero).first():
        return jsonify({"erro": "Já existe mesa com esse número"}), 400

    mesa = Mesa(numero=int(numero), capacidade=int(capacidade), status="livre")
    db.session.add(mesa)
    db.session.commit()
    return jsonify(mesa.to_dict()), 201


@app.patch("/api/mesas/<int:mesa_id>/status")
def mudar_status(mesa_id):
    """Altera o status de uma mesa.
    Status válidos: livre | ocupada | reservada | limpeza
    Quando passa para 'ocupada', registra o horário de início.
    """
    mesa = Mesa.query.get_or_404(mesa_id)
    data = request.get_json() or {}
    novo_status = data.get("status")
    cliente = data.get("cliente")

    if novo_status not in {"livre", "ocupada", "reservada", "limpeza"}:
        return jsonify({"erro": "status inválido"}), 400

    mesa.status = novo_status
    if novo_status == "ocupada":
        mesa.cliente = cliente or mesa.cliente or "Cliente"
        mesa.ocupada_em = datetime.utcnow()
    elif novo_status == "livre":
        # Liberar mesa: limpa cliente e tempo
        mesa.cliente = None
        mesa.ocupada_em = None
    elif novo_status == "reservada":
        mesa.cliente = cliente or mesa.cliente
        mesa.ocupada_em = None
    elif novo_status == "limpeza":
        mesa.ocupada_em = None

    db.session.commit()
    return jsonify(mesa.to_dict())


@app.post("/api/mesas/<int:mesa_id>/mover")
def mover_clientes(mesa_id):
    """Revezamento: move o cliente de uma mesa para outra livre."""
    origem = Mesa.query.get_or_404(mesa_id)
    data = request.get_json() or {}
    destino_id = data.get("destino_id")
    destino = Mesa.query.get_or_404(destino_id)

    if origem.status != "ocupada":
        return jsonify({"erro": "Mesa de origem não está ocupada"}), 400
    if destino.status != "livre":
        return jsonify({"erro": "Mesa de destino não está livre"}), 400

    # Transferir dados
    destino.status = "ocupada"
    destino.cliente = origem.cliente
    destino.ocupada_em = origem.ocupada_em  # mantém tempo total

    # A mesa de origem vai para limpeza (boa prática operacional)
    origem.status = "limpeza"
    origem.cliente = None
    origem.ocupada_em = None

    db.session.commit()
    return jsonify({"origem": origem.to_dict(), "destino": destino.to_dict()})


@app.delete("/api/mesas/<int:mesa_id>")
def remover_mesa(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    db.session.delete(mesa)
    db.session.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# API JSON - Fila de espera
# ---------------------------------------------------------------------------
@app.get("/api/fila")
def listar_fila():
    fila = FilaEspera.query.order_by(FilaEspera.criado_em).all()
    return jsonify([c.to_dict() for c in fila])


@app.post("/api/fila")
def adicionar_fila():
    data = request.get_json() or {}
    nome = (data.get("nome") or "").strip()
    pessoas = data.get("pessoas")

    if not nome or not pessoas:
        return jsonify({"erro": "nome e pessoas são obrigatórios"}), 400

    cliente = FilaEspera(nome=nome, pessoas=int(pessoas))
    db.session.add(cliente)
    db.session.commit()
    return jsonify(cliente.to_dict()), 201


@app.post("/api/fila/proximo")
def chamar_proximo():
    """Chama o próximo cliente da fila.
    Se houver uma mesa livre com capacidade suficiente, aloca automaticamente.
    """
    proximo = FilaEspera.query.order_by(FilaEspera.criado_em).first()
    if not proximo:
        return jsonify({"erro": "Fila vazia"}), 404

    # Sugestão automática: menor mesa livre que comporte o grupo
    mesa_sugerida = (
        Mesa.query.filter(Mesa.status == "livre",
                          Mesa.capacidade >= proximo.pessoas)
        .order_by(Mesa.capacidade)
        .first()
    )

    resposta = {"cliente": proximo.to_dict(), "mesa": None}
    if mesa_sugerida:
        mesa_sugerida.status = "ocupada"
        mesa_sugerida.cliente = proximo.nome
        mesa_sugerida.ocupada_em = datetime.utcnow()
        db.session.delete(proximo)
        resposta["mesa"] = mesa_sugerida.to_dict()

    db.session.commit()
    return jsonify(resposta)


@app.delete("/api/fila/<int:cliente_id>")
def remover_fila(cliente_id):
    cliente = FilaEspera.query.get_or_404(cliente_id)
    db.session.delete(cliente)
    db.session.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Boot
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed()
    app.run(debug=True)

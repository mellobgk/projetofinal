# MesaFlow — Sistema de Gerenciamento e Revezamento de Mesas

Projeto acadêmico (ADS) em **Python + Flask + SQLite** com painel web dark, focado em bares e restaurantes.

## Funcionalidades

- **Gestão de mesas**: cadastro, número, capacidade e status (livre / ocupada / reservada / em limpeza).
- **Revezamento**: move clientes de uma mesa para outra livre; a mesa de origem vai para limpeza.
- **Tempo de permanência**: calculado automaticamente a partir do horário de ocupação.
- **Fila de espera**: cadastra clientes, ordena por chegada, mostra tempo de espera.
- **Chamar próximo**: aloca automaticamente o próximo da fila em uma mesa livre compatível (menor mesa que comporte o grupo).
- **Dashboard**: contadores em tempo real + grade visual de todas as mesas (atualiza a cada 5s).

## Estrutura de pastas

```
mesaflow/
├── app.py              # Aplicação Flask: rotas de páginas + API JSON
├── models.py           # Modelos SQLAlchemy (Mesa, FilaEspera)
├── requirements.txt    # Dependências Python
├── instance/
│   └── mesaflow.db     # Banco SQLite (criado automaticamente)
├── templates/          # Templates Jinja2 (HTML)
│   ├── base.html       # Layout com sidebar
│   ├── dashboard.html  # Página inicial / visão geral
│   ├── mesas.html      # CRUD de mesas + ações
│   └── fila.html       # Gerenciamento da fila
└── static/
    ├── css/style.css   # Tema dark "Slate & Steel"
    └── js/app.js       # Helpers JS compartilhados (renderização de cards e ações)
```

## Função de cada arquivo

| Arquivo | Função |
|--------|--------|
| `app.py` | Cria a aplicação Flask, define rotas (`/`, `/mesas`, `/fila`) e a API REST (`/api/...`). Lê/escreve no banco via SQLAlchemy. |
| `models.py` | Define as tabelas `mesas` e `fila` com seus campos e métodos auxiliares (`tempo_ocupacao_min`, `to_dict`). |
| `templates/base.html` | HTML base com sidebar de navegação; demais páginas estendem dele. |
| `templates/dashboard.html` | Mostra estatísticas e a grade de mesas; faz polling a cada 5s. |
| `templates/mesas.html` | Formulário de cadastro e cards com botões de ação (ocupar, reservar, revezar, limpeza, liberar, excluir). |
| `templates/fila.html` | Formulário para entrar na fila e tabela com clientes aguardando + botão "Chamar próximo". |
| `static/css/style.css` | Estilos dark (`Slate & Steel`), cores por status, layout responsivo (tablet e desktop). |
| `static/js/app.js` | Funções JS reutilizáveis: `renderCard`, ações `ocupar/reservar/mover/remover/status`. |

## Lógica utilizada

- **Status das mesas** são strings simples (`livre`, `ocupada`, `reservada`, `limpeza`). Ao mudar para `ocupada`, gravamos `ocupada_em = utcnow()` para calcular o tempo de permanência sob demanda (`tempo_ocupacao_min`).
- **Revezamento** transfere `cliente` e `ocupada_em` da mesa de origem para a destino (preservando o tempo total) e marca a origem como `limpeza`.
- **Chamar próximo da fila** ordena por `criado_em` e procura a **menor mesa livre que comporta o grupo** (`capacidade >= pessoas`), evitando desperdiçar mesas grandes.
- **Atualização dinâmica**: as páginas fazem `fetch` a cada 5s (polling simples — sem WebSocket, mantendo o código didático).

## Fluxo do sistema

1. Cliente chega → recepcionista adiciona na **Fila** (`/fila`) com nome e nº de pessoas.
2. Quando uma mesa fica livre, clica em **Chamar próximo** → sistema aloca automaticamente.
3. Funcionário pode mudar status, **revezar** clientes para outra mesa, ou **liberar** ao final.
4. Mesa liberada vai para **limpeza** → depois marcada como **livre** novamente.
5. **Dashboard** mostra a foto do salão em tempo real.

## Como executar localmente

```bash
# 1. Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate           # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Rodar
python app.py
```

Abra **http://127.0.0.1:5000** no navegador. Na primeira execução o banco SQLite é criado com 5 mesas de exemplo.

## Próximos passos sugeridos (para evoluir o trabalho)

- Autenticação de funcionários (Flask-Login).
- WebSocket (Flask-SocketIO) para atualização em tempo real sem polling.
- Histórico de ocupação e relatórios (tempo médio por mesa, taxa de giro).
- Comanda / pedidos integrados ao status da mesa.
- Migração para PostgreSQL em produção.
# projetofinal

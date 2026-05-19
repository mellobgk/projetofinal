/* Helpers compartilhados entre as páginas */
const MesaFlow = {
  /**
   * Renderiza o card visual de uma mesa.
   * @param {object} m - mesa vinda de /api/mesas
   * @param {boolean} comAcoes - se true, mostra botões de ação (gestão)
   */
  renderCard(m, comAcoes = false) {
    const info = (() => {
      if (m.status === 'ocupada')   return `${m.cliente || '—'} • ${m.tempo_min} min`;
      if (m.status === 'reservada') return `Reservada: ${m.cliente || '—'}`;
      if (m.status === 'limpeza')   return 'Aguardando higienização';
      return 'Disponível';
    })();

    const acoes = comAcoes ? `
      <div class="actions">
        ${m.status !== 'livre'    ? `<button class="btn" onclick="MesaFlow.status(${m.id},'livre')">Liberar</button>` : ''}
        ${m.status === 'livre'    ? `<button class="btn" onclick="MesaFlow.ocupar(${m.id})">Ocupar</button>` : ''}
        ${m.status === 'livre'    ? `<button class="btn" onclick="MesaFlow.reservar(${m.id})">Reservar</button>` : ''}
        ${m.status === 'ocupada'  ? `<button class="btn" onclick="MesaFlow.mover(${m.id})">Revezar</button>` : ''}
        ${m.status !== 'limpeza' && m.status !== 'livre' ? `<button class="btn" onclick="MesaFlow.status(${m.id},'limpeza')">Limpeza</button>` : ''}
        <button class="btn ghost" onclick="MesaFlow.remover(${m.id})">Excluir</button>
      </div>` : '';

    return `
      <article class="mesa-card ${m.status}">
        <div class="top">
          <h3>Mesa ${m.numero}</h3>
          <span class="badge ${m.status}">${m.status}</span>
        </div>
        <div class="cap">Capacidade: ${m.capacidade} pessoas</div>
        <div class="info">${info}</div>
        ${acoes}
      </article>`;
  },

  async status(id, novo, cliente) {
    await fetch(`/api/mesas/${id}/status`, {
      method: 'PATCH',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({status: novo, cliente})
    });
    if (typeof refresh === 'function') refresh();
  },

  ocupar(id) {
    const nome = prompt('Nome do cliente:');
    if (nome === null) return;
    this.status(id, 'ocupada', nome || 'Cliente');
  },

  reservar(id) {
    const nome = prompt('Nome da reserva:');
    if (nome === null) return;
    this.status(id, 'reservada', nome || 'Reserva');
  },

  async mover(id) {
    const livres = (window._mesas || []).filter(x => x.status === 'livre');
    if (!livres.length) return alert('Não há mesas livres para revezamento.');
    const opcoes = livres.map(x => `${x.numero} (cap ${x.capacidade})`).join(', ');
    const num = prompt(`Mover para qual mesa? Livres: ${opcoes}\nDigite o NÚMERO da mesa:`);
    const destino = livres.find(x => String(x.numero) === String(num));
    if (!destino) return alert('Mesa inválida.');
    const r = await fetch(`/api/mesas/${id}/mover`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({destino_id: destino.id})
    });
    const data = await r.json();
    if (!r.ok) return alert(data.erro || 'Erro');
    if (typeof refresh === 'function') refresh();
  },

  async remover(id) {
    if (!confirm('Excluir esta mesa?')) return;
    await fetch('/api/mesas/' + id, {method: 'DELETE'});
    if (typeof refresh === 'function') refresh();
  },
};

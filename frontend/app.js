// ATENÇÃO: Como você está no Codespaces, coloque a URL exata do seu backend aqui
const apiUrl = "https://ubiquitous-invention-7v76p7v44rwhx6px-8000.app.github.dev"; 

async function cadastrarEmpresa() {
    const nome = document.getElementById('nome_empresa').value;
    const host = document.getElementById('smtp_host').value;
    const user = document.getElementById('smtp_user').value;
    const pass = document.getElementById('smtp_password').value;
    const msgEl = document.getElementById('msg-empresa');
    

    msgEl.innerText = "Salvando...";
    msgEl.className = "text-sm font-medium mt-2 text-center text-slate-500";

    try {
        const response = await fetch(`${apiUrl}/empresas/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome_fantasia: nome, smtp_host: host, smtp_user: user, smtp_password: pass })
        });

        const data = await response.json();
        if(response.ok) {
            msgEl.innerText = `Sucesso! O ID da empresa é: ${data.id}`;
            msgEl.className = "text-sm font-medium mt-2 text-center text-emerald-600";
            document.getElementById('empresa_id').value = data.id; // Já preenche o campo do lado!
        } else {
            msgEl.innerText = "Erro ao criar empresa.";
            msgEl.className = "text-sm font-medium mt-2 text-center text-red-600";
        }
    } catch (error) {
        msgEl.innerText = "Erro de conexão com a API.";
        msgEl.className = "text-sm font-medium mt-2 text-center text-red-600";
    }
}

async function importarCSV() {
    const empresaId = document.getElementById('empresa_id').value;
    const fileInput = document.getElementById('arquivo_csv');
    const msgEl = document.getElementById('msg-csv');

    if (!empresaId || fileInput.files.length === 0) {
        msgEl.innerText = "Preencha o ID e selecione um arquivo!";
        msgEl.className = "text-sm font-medium mt-2 text-center text-red-600";
        return;
    }

    msgEl.innerText = "Enviando arquivo...";
    msgEl.className = "text-sm font-medium mt-2 text-center text-slate-500";

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const response = await fetch(`${apiUrl}/clientes/importar/${empresaId}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if(response.ok) {
            msgEl.innerText = data.mensagem;
            msgEl.className = "text-sm font-medium mt-2 text-center text-emerald-600";
        } else {
            msgEl.innerText = `Erro: ${data.detail}`;
            msgEl.className = "text-sm font-medium mt-2 text-center text-red-600";
        }
    } catch (error) {
        msgEl.innerText = "Erro ao enviar o arquivo para a API.";
        msgEl.className = "text-sm font-medium mt-2 text-center text-red-600";
    }
}

async function criarPesquisa() {
    // Pega o ID da empresa que já está preenchido no Card 2 para facilitar
    const empresaId = document.getElementById('empresa_id').value || document.getElementById('pesquisa_empresa_id').value;
    const titulo = document.getElementById('titulo_pesquisa').value;
    const msgEl = document.getElementById('msg-pesquisa');
    const linkContainer = document.getElementById('link-container');

    if (!empresaId || !titulo) {
        msgEl.innerText = "Preencha o ID da empresa e o Título!";
        msgEl.className = "text-sm font-medium mt-2 text-center text-red-600";
        return;
    }

    msgEl.innerText = "Criando...";
    msgEl.className = "text-sm font-medium mt-2 text-center text-slate-500";

    try {
        const response = await fetch(`${apiUrl}/pesquisas/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ empresa_id: parseInt(empresaId), titulo: titulo })
        });

        const data = await response.json();
        if(response.ok) {
            msgEl.innerText = "Pesquisa criada com sucesso!";
            msgEl.className = "text-sm font-medium mt-2 text-center text-emerald-600";
            
            // Gera o link simulado que o cliente vai receber
            const linkMoc = `http://localhost:5500/votar.html?pesquisa=${data.id}&empresa=${data.empresa_id}`;
            linkContainer.innerHTML = `<strong>Link gerado para enviar:</strong> <br> <a href="#" class="text-blue-500 underline">${linkMoc}</a>`;
            linkContainer.classList.remove('hidden');
        } else {
            msgEl.innerText = "Erro ao criar pesquisa.";
            msgEl.className = "text-sm font-medium mt-2 text-center text-red-600";
        }
    } catch (error) {
        msgEl.innerText = "Erro de conexão com a API.";
        msgEl.className = "text-sm font-medium mt-2 text-center text-red-600";
    }
}

async function verEstatisticas() {
    // Pega o ID da pesquisa (tenta pegar do Card 3 se já estiver preenchido)
    const pesquisaId = document.getElementById('resultado_pesquisa_id').value || document.getElementById('pesquisa_empresa_id').value || 1;
    const msgEl = document.getElementById('msg-estatisticas');

    msgEl.innerText = "Buscando dados...";
    msgEl.className = "text-sm font-medium mt-2 text-center text-slate-500";

    try {
        const response = await fetch(`${apiUrl}/estatisticas/${pesquisaId}`);
        const data = await response.json();

        if(response.ok) {
            msgEl.innerText = ""; // Limpa a mensagem
            // Atualiza os números grandes no painel
            document.getElementById('dash-media').innerText = data.media_estrelas;
            document.getElementById('dash-votos').innerText = data.total_votos;
        } else {
            msgEl.innerText = "Pesquisa não encontrada.";
            msgEl.className = "text-sm font-medium mt-2 text-center text-red-600";
        }
    } catch (error) {
        msgEl.innerText = "Erro ao buscar estatísticas.";
        msgEl.className = "text-sm font-medium mt-2 text-center text-red-600";
    }
}

async function dispararPesquisa() {
    const pesquisaId = document.getElementById('pesquisa_empresa_id').value || 1;
    const msgEl = document.getElementById('msg-pesquisa');

    msgEl.innerText = "Preparando disparos...";
    const urlFront = window.location.origin + "/frontend"; // Pega a URL do seu GitHub

    try {
        const response = await fetch(`${apiUrl}/pesquisas/${pesquisaId}/disparar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url_frontend: urlFront })
        });
        const data = await response.json();
        msgEl.innerText = data.mensagem;
        msgEl.className = "text-sm font-medium mt-2 text-center text-emerald-600";
    } catch (error) {
        msgEl.innerText = "Erro ao disparar e-mails.";
        msgEl.className = "text-sm font-medium mt-2 text-center text-red-600";
    }
}
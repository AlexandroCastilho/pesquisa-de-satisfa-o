// CONFIGURAÇÃO: URL do Backend no Codespaces
const apiUrl = "https://ubiquitous-invention-7v76p7v44rwhx6px-8000.app.github.dev"; 

// 1. PROTEÇÃO DE ACESSO: Verifica se o usuário está logado ao carregar a página
function verificarAcesso() {
    const email = localStorage.getItem('user_email');
    // Se não estiver logado e não estiver nas páginas de login/registro, expulsa
    if (!email && !window.location.pathname.includes('login.html') && !window.location.pathname.includes('registrar.html')) {
        window.location.href = 'login.html';
    }
}
verificarAcesso();

// 2. CADASTRAR EMPRESA (Vinculando ao seu e-mail de login)
async function cadastrarEmpresa() {
    // Buscamos o email direto da memória do navegador no momento do clique
    const usuarioEmailLogado = localStorage.getItem('user_email');
    
    const nome = document.getElementById('nome_empresa').value;
    const host = document.getElementById('smtp_host').value;
    const user = document.getElementById('smtp_user').value;
    const pass = document.getElementById('smtp_password').value;
    const msgEl = document.getElementById('msg-empresa');

    if (!usuarioEmailLogado) {
        msgEl.innerText = "Erro: Usuário não logado! Refaça o login.";
        msgEl.className = "text-sm font-medium mt-2 text-center text-red-600";
        return;
    }

    msgEl.innerText = "Salvando...";
    msgEl.className = "text-sm font-medium mt-2 text-center text-slate-500";

    try {
        const response = await fetch(`${apiUrl}/empresas/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                nome_fantasia: nome, 
                smtp_host: host, 
                smtp_user: user, 
                smtp_password: pass,
                usuario_email: usuarioEmailLogado // Enviando o email como ID do dono
            })
        });

        const data = await response.json();
        if(response.ok) {
            msgEl.innerText = `Sucesso! Empresa vinculada a ${usuarioEmailLogado}. ID: ${data.id}`;
            msgEl.className = "text-sm font-medium mt-2 text-center text-emerald-600";
            document.getElementById('empresa_id').value = data.id; 
        } else {
            msgEl.innerText = "Erro ao criar empresa. Verifique os campos.";
            msgEl.className = "text-sm font-medium mt-2 text-center text-red-600";
        }
    } catch (error) {
        msgEl.innerText = "Erro de conexão com o servidor.";
        msgEl.className = "text-sm font-medium mt-2 text-center text-red-600";
    }
}

// 3. IMPORTAR CLIENTES (CSV)
async function importarCSV() {
    const empresaId = document.getElementById('empresa_id').value;
    const fileInput = document.getElementById('arquivo_csv');
    const msgEl = document.getElementById('msg-csv');

    if (!empresaId || fileInput.files.length === 0) {
        msgEl.innerText = "Preencha o ID da Empresa e selecione o arquivo!";
        msgEl.className = "text-sm font-medium mt-2 text-red-600";
        return;
    }

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
            msgEl.className = "text-sm font-medium mt-2 text-emerald-600";
        } else {
            msgEl.innerText = "Erro na importação.";
        }
    } catch (error) {
        msgEl.innerText = "Erro de conexão.";
    }
}

// 4. CRIAR PESQUISA
async function criarPesquisa() {
    const empresaId = document.getElementById('empresa_id').value;
    const titulo = document.getElementById('titulo_pesquisa').value;
    const msgEl = document.getElementById('msg-pesquisa');

    if (!empresaId || !titulo) {
        msgEl.innerText = "Preencha o ID da empresa e o título!";
        return;
    }

    try {
        const response = await fetch(`${apiUrl}/pesquisas/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ empresa_id: parseInt(empresaId), titulo: titulo })
        });

        const data = await response.json();
        if(response.ok) {
            msgEl.innerText = "Pesquisa criada com sucesso!";
            msgEl.className =
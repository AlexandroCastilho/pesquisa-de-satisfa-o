const apiUrl = "https://ubiquitous-invention-7v76p7v44rwhx6px-8000.app.github.dev";

// Verifica se está logado
const userEmail = localStorage.getItem('user_email');
if (!userEmail && !window.location.pathname.includes('login.html') && !window.location.pathname.includes('registrar.html')) {
    window.location.href = 'login.html';
}

async function cadastrarEmpresa() {
    const msgEl = document.getElementById('msg-empresa');
    const dados = {
        nome_fantasia: document.getElementById('nome_empresa').value,
        smtp_host: document.getElementById('smtp_host').value,
        smtp_user: document.getElementById('smtp_user').value,
        smtp_password: document.getElementById('smtp_password').value,
        usuario_email: userEmail
    };

    try {
        const response = await fetch(`${apiUrl}/empresas/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });

        if (response.ok) {
            const data = await response.json();
            msgEl.innerText = "Empresa vinculada com sucesso!";
            msgEl.className = "text-emerald-600 mt-2 text-center font-bold";
            document.getElementById('empresa_id').value = data.id;
        } else {
            msgEl.innerText = "Erro ao salvar. Verifique o schemas.py.";
            msgEl.className = "text-red-600 mt-2 text-center";
        }
    } catch (err) {
        msgEl.innerText = "Erro de conexão.";
    }
}

async function importarCSV() {
    const empresaId = document.getElementById('empresa_id').value;
    const fileInput = document.getElementById('arquivo_csv');
    const msgEl = document.getElementById('msg-csv');

    if (!fileInput.files[0]) return alert("Selecione um arquivo CSV!");

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const response = await fetch(`${apiUrl}/clientes/importar/${empresaId}`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        msgEl.innerText = data.mensagem;
        msgEl.className = "text-emerald-600 mt-2 text-center font-bold";
    } catch (err) {
        msgEl.innerText = "Erro no upload.";
    }
}

function logout() {
    localStorage.clear();
    window.location.href = 'login.html';
}
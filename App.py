import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
import json
import re

# ==========================================
# CONFIGURAÇÃO DA IA (GEMINI)
# ==========================================
# Substitua pela sua chave de API do Google Gemini
GEMINI_API_KEY 
modelo = genai.GenerativeModel('gemini-2.5-flash')
GEMINI_API_KEY = st.secrets["AQ.Ab8RN6LfH-7T-3GBzGUJFtgIuO7BIMPd9p3i48b2slBdQ41CkQ"]
# ==========================================
# FUNÇÕES DE EXTRAÇÃO DE TEXTO
# ==========================================
def extrair_texto_pdf(arquivo):
    leitor = PyPDF2.PdfReader(arquivo)
    texto = ""
    for pagina in leitor.pages:
        texto += pagina.extract_text() + "\n"
    return texto

def extrair_texto_docx(arquivo):
    doc = docx.Document(arquivo)
    texto = "\n".join([paragrafo.text for paragrafo in doc.paragraphs])
    return texto

# ==========================================
# FUNÇÃO PARA GERAR O QUIZ COM IA
# ==========================================
def gerar_quiz_da_ia(texto_base):
    prompt = f"""
    Baseado no texto abaixo, crie um quiz de múltipla escolha com 5 perguntas.
    Retorne APENAS um array JSON válido, sem formatação markdown, com a seguinte estrutura:
    [
      {{
        "pergunta": "Qual é a cor do cavalo branco de Napoleão?",
        "opcoes": ["Preto", "Branco", "Marrom", "Cinza"],
        "resposta_correta": 1
      }}
    ]
    A resposta_correta deve ser o índice (0 a 3) da opção certa.
    
    TEXTO BASE:
    {texto_base[:15000]} # Limitando o tamanho para não estourar o contexto
    """
    
    resposta = modelo.generate_content(prompt)
    texto_resposta = resposta.text
    
    # Limpando a resposta caso a IA retorne com marcação markdown (```json ... ```)
    texto_resposta = re.sub(r'```json\n?', '', texto_resposta)
    texto_resposta = re.sub(r'```\n?', '', texto_resposta)
    
    return json.loads(texto_resposta.strip())

# ==========================================
# TEMPLATE DO JOGO WEB (HTML + CSS + JS)
# ==========================================
def obter_html_jogo(json_perguntas):
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
            body {{ font-family: 'Poppins', sans-serif; }}
            .btn-opcao {{ transition: all 0.2s; }}
            .btn-opcao:hover {{ transform: scale(1.02); }}
            .correto {{ background-color: #22c55e !important; color: white !important; border-color: #22c55e !important; }}
            .errado {{ background-color: #ef4444 !important; color: white !important; border-color: #ef4444 !important; }}
        </style>
    </head>
    <body class="bg-slate-900 text-white flex items-center justify-center min-h-screen p-4">
        <div class="w-full max-w-md bg-slate-800 rounded-2xl shadow-2xl p-6 border border-slate-700">
            
            <!-- Header do Quiz -->
            <div class="flex justify-between items-center mb-6">
                <div class="text-sm font-semibold text-slate-400">Questão <span id="num-questao">1</span>/<span id="total-questoes">5</span></div>
                <div class="text-sm font-semibold text-indigo-400">Pontos: <span id="pontuacao">0</span></div>
            </div>

            <!-- Barra de Progresso -->
            <div class="w-full bg-slate-700 rounded-full h-2.5 mb-6">
                <div id="barra-progresso" class="bg-indigo-500 h-2.5 rounded-full transition-all duration-500" style="width: 0%"></div>
            </div>

            <!-- Tela de Pergunta -->
            <div id="tela-pergunta">
                <h2 id="texto-pergunta" class="text-xl font-bold mb-6 text-center text-slate-100">Carregando...</h2>
                <div id="opcoes-container" class="flex flex-col gap-3">
                    <!-- Botões injetados via JS -->
                </div>
            </div>

            <!-- Tela de Resultado -->
            <div id="tela-resultado" class="hidden text-center">
                <div class="text-6xl mb-4">🏆</div>
                <h2 class="text-2xl font-bold mb-2">Fim de Jogo!</h2>
                <p class="text-slate-300 mb-6">Você fez <span id="pontuacao-final" class="font-bold text-indigo-400 text-xl"></span> pontos.</p>
                <button onclick="location.reload()" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded-xl transition-all">Jogar Novamente</button>
            </div>
        </div>

        <script>
            // Recebendo os dados da IA gerados no Python
            const perguntas = {json.dumps(json_perguntas)};
            
            let indiceAtual = 0;
            let pontos = 0;
            let respondido = false;

            document.getElementById('total-questoes').innerText = perguntas.length;

            function carregarPergunta() {{
                respondido = false;
                const perguntaAtual = perguntas[indiceAtual];
                document.getElementById('texto-pergunta').innerText = perguntaAtual.pergunta;
                document.getElementById('num-questao').innerText = indiceAtual + 1;
                
                // Atualiza barra de progresso
                const progresso = (indiceAtual / perguntas.length) * 100;
                document.getElementById('barra-progresso').style.width = progresso + '%';

                const container = document.getElementById('opcoes-container');
                container.innerHTML = '';

                perguntaAtual.opcoes.forEach((opcao, index) => {{
                    const btn = document.createElement('button');
                    btn.innerText = opcao;
                    btn.className = 'btn-opcao w-full bg-slate-700 border-2 border-slate-600 text-left py-3 px-5 rounded-xl font-semibold text-slate-200 hover:bg-slate-600 hover:border-indigo-400';
                    btn.onclick = () => verificarResposta(index, btn);
                    container.appendChild(btn);
                }});
            }}

            function verificarResposta(indiceSelecionado, botaoClicado) {{
                if (respondido) return;
                respondido = true;

                const perguntaAtual = perguntas[indiceAtual];
                const botoes = document.querySelectorAll('.btn-opcao');

                if (indiceSelecionado === perguntaAtual.resposta_correta) {{
                    botaoClicado.classList.add('correto');
                    pontos += 100;
                    document.getElementById('pontuacao').innerText = pontos;
                }} else {{
                    botaoClicado.classList.add('errado');
                    botoes[perguntaAtual.resposta_correta].classList.add('correto');
                }}

                setTimeout(() => {{
                    indiceAtual++;
                    if (indiceAtual < perguntas.length) {{
                        carregarPergunta();
                    }} else {{
                        mostrarResultado();
                    }}
                }}, 1500);
            }}

            function mostrarResultado() {{
                document.getElementById('tela-pergunta').classList.add('hidden');
                document.getElementById('barra-progresso').style.width = '100%';
                document.getElementById('tela-resultado').classList.remove('hidden');
                document.getElementById('pontuacao-final').innerText = pontos;
            }}

            // Inicia o jogo
            carregarPergunta();
        </script>
    </body>
    </html>
    """
    return html

# ==========================================
# INTERFACE PRINCIPAL DO STREAMLIT
# ==========================================
st.set_page_config(page_title="Gerador de Quiz Gamificado", layout="centered")

st.title("🎲 Transforme Documentos em Jogos")
st.write("Faça upload do seu material de estudo (PDF ou Word) e a IA vai gerar um quiz gamificado na hora!")

arquivo_enviado = st.file_uploader("Envie seu arquivo aqui", type=["pdf", "docx"])

if arquivo_enviado is not None:
    if st.button("✨ Gerar Jogo a partir do Documento", use_container_width=True):
        with st.spinner("A IA está lendo seu documento e criando as perguntas..."):
            try:
                # 1. Extrair Texto
                if arquivo_enviado.name.endswith(".pdf"):
                    texto_extraido = extrair_texto_pdf(arquivo_enviado)
                elif arquivo_enviado.name.endswith(".docx"):
                    texto_extraido = extrair_texto_docx(arquivo_enviado)
                
                # 2. Gerar Perguntas com Gemini
                perguntas_json = gerar_quiz_da_ia(texto_extraido)
                
                # 3. Mostrar o WebApp
                st.success("Jogo gerado com sucesso!")
                
                html_final = obter_html_jogo(perguntas_json)
                st.components.v1.html(html_final, height=650, scrolling=True)
                
         except Exception as e:
                st.error(f"Ocorreu um erro ao processar: {e}")   


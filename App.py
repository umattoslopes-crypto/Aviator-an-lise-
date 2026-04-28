
import streamlit as st
import os

# Configuração da página
st.set_page_config(page_title="Analisador Pro 10k", layout="wide")

# --- 1. FUNÇÕES DE BANCO DE DADOS (ARQUIVO FÍSICO) ---
ARQUIVO_DADOS = "historico_velas.csv"

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r") as f:
            conteudo = f.read().strip()
            if conteudo:
                return [float(v) for v in conteudo.split(",") if v]
    return []

def salvar_dados(lista_velas):
    # Mantém apenas as últimas 10.000 para o arquivo não ficar pesado demais
    lista_velas = lista_velas[-10000:]
    with open(ARQUIVO_DADOS, "w") as f:
        f.write(",".join(map(str, lista_velas)))
    return lista_velas

# Inicializa o banco carregando do arquivo
if 'banco_dados' not in st.session_state:
    st.session_state.banco_dados = carregar_dados()

def formatar_vela(v):
    cor = "#ff4b4b" if v < 2 else "#00ff00"
    return f'<span style="color: {cor}; font-weight: bold;">{v:.2f}x</span>'

# --- 2. INTERFACE ---
st.title("📊 Histórico Permanente (10.000 Velas)")
st.info(f"O banco de dados atual possui: **{len(st.session_state.banco_dados)}** velas guardadas.")

entrada = st.text_area("Cole as novas velas aqui:")

if st.button("📥 Salvar no Histórico Permanente"):
    if entrada:
        try:
            # CORREÇÃO: Lê o número completo (ex: 2.67) e não apenas o decimal
            texto_limpo = entrada.replace(',', '.')
            # Aceita números separados por espaço, vírgula ou quebra de linha
            import re
            novas_velas = [float(v) for v in re.findall(r"[-+]?\d*\.\d+|\d+", texto_limpo)]
            
            # Adiciona ao banco e salva no arquivo físico
            st.session_state.banco_dados.extend(novas_velas)
            st.session_state.banco_dados = salvar_dados(st.session_state.banco_dados)
            
            st.success(f"Adicionadas {len(novas_velas)} velas com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao processar: {e}")

# --- 3. BUSCA DE PADRÃO EM 10.000 VELAS ---
st.markdown("---")
if len(st.session_state.banco_dados) >= 13:
    padrao_atual = st.session_state.banco_dados[-10:]
    encontrou = False
    
    # Varre todo o histórico carregado do arquivo
    for i in range(len(st.session_state.banco_dados) - 13):
        if st.session_state.banco_dados[i : i + 10] == padrao_atual:
            encontrou = True
            v1, v2, v3 = st.session_state.banco_dados[i+10], st.session_state.banco_dados[i+11], st.session_state.banco_dados[i+12]
            
            st.subheader("🎯 PADRÃO ENCONTRADO NO HISTÓRICO")
            cols = st.columns(3)
            for pos, v in enumerate([v1, v2, v3], 0):
                cor = "#ff00ff" if v >= 10 else ("#ffd700" if v >= 5 else ("#00ff00" if v >= 2 else "#ff4b4b"))
                cols[pos].markdown(f'''
                    <div style="background-color: {cor}; padding: 20px; border-radius: 10px; color: black; text-align: center; font-weight: bold; border: 2px solid black;">
                        {v:.2f}x
                    </div>
                ''', unsafe_allow_html=True)

# --- 4. VISUALIZAÇÃO ---
st.markdown("---")
if st.session_state.banco_dados:
    if st.checkbox("Mostrar Histórico (Últimas 100)"):
        h_html = " | ".join([formatar_vela(v) for v in st.session_state.banco_dados[-100:]])
        st.markdown(f'<div style="word-wrap: break-word; font-family: monospace;">{h_html}</div>', unsafe_allow_html=True)

    if st.button("🗑️ Resetar Todo o Arquivo"):
        if os.path.exists(ARQUIVO_DADOS):
            os.remove(ARQUIVO_DADOS)
        st.session_state.banco_dados = []
        st.rerun()

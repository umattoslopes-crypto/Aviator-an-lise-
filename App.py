import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# --- 1. PERSISTÊNCIA (GRAVAÇÃO NO ARQUIVO) ---
DB_FILE = "historico_velas.csv"

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.velas = pd.read_csv(DB_FILE)['velas'].tolist()
    else:
        st.session_state.velas = []

def salvar_dados():
    pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

# Carrega o leitor de imagem
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()

st.title("🤖 Analisador de Velas Pro")

# --- 2. ÁREA DE ENTRADA (PRINT + MANUAL) ---
st.subheader("📥 Inserir Dados")

arquivo_img = st.file_uploader("📸 Suba o Print das Velas", type=['png', 'jpg', 'jpeg'])
input_manual = st.text_area("⌨️ Ou cole as velas manualmente:", placeholder="Ex: 1.50 9.34 2.10...")

# Variável para acumular o que foi lido
texto_final = ""

if arquivo_img:
    img = Image.open(arquivo_img)
    st.image(img, width=200, caption="Imagem carregada")
    with st.spinner("Lendo números do print..."):
        img_np = np.array(img)
        resultado = reader.readtext(img_np, detail=0) # detail=0 traz apenas o texto
        texto_final = " ".join(resultado)
        st.info(f"Texto detectado no print: {texto_final}")

# Se houver algo no manual, ele soma ao que veio do print
if input_manual:
    texto_final += " " + input_manual

# --- 3. BOTÃO ÚNICO PARA SALVAR E FILTRAR REPETIDAS ---
if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    if texto_final.strip():
        # Extrai os números (trata vírgula como ponto)
        novas = [float(v) for v in re.findall(r"\d+\.\d+|\d+", texto_final.replace(',', '.'))]
        
        if novas:
            # LÓGICA DE NÃO DUPLICAR: Compara o início do novo texto com o fim do banco
            ultimas_banco = st.session_state.velas[-10:]
            ponto_corte = 0
            
            # Tenta encontrar onde o print novo "encaixa" no final do antigo
            for i in range(len(novas)):
                # Se o par de velas bater com algum par no final do banco, corta as repetidas
                if novas[i:i+2] in [ultimas_banco[j:j+2] for j in range(len(ultimas_banco)-1)]:
                    ponto_corte = i + 2

            velas_ineditas = novas[ponto_corte:]

            if velas_ineditas:
                st.session_state.velas.extend(velas_ineditas)
                st.session_state.velas = st.session_state.velas[-10000:]
                salvar_dados()
                st.success(f"✅ {len(velas_ineditas)} novas velas salvas com sucesso!")
                st.rerun()
            else:
                st.warning("⚠️ Todas as velas desse print já estão no banco.")
    else:
        st.error("Nenhum dado encontrado para adicionar.")

st.divider()

# --- 4. BUSCA MANUAL ---
st.subheader("🔍 Localizar Sequência")
seq_busca = st.text_input("Digite a sequência (ex: 1.50, 2.00)")
if st.button("🔍 BUSCAR"):
    if seq_busca:
        try:
            padrao = [float(x.strip()) for x in seq_busca.replace(',', ' ').split()]
            n = len(padrao)
            indices = [i+1 for i in range(len(st.session_state.velas)-n+1) if st.session_state.velas[i:i+n] == padrao]
            if indices: st.success(f"Encontrado nas posições: {indices}")
            else: st.error("Não encontrado.")
        except: st.error("Formato inválido.")

st.divider()

# --- 5. VISUALIZAÇÃO COM "X" E CORES (8x EM ROSA) ---
total = len(st.session_state.velas)
st.header(f"📊 Histórico: {total} Velas")

if total > 0:
    # Lista horizontal colorida
    resumo_html = []
    for v in st.session_state.velas[-12:][::-1]:
        cor = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#BBBBBB"
        resumo_html.append(f"<b style='color: {cor}; font-size: 1.2em;'>{v:.2f}x</b>")
    st.markdown(" | ".join(resumo_html), unsafe_allow_html=True)

    # Tabela completa
    with st.expander("👁️ VER TODO O BANCO (ORDEM RECENTE)"):
        df_v = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
        
        def colorir_8x(val):
            return 'color: #FF00FF; font-weight: bold' if val >= 8.0 else 'color: white'
        
        # .format("{:.2f}x") coloca o X em todas as células
        st.dataframe(df_v.style.applymap(colorir_8x).format("{:.2f}x"), use_container_width=True, height=400)
else:
    st.info("O banco de dados está vazio. Adicione velas acima.")

# --- 6. RESET ---
st.divider()
if st.checkbox("Deseja apagar TODO o histórico?"):
    if st.button("🗑️ ZERAR TUDO AGORA"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()
                

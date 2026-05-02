import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# --- 1. PERSISTÊNCIA (GRAVAÇÃO EM ARQUIVO) ---
DB_FILE = "banco_dados_velas.csv"

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.velas = pd.read_csv(DB_FILE)['velas'].tolist()
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

# --- 2. LAYOUT: BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("📥 Entrada de Dados")
    
    # Aba de Prints
    st.subheader("📸 Prints")
    arquivo_img = st.file_uploader("Anexe o print aqui", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
    
    # Aba Manual
    st.subheader("⌨️ Manual")
    input_manual = st.text_area("Cole as velas (até 500):", placeholder="1.50 2.30 10.00...", height=100)
    
    if st.button("📥 ADICIONAR AO BANCO", use_container_width=True):
        texto_extraido = ""
        if arquivo_img:
            img_np = np.array(Image.open(arquivo_img))
            res = reader.readtext(img_np, detail=0)
            texto_extraido = " ".join(res)
        
        if input_manual:
            texto_extraido += " " + input_manual
            
        if texto_extraido:
            # Extrai números e evita horários
            nums = [float(v) for v in re.findall(r"(\d+[\.\d]*)", texto_extraido.replace(',', '.'))]
            novas = [v for v in nums if 1.0 <= v <= 5000.0]
            
            if novas:
                # Sincronização (Anti-duplicação)
                ultimas = st.session_state.velas[-10:]
                ponto = 0
                for i in range(len(novas)):
                    if novas[i:i+2] in [ultimas[j:j+2] for j in range(len(ultimas)-1)]:
                        ponto = i + 2
                
                final = novas[ponto:]
                if final:
                    st.session_state.velas.extend(final)
                    salvar()
                    st.success(f"Adicionadas {len(final)} velas.")
                    st.rerun()

    st.divider()
    if st.checkbox("⚠️ Resetar Banco"):
        if st.button("🗑️ APAGAR TUDO"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.velas = []
            st.rerun()

# --- 3. ÁREA PRINCIPAL: BUSCA DE PADRÃO ---
st.title("🤖 Analisador de Padrões")

st.subheader("🔍 Buscar Sequência (Padrão de 10)")
seq_busca = st.text_input("Insira as velas separadas por espaço ou vírgula", placeholder="Ex: 1.50 2.00 1.10...")

if st.button("🔎 ANALISAR HISTÓRICO", use_container_width=True):
    if seq_busca:
        try:
            padrao = [float(x.strip()) for x in seq_busca.replace(',', ' ').split()]
            n = len(padrao)
            historico = st.session_state.velas
            achou = False
            
            for i in range(len(historico) - n):
                if historico[i : i + n] == padrao:
                    achou = True
                    st.success(f"✅ PADRÃO ENCONTRADO! (Ocorrência na posição {i+1})")
                    
                    # ALERTA: Próximas 15 velas após o padrão
                    proximas = historico[i + n : i + n + 15]
                    if proximas:
                        st.warning("🔥 Antecipação: Próximas 15 velas após este padrão no histórico:")
                        formatadas = [f"<span style='color:{'#FF00FF' if v >= 8.0 else '#00FF00' if v >= 2.0 else '#FFFFFF'}; font-weight:bold;'>{v:.2f}x</span>" for v in proximas]
                        st.markdown(" , ".join(formatadas), unsafe_allow_html=True)
            
            if not achou:
                st.error("❌ Padrão não encontrado no banco de dados.")
        except:
            st.error("Erro no formato das velas digitadas.")

st.divider()

# --- 4. VISUALIZAÇÃO COMPLETA DO BANCO ---
st.subheader(f"📊 Banco de Dados Completo ({len(st.session_state.velas)} velas)")

if st.session_state.velas:
    # Exibe TODAS as velas (ordem da mais recente para a mais antiga)
    df = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
    
    def colorir(val):
        return 'color: #FF00FF; font-weight: bold' if val >= 8.0 else 'color: white'
    
    # Exibição total com cores
    st.dataframe(
        df.style.map(colorir).format("{:.2f}x"), 
        use_container_width=True, 
        height=600 # Altura maior para ver tudo
    )
else:
    st.info("O banco está vazio. Adicione velas pela barra lateral.")


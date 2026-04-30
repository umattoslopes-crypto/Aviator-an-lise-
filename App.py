import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# --- CONFIGURAÇÃO DE DADOS ---
DB_FILE = "historico_velas.csv"

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

st.title("🤖 Analisador de Velas")

# --- ÁREA DE INPUT (SEM EXIBIÇÃO DE IMAGEM) ---
arquivo = st.file_uploader("📥 Envie o Print das Velas", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
manual = st.text_input("⌨️ Entrada Manual (opcional)")

if st.button("🚀 PROCESSAR E ADICIONAR"):
    texto_bruto = ""
    
    if arquivo:
        with st.spinner("Lendo..."):
            img = Image.open(arquivo)
            texto_bruto = " ".join(reader.readtext(np.array(img), detail=0))
    
    if manual:
        texto_bruto += " " + manual

    if texto_bruto:
        # Extração limpa: ignora letras e foca em números 1.00 a 5000.00
        extraidas = [float(v) for v in re.findall(r"(\d+[\.\d]*)", texto_bruto.replace(',', '.'))]
        novas = [v for v in extraidas if 1.0 <= v <= 5000.0]

        if novas:
            # Filtro de duplicidade (Sincronização)
            ultimas = st.session_state.velas[-10:]
            ponto = 0
            for i in range(len(novas)):
                if novas[i:i+2] in [ultimas[j:j+2] for j in range(len(ultimas)-1)]:
                    ponto = i + 2
            
            final = novas[ponto:]
            if final:
                st.session_state.velas.extend(final)
                st.session_state.velas = st.session_state.velas[-10000:]
                salvar()
                st.success(f"✅ {len(final)} velas adicionadas.")
                st.rerun()
            else:
                st.warning("Velas já existem no banco.")

st.divider()

# --- EXIBIÇÃO DO HISTÓRICO (FORMATO: 2.34x , 5.44x) ---
total = len(st.session_state.velas)
st.subheader(f"📊 Histórico ({total} velas)")

if total > 0:
    # Formata a lista como solicitado: 2.34x , 5.44x
    ultimas_15 = st.session_state.velas[-15:][::-1]
    lista_formatada = []
    
    for v in ultimas_15:
        cor = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#BBBBBB"
        lista_formatada.append(f"<span style='color: {cor}; font-weight: bold;'>{v:.2f}x</span>")
    
    # Exibe com a vírgula separando conforme pedido
    st.markdown(" , ".join(lista_formatada), unsafe_allow_html=True)

    with st.expander("👁️ Ver Banco Completo"):
        df = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
        st.dataframe(
            df.style.applymap(lambda x: 'color: #FF00FF' if x >= 8.0 else 'color: white').format("{:.2f}x"),
            use_container_width=True
        )

# --- BUSCA E RESET ---
st.divider()
col1, col2 = st.columns(2)
with col1:
    busca = st.text_input("🔍 Buscar Sequência")
    if st.button("Buscar"):
        p = [float(x.strip()) for x in busca.replace(',', ' ').split()]
        pos = [i+1 for i in range(len(st.session_state.velas)-len(p)+1) if st.session_state.velas[i:i+len(p)] == p]
        if pos: st.success(f"Posições: {pos}")
with col2:
    if st.checkbox("Zerar tudo?"):
        if st.button("🗑️ Reset"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.velas = []
            st.rerun()

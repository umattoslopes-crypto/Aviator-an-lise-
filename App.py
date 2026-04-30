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
        try:
            st.session_state.velas = pd.read_csv(DB_FILE)['velas'].tolist()
        except: st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

st.title("🤖 Analisador de Velas")

# --- ÁREA DE INPUT (LIMPA E DIRETA) ---
arquivo = st.file_uploader("📥 Envie o Print das Velas", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
manual = st.text_input("⌨️ Entrada Manual (opcional)")

if st.button("🚀 PROCESSAR E ADICIONAR", use_container_width=True):
    texto_bruto = ""
    
    if arquivo:
        with st.spinner("Lendo print..."):
            img = Image.open(arquivo)
            texto_bruto = " ".join(reader.readtext(np.array(img), detail=0))
    
    if manual:
        texto_bruto += " " + manual

    if texto_bruto:
        # Filtro inteligente: ignora horários (HH.MM) e pega multiplicadores
        extraidas = []
        # Procura números que não tenham cara de hora (evita o 22.18 do seu print)
        limpeza = re.findall(r"(\d+[\.\d]*)", texto_bruto.replace(',', '.'))
        
        for v in limpeza:
            try:
                num = float(v)
                # Filtro: Geralmente velas não são redondas como horas 22.18
                # E ignoramos valores que o OCR lê errado como 0.0
                if 1.0 <= num <= 5000.0:
                    extraidas.append(num)
            except: continue

        if extraidas:
            # Sincronização para não duplicar velas entre prints
            ultimas = st.session_state.velas[-10:]
            ponto = 0
            for i in range(len(extraidas)):
                if extraidas[i:i+2] in [ultimas[j:j+2] for j in range(len(ultimas)-1)]:
                    ponto = i + 2
            
            final = extraidas[ponto:]
            if final:
                st.session_state.velas.extend(final)
                st.session_state.velas = st.session_state.velas[-10000:]
                salvar()
                st.success(f"✅ {len(final)} novas velas adicionadas.")
                st.rerun()
            else:
                st.warning("Essas velas já estão no banco.")

st.divider()

# --- EXIBIÇÃO DO HISTÓRICO (FORMATO: 2.34x , 5.44x) ---
total = len(st.session_state.velas)
st.subheader(f"📊 Histórico ({total} velas)")

if total > 0:
    # Mostra as últimas 15 velas de trás para frente
    ultimas_15 = st.session_state.velas[-15:][::-1]
    lista_formatada = []
    
    for v in ultimas_15:
        # Rosa para >= 8x, Verde para >= 2x, Cinza para o resto
        cor = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#BBBBBB"
        lista_formatada.append(f"<span style='color: {cor}; font-weight: bold;'>{v:.2f}x</span>")
    
    # Exibe separado por vírgula como você pediu
    st.markdown(" , ".join(lista_formatada), unsafe_allow_html=True)

    with st.expander("👁️ Ver Banco Completo"):
        df = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
        
        # Correção do Erro de Atributo (Troca applymap por map ou style.map)
        def colorir(val):
            return 'color: #FF00FF; font-weight: bold' if val >= 8.0 else 'color: white'
            
        try:
            # Tenta o método novo do Pandas
            st.dataframe(df.style.map(colorir).format("{:.2f}x"), use_container_width=True)
        except:
            # Caso o Streamlit use Pandas antigo
            st.dataframe(df.style.applymap(colorir).format("{:.2f}x"), use_container_width=True)

# --- BUSCA E RESET ---
st.divider()
col1, col2 = st.columns(2)
with col1:
    busca = st.text_input("🔍 Buscar Sequência")
    if st.button("Buscar"):
        try:
            p = [float(x.strip()) for x in busca.replace(',', ' ').split()]
            pos = [i+1 for i in range(len(st.session_state.velas)-len(p)+1) if st.session_state.velas[i:i+len(p)] == p]
            if pos: st.success(f"Encontrado em: {pos}")
            else: st.error("Não encontrado.")
        except: st.error("Use números.")
with col2:
    if st.checkbox("Apagar histórico?"):
        if st.button("🗑️ Reset Total"):
            if os.path.exists(DB_FILE): os.remove(DB_FILE)
            st.session_state.velas = []
            st.rerun()

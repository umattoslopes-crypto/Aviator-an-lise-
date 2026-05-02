import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# --- 1. PERSISTÊNCIA ---
DB_FILE = "banco_dados_fiel.csv"

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
def iniciar_leitor():
    return easyocr.Reader(['en'], gpu=False)

reader = iniciar_leitor()

# --- LAYOUT FIEL (ORDEM EXATA) ---
st.markdown("<h2 style='text-align: center;'>ATE 500 VELAS</h2>", unsafe_allow_html=True)

aba_manual, aba_print = st.tabs(["📥 INSERIR MANUAL", "📸 INSERIR ATRAVÉS PRINT"])

with aba_manual:
    manual_txt = st.text_area("Exemplo: 1.25x 4.10x", placeholder="Digite aqui...", height=100)

with aba_print:
    arquivo_img = st.file_uploader("Arraste o print aqui", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    texto_bruto = ""
    if arquivo_img:
        with st.spinner("Lendo print..."):
            img = Image.open(arquivo_img)
            resultado = reader.readtext(np.array(img), detail=0)
            texto_bruto = " ".join(resultado)
    
    if manual_txt:
        texto_bruto += " " + manual_txt

    if texto_bruto:
        # Extração de números tratando vírgula como ponto
        brutos = re.findall(r"(\d+[\.\d]*)", texto_bruto.replace(',', '.'))
        novas = []
        for v in brutos:
            try:
                num = float(v)
                # --- TRAVAS DE PRECISÃO ---
                # 1. Ignora o horário do celular (22.18) que aparece no seu print
                # 2. Ignora IDs de rodada gigantes (acima de 1000)
                if num == 22.18 or num > 1000.0:
                    continue
                if num >= 1.0:
                    novas.append(num)
            except: continue
        
        if novas:
            # Sincronização para não duplicar velas
            ultimas = st.session_state.velas[-15:]
            corte = 0
            for i in range(len(novas)):
                if novas[i:i+2] in [ultimas[j:j+2] for j in range(len(ultimas)-1)]:
                    corte = i + 2
            
            finais = novas[corte:]
            if finais:
                st.session_state.velas.extend(finais)
                salvar()
                st.success(f"✅ {len(finais)} novas velas adicionadas!")
                st.rerun()

st.divider()

# --- BUSCA DE PADRÃO ---
st.subheader("🔍 BUSCA DE PADRAO")
col_in, col_bt = st.columns([0.85, 0.15])
with col_in:
    padrao_input = st.text_input("Insira 10 velas:", label_visibility="collapsed")
with col_bt:
    if st.button("🔎"):
        if padrao_input:
            try:
                alvo = [float(x.strip()) for x in padrao_input.replace(',', ' ').split()]
                hist = st.session_state.velas
                encontrou = False
                for i in range(len(hist) - len(alvo)):
                    if hist[i : i + len(alvo)] == alvo:
                        encontrou = True
                        st.success(f"🎯 PADRÃO NA POSIÇÃO {i+1}")
                        futuro = hist[i + len(alvo) : i + len(alvo) + 15]
                        if futuro:
                            st.warning("⚠️ PRÓXIMAS 15 VELAS:")
                            res = [f"<b style='color:{'#FF00FF' if v >= 8.0 else '#00FF00' if v >= 2.0 else '#FFFFFF'};'>{v:.2f}x</b>" for v in futuro]
                            st.markdown(" , ".join(res), unsafe_allow_html=True)
                if not encontrou: st.error("Não encontrado.")
            except: st.error("Erro no formato.")

st.divider()

# --- HISTÓRICO DE VELAS ---
st.subheader("📋 HISTORICO DE VELAS")
if st.session_state.velas:
    df = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
    st.dataframe(
        df.style.map(lambda x: 'color: #FF00FF; font-weight: bold' if x >= 8.0 else 'color: white').format("{:.2f}x"),
        use_container_width=True, height=400
    )

st.divider()

# --- ÚLTIMAS 20 VELAS (RODAPÉ LIMPO) ---
st.subheader("📉 ULTIMA 20 VELA ADICIONADA")
if st.session_state.velas:
    ultimas_20 = [v for v in st.session_state.velas[-20:][::-1]]
    html = []
    for v in ultimas_20:
        cor = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#FFFFFF"
        html.append(f"<b style='color:{cor};'>{v:.2f}x</b>")
    
    # Exibe a lista limpa, sem vírgulas sobrando ou espaços vazios
    st.markdown(" , ".join(html), unsafe_allow_html=True)

# Botão de Reset na Sidebar para limpar o erro anterior
if st.sidebar.button("🗑️ LIMPAR BANCO"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.session_state.velas = []
    st.rerun()

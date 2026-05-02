import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# --- CONFIGURAÇÃO DE PERSISTÊNCIA ---
DB_FILE = "banco_velas_final.csv"

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

# --- LAYOUT CONFORME O DESENHO ---

st.markdown("<h2 style='text-align: center;'>ATE 500 VELAS</h2>", unsafe_allow_html=True)

# Moldura de entrada
aba_manual, aba_print = st.tabs(["📥 INSERIR MANUAL", "📸 INSERIR ATRAVÉS PRINT"])

with aba_manual:
    manual_txt = st.text_area("Exemplo: 1.25x 4.10x", placeholder="Cole as velas aqui...", height=100)

with aba_print:
    arquivo = st.file_uploader("Anexe o print aqui", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    texto_bruto = ""
    if arquivo:
        with st.spinner("Lendo print..."):
            img = Image.open(arquivo)
            res = reader.readtext(np.array(img), detail=0)
            texto_bruto = " ".join(res)
    if manual_txt:
        texto_bruto += " " + manual_txt

    if texto_bruto:
        # Extração e Filtro de Desduplicação
        nums = [float(v) for v in re.findall(r"(\d+[\.\d]*)", texto_bruto.replace(',', '.'))]
        novas = [v for v in nums if 1.0 <= v <= 5000.0]
        
        ultimas_banco = st.session_state.velas[-15:]
        ponto_corte = 0
        for i in range(len(novas)):
            if novas[i:i+2] in [ultimas_banco[j:j+2] for j in range(len(ultimas_banco)-1)]:
                ponto_corte = i + 2
        
        velas_finais = novas[ponto_corte:]
        if velas_finais:
            st.session_state.velas.extend(velas_finais)
            salvar()
            st.success(f"{len(velas_finais)} velas adicionadas!")
            st.rerun()

st.divider()

# --- SEÇÃO: BUSCA DE PADRÃO COM ALERTA ---
st.markdown("### BUSCA DE PADRAO")
col_input, col_botao = st.columns([0.85, 0.15])

with col_input:
    seq_alvo = st.text_input("Insira o padrão de 10 velas para analisar", placeholder="1.25, 2.00, 1.10...", label_visibility="collapsed")

with col_botao:
    buscar = st.button("🔎")

if buscar and seq_alvo:
    try:
        padrao = [float(x.strip()) for x in seq_alvo.replace(',', ' ').split()]
        n = len(padrao)
        historico = st.session_state.velas
        encontrou_padrao = False
        
        for i in range(len(historico) - n):
            # Se encontrar a sequência de 10 velas
            if historico[i : i + n] == padrao:
                encontrou_padrao = True
                st.success(f"✅ PADRÃO ENCONTRADO! (Ocorrência na posição {i+1} do histórico)")
                
                # --- ALERTA DAS PRÓXIMAS 15 VELAS ---
                proximas = historico[i + n : i + n + 15]
                if proximas:
                    st.warning("⚠️ ALERTA DE ANTECIPAÇÃO: Próximas 15 velas após este padrão:")
                    fmt = []
                    for v in proximas:
                        # Rosa Choque para >= 8x
                        cor = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#BBBBBB"
                        fmt.append(f"<b style='color:{cor}; font-size:1.2em;'>{v:.2f}x</b>")
                    
                    st.markdown(" , ".join(fmt), unsafe_allow_html=True)
                else:
                    st.info("Padrão encontrado no final do banco, não há velas seguintes para exibir.")
                    
        if not encontrou_padrao:
            st.error("❌ Padrão não localizado no histórico atual.")
    except:
        st.error("Formato de números inválido. Use pontos e vírgulas corretamente.")

st.divider()

# --- SEÇÃO: HISTÓRICO DE VELAS ---
st.markdown("### HISTORICO DE VELAS")
if st.session_state.velas:
    df = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
    
    def colorir_8x(val):
        return 'color: #FF00FF; font-weight: bold' if val >= 8.0 else 'color: white'

    st.dataframe(
        df.style.map(colorir_8x).format("{:.2f}x"), 
        use_container_width=True, 
        height=350
    )

st.divider()

# --- SEÇÃO: ÚLTIMA 10 VELA ADICIONADA ---
st.markdown("### ULTIMA 10 VELA ADICIONADA")
if st.session_state.velas:
    ultimas_10 = st.session_state.velas[-10:][::-1]
    resumo_html = []
    for v in ultimas_10:
        cor = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#BBBBBB"
        resumo_html.append(f"<span style='color:{cor}; font-weight:bold; font-size:1.1em;'>{v:.2f}x</span>")
    
    st.markdown(" , ".join(resumo_html), unsafe_allow_html=True)

# Opção de Reset
if st.sidebar.checkbox("Configurações do Banco"):
    if st.sidebar.button("🗑️ ZERAR TUDO AGORA"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()

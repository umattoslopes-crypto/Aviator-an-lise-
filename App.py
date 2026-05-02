import streamlit as st
import pandas as pd
import os
import re
from PIL import Image
import easyocr
import numpy as np

# --- 1. CONFIGURAÇÃO DE PERSISTÊNCIA (PARA NÃO SUMIR) ---
DB_FILE = "banco_dados_fiel.csv"

if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            st.session_state.velas = pd.read_csv(DB_FILE)['velas'].tolist()
        except: st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar_no_arquivo():
    pd.DataFrame({'velas': st.session_state.velas}).to_csv(DB_FILE, index=False)

@st.cache_resource
def iniciar_leitor():
    return easyocr.Reader(['en'], gpu=False)

reader = iniciar_leitor()

# --- LAYOUT FIEL AO DESENHO (ORDEM EXATA) ---

# TÍTULO SUPERIOR
st.markdown("<h2 style='text-align: center;'>ATE 500 VELAS</h2>", unsafe_allow_html=True)

# MOLDURA DE ENTRADA (ABAS LADO A LADO)
aba_manual, aba_print = st.tabs(["📥 INSERIR MANUAL", "📸 INSERIR ATRAVÉS PRINT"])

with aba_manual:
    manual_txt = st.text_area("Exemplo: 1.25x 4.10x", placeholder="Cole ou digite aqui...", height=100, key="txt_manual")

with aba_print:
    arquivo_img = st.file_uploader("Arraste o print aqui", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

# BOTÃO DE ADICIONAR (PROCESSA TUDO)
if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    texto_bruto = ""
    if arquivo_img:
        with st.spinner("Lendo print..."):
            img = Image.open(arquivo_img)
            resultado_ocr = reader.readtext(np.array(img), detail=0)
            texto_bruto = " ".join(resultado_ocr)
    
    if manual_txt:
        texto_bruto += " " + manual_txt

    if texto_bruto:
        # REGEX BLINDADA: Filtra apenas velas reais (1.00 até 1000.00)
        # Isso remove automaticamente horários (22.18) e IDs de rodada gigantes
        brutos = re.findall(r"(\d+[\.\d]*)", texto_bruto.replace(',', '.'))
        novas_filtradas = []
        for v in brutos:
            try:
                valor = float(v)
                # Só aceita se for uma vela plausível (1x a 1000x)
                if 1.0 <= valor <= 1000.0:
                    novas_filtradas.append(valor)
            except:
                continue
        
        if novas_filtradas:
            # SINCRONIZAÇÃO: Identifica se o print novo já começa com velas que estão no banco
            ultimas_banco = st.session_state.velas[-15:]
            ponto_encaixe = 0
            for i in range(len(novas_filtradas)):
                if novas_filtradas[i:i+2] in [ultimas_banco[j:j+2] for j in range(len(ultimas_banco)-1)]:
                    ponto_encaixe = i + 2
            
            velas_para_inserir = novas_filtradas[ponto_encaixe:]
            
            if velas_para_inserir:
                st.session_state.velas.extend(velas_para_inserir)
                salvar_no_arquivo()
                st.success(f"✅ {len(velas_para_inserir)} velas adicionadas com sucesso!")
                st.rerun()
            else:
                st.warning("⚠️ Todas as velas desse print já estão no banco.")

st.divider()

# --- SEÇÃO: BUSCA DE PADRÃO (MEIO DO DESENHO) ---
st.subheader("🔍 BUSCA DE PADRAO")
col_input, col_botao = st.columns([0.85, 0.15])

with col_input:
    padrao_procurado = st.text_input("Insira o padrão de 10 velas:", placeholder="1.10, 2.50, 1.05...", label_visibility="collapsed")

with col_botao:
    btn_buscar = st.button("🔎")

if btn_buscar and padrao_procurado:
    try:
        alvo = [float(x.strip()) for x in padrao_procurado.replace(',', ' ').split()]
        n = len(alvo)
        banco = st.session_state.velas
        achou_algo = False
        
        for i in range(len(banco) - n):
            if banco[i : i + n] == alvo:
                achou_algo = True
                st.success(f"🎯 PADRÃO ENCONTRADO (Posição {i+1})")
                
                # ALERTA DE ANTECIPAÇÃO (PRÓXIMAS 15 VELAS)
                futuro = banco[i + n : i + n + 15]
                if futuro:
                    st.warning("⚠️ ALERTA: PRÓXIMAS 15 VELAS APÓS O PADRÃO")
                    chips = []
                    for v in futuro:
                        # ROSA CHOQUE PARA >= 8x
                        cor_f = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#FFFFFF"
                        chips.append(f"<b style='color:{cor_f}; font-size:1.1em;'>{v:.2f}x</b>")
                    st.markdown(" , ".join(chips), unsafe_allow_html=True)
        
        if not achou_algo:
            st.error("❌ Padrão não localizado no histórico.")
    except:
        st.error("Formato inválido. Use números separados por vírgula ou espaço.")

st.divider()

# --- SEÇÃO: HISTÓRICO DE VELAS (TODAS) ---
st.subheader("📋 HISTORICO DE VELAS")
if st.session_state.velas:
    df_visão = pd.DataFrame({"Vela": st.session_state.velas[::-1]})
    
    def aplicar_cor_8x(val):
        return 'color: #FF00FF; font-weight: bold' if val >= 8.0 else 'color: white'

    st.dataframe(
        df_visão.style.map(aplicar_cor_8x).format("{:.2f}x"), 
        use_container_width=True, 
        height=400
    )

st.divider()

# --- SEÇÃO: ÚLTIMA 20 VELA ADICIONADA (RODAPÉ) ---
st.subheader("📉 ULTIMA 20 VELA ADICIONADA")
if st.session_state.velas:
    ultimas_20 = st.session_state.velas[-20:][::-1]
    resumo_html = []
    for v in ultimas_20:
        cor_r = "#FF00FF" if v >= 8.0 else "#00FF00" if v >= 2.0 else "#FFFFFF"
        resumo_html.append(f"<span style='color:{cor_r}; font-weight:bold; font-size:1.1em;'>{v:.2f}x</span>")
    
    st.markdown(" , ".join(resumo_html), unsafe_allow_html=True)

# BOTÃO DE RESET DISCRETO NA SIDEBAR
if st.sidebar.checkbox("Limpar Banco"):
    if st.sidebar.button("🗑️ ZERAR TUDO AGORA"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.velas = []
        st.rerun()

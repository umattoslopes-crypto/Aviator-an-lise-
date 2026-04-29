     import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import easyocr
import numpy as np
from PIL import Image

# --- CONFIGURAÇÃO VISUAL (MANTENDO SEU LAYOUT) ---
st.set_page_config(page_title="Analisador Pro", page_icon="📈")

# --- CONEXÃO COM BANCO DE DADOS (PARA NÃO SUMIR NADA) ---
# 1. Crie uma Planilha Google e escreva 'velas' na célula A1.
# 2. Compartilhe como EDITOR para QUALQUER PESSOA COM O LINK.
# 3. Cole o link abaixo:
URL_BANCO_DADOS = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_do_banco():
    try:
        df = conn.read(spreadsheet=URL_BANCO_DADOS)
        # Limpa dados inválidos e converte para número
        return [float(x) for x in df['velas'].tolist() if str(x).replace('.','').isdigit()]
    except:
        return []

# Inicializa o histórico buscando na nuvem toda vez que o app abre/reinicia
if 'velas' not in st.session_state:
    st.session_state.velas = carregar_do_banco()

# --- FUNÇÃO DE LEITURA DE IMAGEM (OCR) ---
@st.cache_resource
def carregar_leitor():
    return easyocr.Reader(['en']) # Carrega o leitor uma única vez

def ler_velas_da_imagem(imagem):
    reader = carregar_leitor()
    img_array = np.array(Image.open(imagem))
    resultado = reader.readtext(img_array)
    detectadas = []
    for (bbox, texto, prob) in resultado:
        texto_limpo = texto.replace('x', '').replace(',', '.').strip()
        try:
            valor = float(texto_limpo)
            if 1.0 <= valor <= 1000.0: detectadas.append(valor)
        except: continue
    return detectadas

# --- LAYOUT DO APP (CONFORME SEUS PRINTS) ---
st.title("📈 Analisador Pro: Histórico & Padrões")

# Seção de Inserção
with st.expander("🚨 ADICIONAR NOVAS VELAS", expanded=True):
    metodo = st.radio("Como deseja adicionar?", ["Texto/Digitar", "Ler por Foto (Print)"], horizontal=True)
    
    if metodo == "Texto/Digitar":
        entrada = st.text_area("Cole até 500 velas aqui:", placeholder="Ex: 2.76, 1.05, 8.40...")
        if st.button("GRAVAR NO HISTÓRICO"):
            if entrada:
                novas = [float(v.strip()) for v in entrada.replace(",", " ").split() if v.strip()]
                st.session_state.velas.extend(novas)
                # Salva na Planilha Google (Persistência)
                conn.update(spreadsheet=URL_BANCO_DADOS, data=pd.DataFrame({"velas": st.session_state.velas}))
                st.success(f"{len(novas)} velas salvas na nuvem!")
                st.rerun()
    
    else:
        arquivo_img = st.file_uploader("Envie o print das velas", type=['png', 'jpg', 'jpeg'])
        if arquivo_img:
            if st.button("LER FOTO E SALVAR"):
                with st.spinner("Lendo números da imagem..."):
                    velas_lidas = ler_velas_da_imagem(arquivo_img)
                    if velas_lidas:
                        st.session_state.velas.extend(velas_lidas)
                        # Salva na Planilha Google (Persistência)
                        conn.update(spreadsheet=URL_BANCO_DADOS, data=pd.DataFrame({"velas": st.session_state.velas}))
                        st.success(f"Foram lidas e salvas {len(velas_lidas)} velas!")
                        st.rerun()
                    else:
                        st.error("Nenhuma vela detectada. Tente um print mais nítido.")

st.divider()

# Seção de Busca
st.subheader("🔍 BUSCAR PADRÃO (ÚLTIMAS 10)")
st.write("Insira as 10 velas para buscar repetição no banco:")
busca_input = st.text_input("Velas para análise:", placeholder="Ex: 1.50, 2.00...", label_visibility="collapsed")

if st.button("BUSCAR"):
    if len(st.session_state.velas) > 10:
        ultima_sequencia = st.session_state.velas[-10:]
        st.info(f"Analisando histórico baseado nas últimas 10 velas...")
        # Adicione aqui sua lógica específica de alerta 8x
    else:
        st.warning("Histórico insuficiente (mínimo 10 velas).")

st.divider()

# Seção do Contador (Idêntica ao seu print)
st.subheader("📊 Contador")
st.write("Velas Acumuladas")
total = len(st.session_state.velas)
st.header(f"{total} / 10.000")

if total < 10000:
    st.info(f"Faltam {10000 - total} velas.")

st.divider()

# Botão de Reset
if st.button("🗑️ RESETAR BANCO DE DADOS"):
    if st.checkbox("Confirmar que deseja apagar as 10.000 velas da nuvem?"):
        conn.update(spreadsheet=URL_BANCO_DADOS, data=pd.DataFrame(columns=["velas"]))
        st.session_state.velas = []
        st.rerun()
   

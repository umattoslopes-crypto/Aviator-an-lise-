import streamlit as st
import pandas as pd
import os
import re
from PIL import Image, ImageOps
import easyocr
import numpy as np
import cv2

# Configurações de arquivo
DB_FILE = "banco_velas_projeto.csv"
MAX_VELAS = 10000
MAX_POR_ENVIO = 500

# =========================
# BANCO DE DADOS
# =========================
if 'velas' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            st.session_state.velas = [
                float(v) for v in df['velas'].dropna() if float(v) > 0
            ]
        except:
            st.session_state.velas = []
    else:
        st.session_state.velas = []

def salvar():
    pd.DataFrame({'velas': st.session_state.velas[-MAX_VELAS:]}).to_csv(DB_FILE, index=False)

# =========================
# OCR E PROCESSAMENTO
# =========================
@st.cache_resource
def load_reader():
    # Carrega o modelo uma vez para ganhar performance
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

def preprocessar(img):
    """
    Melhoria crucial: Converte para cinza e aplica threshold adaptativo
    para capturar velas de cores claras (cinza/branco) que o OCR ignorava.
    """
    img = ImageOps.grayscale(img)
    img_np = np.array(img)
    
    # Aplica um filtro de nitidez e binarização adaptativa
    # Isso ajuda a destacar números baixos que costumam ser cinza claro
    img_bin = cv2.adaptiveThreshold(
        img_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 31, 2
    )
    return img_bin

def organizar_por_posicao(res):
    """
    Agrupa os textos detectados por linhas horizontais e 
    ordena da direita para a esquerda (como no histórico dos jogos).
    """
    linhas = []
    for (bbox, texto, conf) in res:
        texto = texto.strip().lower()
        
        # Ignora textos muito curtos ou que claramente não são números
        if len(texto) < 1:
            continue

        y_topo = bbox[0][1]
        x_esq = bbox[0][0]

        colocado = False
        for linha in linhas:
            # Se a diferença de altura for pequena, pertence à mesma linha
            if abs(linha['y'] - y_topo) < 25:
                linha['itens'].append((x_esq, texto))
                colocado = True
                break

        if not colocado:
            linhas.append({'y': y_topo, 'itens': [(x_esq, texto)]})

    # Ordena linhas de baixo para cima (mais recentes primeiro dependendo do print)
    linhas.sort(key=lambda l: l['y'])

    resultado = []
    for linha in linhas:
        # Ordena itens da linha da direita para a esquerda
        linha['itens'].sort(key=lambda i: i[0], reverse=True)
        for _, texto in linha['itens']:
            resultado.append(texto)

    return resultado

def extrair_velas(lista_textos):
    """
    Extrai números decimais. Agora aceita números mesmo sem o 'x'
    para garantir que velas baixas (1.00) sejam lidas.
    """
    velas_extraidas = []
    for texto in lista_textos:
        # Limpa o texto: troca vírgula por ponto e remove letras indesejadas
        texto_limpo = texto.replace(',', '.').replace('s', '5').replace('o', '0')
        
        # Regex busca: números com ou sem decimais, seguidos ou não de 'x'
        matches = re.findall(r"(\d+(?:\.\d+)?)\s*x?", texto_limpo)
        
        for m in matches:
            try:
                val = float(m)
                if 1.0 <= val <= 10000.0:
                    velas_extraidas.append(val)
            except:
                continue
    return velas_extraidas

# =========================
# INTERFACE STREAMLIT
# =========================
st.set_page_config(page_title="Analisador de Velas", layout="centered")
st.title("📊 ANALISADOR DE VELAS (OCR)")

aba1, aba2 = st.tabs(["📸 PRINT DO HISTÓRICO", "📥 ADICIONAR MANUAL"])

with aba1:
    arquivo = st.file_uploader("Envie o print das velas", type=['png','jpg','jpeg'])
    if arquivo:
        st.image(arquivo, caption="Imagem carregada", use_container_width=True)

with aba2:
    manual = st.text_area("Cole as velas separadas por espaço (Ex: 1.20 5.00 1.05)")

# =========================
# BOTÃO DE PROCESSAMENTO
# =========================
if st.button("🚀 ADICIONAR AO HISTÓRICO", use_container_width=True):
    novas_velas = []

    if arquivo:
        with st.spinner("Lendo imagem..."):
            img_processada = preprocessar(Image.open(arquivo))
            resultado_ocr = reader.readtext(img_processada)
            textos_ordenados = organizar_por_posicao(resultado_ocr)
            novas_velas = extrair_velas(textos_ordenados)
    
    if manual:
        novas_velas += extrair_velas(manual.split())

    if novas_velas:
        # Evita duplicados em excesso e limita envio
        novas_velas = novas_velas[:MAX_POR_ENVIO]
        
        for v in novas_velas:
            st.session_state.velas.append(v)

        # Mantém apenas o limite do banco
        if len(st.session_state.velas) > MAX_VELAS:
            st.session_state.velas = st.session_state.velas[-MAX_VELAS:]

        salvar()
        st.success(f"✅ {len(novas_velas)} velas adicionadas com sucesso!")
        st.rerun()
    else:
        st.error("Nenhuma vela detectada. Tente um print com mais zoom ou digite manual.")

st.divider()

# =========================
# VISUALIZAÇÃO E BUSCA
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔍 BUSCAR PADRÃO")
    seq = st.text_input("Sequência (ex: 1.05 2.10)")
    if st.button("🔎 BUSCAR"):
        padrao = [float(x.replace(',', '.')) for x in seq.split()]
        hist = st.session_state.velas
        achou = False
        for i in range(len(hist) - len(padrao)):
            if hist[i:i+len(padrao)] == padrao:
                achou = True
                st.write(f"✅ Padrão encontrado! Próximas: **{hist[i+len(padrao):i+len(padrao)+3]}**")
        if not achou: st.warning("Padrão não visto.")

with col2:
    st.subheader("📋 ÚLTIMAS 10")
    if st.session_state.velas:
        ultimas = st.session_state.velas[-10:]
        for v in reversed(ultimas):
            cor = "#FF00FF" if v >= 10 else "#00FF00" if v >= 2 else "#FF4B4B"
            st.markdown(f"<span style='color:{cor}; font-weight:bold; font-size:20px'>{v:.2f}x</span>", unsafe_allow_html=True)

# =========================
# RESET
# =========================
with st.expander("⚙️ OPÇÕES DE BANCO"):
    if st.button("🗑️ APAGAR TUDO"):
        st.session_state.velas = []
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

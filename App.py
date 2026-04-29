import streamlit as st
import pandas as pd
import easyocr
import numpy as np
from PIL import Image
import os

st.set_page_config(page_title="Analisador Pro", layout="centered")

# Banco de Dados Local
DB_FILE = "banco_de_velas.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            return [float(v) for v in df['velas'].tolist()]
        except: return []
    return []

def salvar_dados(lista):
    pd.DataFrame({"velas": lista}).to_csv(DB_FILE, index=False)

if 'velas' not in st.session_state:
    st.session_state.velas = carregar_dados()

@st.cache_resource
def get_reader():
    return easyocr.Reader(['en'])

st.title("📈 Analisador Pro: Histórico Completo")

# --- SEÇÃO 1: ADICIONAR E SINCRONIZAR ---
with st.expander("🚨 ADICIONAR NOVAS VELAS", expanded=True):
    aba1, aba2, aba3 = st.tabs(["📝 Texto", "📷 Prints Sincronizados", "📂 Backup"])
    
    with aba1:
        entrada = st.text_area("Cole as velas aqui (Ex: 1.50, 2.00):")
        if st.button("GRAVAR TEXTO", use_container_width=True):
            if entrada:
                novas = [float(v.strip()) for v in entrada.replace(",", " ").split() if v.strip()]
                st.session_state.velas.extend(novas)
                salvar_dados(st.session_state.velas)
                st.success("✅ Gravado!")
                st.rerun()

    with aba2:
        fotos = st.file_uploader("Suba um ou mais prints:", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if fotos and st.button("LER E SINCRONIZAR", use_container_width=True):
            with st.spinner("🤖 Sincronizando..."):
                reader = get_reader()
                lidas = []
                for foto in fotos:
                    res = reader.readtext(np.array(Image.open(foto)))
                    for (_, t, _) in res:
                        val = t.replace('x','').replace(',','.').strip()
                        try:
                            num = float(val)
                            if 1.0 <= num <= 1000.0: lidas.append(num)
                        except: continue
                
                if lidas:
                    if not st.session_state.velas:
                        novas_reais = lidas
                    else:
                        # Pega as últimas 15 para comparar e evitar duplicados
                        ultimas = st.session_state.velas[-15:]
                        ponto_corte = 0
                        for i in range(len(lidas)):
                            if lidas[i] in ultimas: ponto_corte = i + 1
                            else: break
                        novas_reais = lidas[ponto_corte:]
                    
                    if novas_reais:
                        st.session_state.velas.extend(novas_reais)
                        salvar_dados(st.session_state.velas)
                        st.success(f"🚀 {len(novas_reais)} novas velas adicionadas!")
                    else: st.warning("Velas já existem no histórico.")
                    st.rerun()

    with aba3:
        st.write("Restaure um histórico salvo:")
        arq_backup = st.file_uploader("Arquivo CSV", type=['csv'])
        if arq_backup and st.button("RESTAURAR"):
            df_bkp = pd.read_csv(arq_backup)
            st.session_state.velas = df_bkp['velas'].tolist()
            salvar_dados(st.session_state.velas)
            st.success("Histórico Restaurado!")
            st.rerun()

st.divider()

# --- SEÇÃO 2: BUSCA DE PADRÃO ---
st.subheader("🔍 BUSCAR PADRÃO (15 VELAS)")
if st.button("ANALISAR AGORA", use_container_width=True):
    if len(st.session_state.velas) > 1:
        ultima = st.session_state.velas[-1]
        encontrou = False
        for i in range(len(st.session_state.velas) - 1):
            if st.session_state.velas[i] == ultima:
                seq = st.session_state.velas[i+1 : i+16]
                if any(v >= 8.0 for v in seq):
                    st.error(f"⚠️ **PADRÃO 8X ENCONTRADO!**")
                    cols = st.columns(5)
                    for idx, v in enumerate(seq):
                        txt = f"🔥 **{v:.2f}x**" if v >= 8.0 else f"{v:.2f}x"
                        cols[idx % 5].write(f"{idx+1}º: {txt}")
                    encontrou = True
                    st.divider()
        if not encontrou: st.info(f"Sem 8x após {ultima}x.")

st.divider()

# --- SEÇÃO 3: CONTADOR E TABELA ---
st.subheader("📊 Contador de Histórico")
total = len(st.session_state.velas)
st.header(f"{total} / 10.000")

with st.expander("👁️ VER TODO O HISTÓRICO SALVO", expanded=True):
    if total > 0:
        df_full = pd.DataFrame({
            "Posição": range(1, total + 1),
            "Vela": [f"{v:.2f}x" for v in st.session_state.velas]
        })
        st.dataframe(df_full.iloc[::-1], use_container_width=True, height=400)
    else:
        st.write("Banco de dados vazio.")

st.divider()

# --- SEÇÃO 4: BACKUP E ZERAR CONTADOR ---
st.subheader("⚙️ Gerenciar Banco de Dados")

# Botão de Backup
csv_data = pd.DataFrame({"velas": st.session_state.velas}).to_csv(index=False)
st.download_button("💾 BAIXAR BACKUP (CSV)", csv_data, "banco_aviator.csv", "text/csv", use_container_width=True)

st.write("---")

# Botão para Zerar o Contador (Reset Total)
st.warning("Cuidado: A ação abaixo é irreversível!")
if st.button("🗑️ ZERAR TODO O CONTADOR", use_container_width=True):
    if st.checkbox("Confirmar que desejo APAGAR TUDO e voltar para 0?"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.velas = []
        st.success("O contador foi zerado com sucesso!")
        st.rerun()

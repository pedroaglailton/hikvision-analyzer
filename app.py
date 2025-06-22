# app.py

import streamlit as st
from hikvision_analyzer import analyze_cameras
from hikvision_analyzer.exporter import export_to_excel
import pandas as pd
import io

# Configuração da página
st.set_page_config(page_title="Analisador Hikvision", layout="wide")
st.title("🎥 Analisador de Câmeras Hikvision")

# Sidebar - Configurações
st.sidebar.header("⚙️ Configurações")
username = st.sidebar.text_input("Usuário Hikvision", value="admin")
password1 = st.sidebar.text_input("Senha 1", type="password", value="senha")
password2 = st.sidebar.text_input("Senha 2 (opcional)", type="password")
port = st.sidebar.number_input("Porta", value=80, min_value=1, max_value=65535)
timeout = st.sidebar.slider("Timeout (segundos)", min_value=1, max_value=30, value=5)

# Upload do arquivo TXT com IPs
st.sidebar.header("📁 Arquivo de IPs")
uploaded_file = st.sidebar.file_uploader("Selecione um arquivo .txt com os IPs", type=["txt"])

# Função principal
if uploaded_file is not None:
    # Ler IPs do arquivo
    file_content = uploaded_file.getvalue().decode("utf-8")
    ips = [line.strip() for line in file_content.splitlines() if line.strip()]
    
    st.success(f"✅ {len(ips)} IP(s) carregado(s).")
    
    if st.button("🔍 Iniciar Análise", type="primary"):
        passwords = [p for p in [password1, password2] if p.strip()]
        if not passwords:
            st.error("⚠️ Insira pelo menos uma senha.")
        else:
            placeholder = st.empty()
            progress_bar = st.progress(0)
            
            with placeholder.container():
                st.subheader("📊 Resultados em Tempo Real")
                status_area = st.empty()

            results = []

            def update_status(index, ip, status):
                results.append({
                    "IP": ip,
                    "Status": status,
                    "Progresso": f"{index + 1}/{len(ips)}"
                })
                df_progress = pd.DataFrame(results)
                status_area.write(df_progress.to_string(index=False))

            index = 0
            for ip in ips:
                df_part = analyze_cameras([ip], username, passwords, port=port, timeout=timeout)
                if not df_part.empty:
                    results.append({
                        "IP": ip,
                        "Status": "Sucesso",
                        "Progresso": f"{index + 1}/{len(ips)}"
                    })
                else:
                    results.append({
                        "IP": ip,
                        "Status": "Erro",
                        "Progresso": f"{index + 1}/{len(ips)}"
                    })
                index += 1
                progress_bar.progress(index / len(ips))
                status_area.write(pd.DataFrame(results).to_string(index=False))

            # Consolidar todos os resultados
            df_final = analyze_cameras(ips, username, passwords, port=port, timeout=timeout)

            st.subheader("📊 Resultado Final")
            if not df_final.empty:
                # Mostrar DataFrame
                st.dataframe(df_final)

                # Exportar para Excel
                buffer = io.BytesIO()
                export_to_excel(df_final, buffer)
                buffer.seek(0)

                st.download_button(
                    label="📥 Baixar Relatório Excel",
                    data=buffer,
                    file_name="relatorio_hikvision.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # Estatísticas finais
                success_count = df_final[df_final["Status"] == "Sucesso"]["IP"].nunique()
                error_count = df_final[df_final["Status"] == "Erro"]["IP"].nunique()
                st.markdown(f"✅ Câmeras acessadas com sucesso: **{success_count}**")
                st.markdown(f"❌ Câmeras com erro: **{error_count}**")

            else:
                st.warning("⚠️ Nenhuma câmera foi acessada com sucesso.")

# Mensagem inicial caso não tenha upload
else:
    st.info("ℹ️ Por favor, faça o upload de um arquivo .txt com os IPs das câmeras.")

# Rodapé
st.markdown("---")
st.caption("© Pedro Aglailton | Analisador Profissional Hikvision v2.1")
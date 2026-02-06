import streamlit as st
import pandas as pd
import io

# 1. Definição do HTML do Rodapé (Definido no início para evitar NameError)
footer_html = """
<div style='text-align: center; color: gray;'>
    <p style='margin-bottom: 5px;'>Desenvolvido por <b>Rodrigo AIOSA</b></p>
    <div style='display: flex; justify-content: center; gap: 20px; font-size: 24px;'>
        <a href='https://wa.me/5511977019335' target='_blank' style='text-decoration: none;'>
            <img src='https://cdn-icons-png.flaticon.com/512/733/733585.png' width='25' height='25' title='WhatsApp'>
        </a>
        <a href='https://www.linkedin.com/in/rodrigoaiosa/' target='_blank' style='text-decoration: none;'>
            <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' width='25' height='25' title='LinkedIn'>
        </a>
    </div>
</div>
"""

# Configuração da Página
st.set_page_config(page_title="Análise Pro: Amortização", layout="wide")

def calcular_todos_sistemas(valor, taxa_anual, prazo, metodo_taxa):
    if metodo_taxa == "Mensal (Nominal/12)":
        taxa_mensal = (taxa_anual / 100) / 12
    else:
        taxa_mensal = (1 + taxa_anual/100)**(1/12) - 1
        
    sistemas = {}
    
    def gerar_df(dados):
        return pd.DataFrame(dados, columns=['Mês', 'Parcela', 'Juros', 'Amortização', 'Saldo Devedor'])

    # --- SAC ---
    sd, amort = valor, valor / prazo
    sistemas['SAC'] = gerar_df([[i, amort + (sd - (i-1)*amort) * taxa_mensal, (sd - (i-1)*amort) * taxa_mensal, amort, max(sd - i*amort, 0)] for i in range(1, prazo + 1)])

    # --- PRICE ---
    sd = valor
    p_fixa = valor * (taxa_mensal * (1 + taxa_mensal)**prazo) / ((1 + taxa_mensal)**prazo - 1)
    dados_price = []
    for i in range(1, prazo + 1):
        j = sd * taxa_mensal
        a = p_fixa - j
        sd -= a
        dados_price.append([i, p_fixa, j, a, max(sd, 0)])
    sistemas['PRICE'] = gerar_df(dados_price)

    # --- SACRE ---
    sd = valor
    dados_sacre = []
    for i in range(1, prazo + 1):
        a = sd / (prazo - i + 1)
        j = sd * taxa_mensal
        dados_sacre.append([i, a + j, j, a, max(sd - a, 0)])
        sd -= a
    sistemas['SACRE'] = gerar_df(dados_sacre)

    return sistemas

# --- Interface Principal ---
st.title("📊 Análise Pro: Sistemas de Amortização")
st.markdown("Compare qual sistema protege melhor o seu patrimônio ao longo do tempo.")

tab_analise, tab_ajuda = st.tabs(["🚀 Simulador e Análise", "📖 Entenda os Sistemas"])

with tab_analise:
    with st.sidebar:
        st.header("⚙️ Configurações")
        v_total = st.number_input("Valor Financiado (R$)", min_value=0.0, value=100000.0, step=1000.0)
        t_anual = st.number_input("Taxa de Juros Anual (%)", min_value=0.0, value=12.0)
        p_meses = st.number_input("Prazo (Meses)", min_value=1, value=60)
        metodo_taxa = st.selectbox("Cálculo da Taxa", ["Mensal (Nominal/12)", "Equivalente (Exponencial)"])
        
        # O clique no botão salva os dados no estado da sessão
        if st.button("🚀 Calcular e Analisar Vantagens", use_container_width=True):
            st.session_state['resultados'] = calcular_todos_sistemas(v_total, t_anual, p_meses, metodo_taxa)
            st.session_state['prazo'] = p_meses

    # Exibe os resultados se eles existirem no estado da sessão
    if 'resultados' in st.session_state:
        res = st.session_state['resultados']
        p_meses = st.session_state['prazo']
        
        resumo = []
        for nome, df in res.items():
            resumo.append({
                'Sistema': nome,
                'Total Pago': df['Parcela'].sum(),
                'Total Juros': df['Juros'].sum(),
                'Primeira Parcela': df['Parcela'].iloc[0],
                'Última Parcela': df['Parcela'].iloc[-1]
            })
        
        df_res = pd.DataFrame(resumo).sort_values('Total Juros')
        maior_juros = df_res['Total Juros'].max()
        df_res['Economia'] = maior_juros - df_res['Total Juros']

        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("🏆 Ranking de Economia")
            st.table(df_res.style.format({
                'Total Pago': 'R$ {:.2f}', 
                'Total Juros': 'R$ {:.2f}', 
                'Economia': 'R$ {:.2f}',
                'Primeira Parcela': 'R$ {:.2f}',
                'Última Parcela': 'R$ {:.2f}'
            }))
            
            melhor = df_res.iloc[0]
            st.success(f"O sistema **{melhor['Sistema']}** é o mais vantajoso!")

        with col2:
            st.subheader("📉 Evolução do Saldo Devedor")
            plot_data = pd.DataFrame({'Mês': range(1, p_meses + 1)})
            for nome, df in res.items():
                plot_data[nome] = df['Saldo Devedor'].values
            st.line_chart(plot_data.set_index('Mês'))

        # Preparação do arquivo Excel para download
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_res.to_excel(writer, sheet_name='Resumo', index=False)
            for nome, df in res.items():
                df.to_excel(writer, sheet_name=nome, index=False)
        
        st.download_button(
            label="📥 Baixar Relatório Completo (.xlsx)",
            data=output.getvalue(),
            file_name="analise_amortizacao_aiosa.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

with tab_ajuda:
    st.header("Entenda a diferença entre os sistemas")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📌 SAC")
        st.write("Amortização constante, parcelas decrescentes.")
    with col_b:
        st.subheader("📌 PRICE")
        st.write("Parcelas fixas, juros maiores no início.")

# --- RODAPÉ ---
st.markdown("---")
st.markdown(footer_html, unsafe_allow_html=True)

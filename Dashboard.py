#Importando todas as bibliotecas necessárias para o TechChallenge
import streamlit as st
import requests #biblioteca para requisições
import pandas as pd
from bs4 import BeautifulSoup #extração de dados de documentos HTML e XML
from datetime import datetime
import psycopg2 as ps
from prophet import Prophet
import matplotlib.pyplot as plt

# Função para conectar ao banco de dados
#@ st.cache_resource

def conexao():
    try:
        conn = ps.connect(
            host="db-previsao.cbnbr78bfmrx.us-east-1.rds.amazonaws.com",
            port=5432,
            database="bd_covid",
            user="postgres",
            password="covid123"
        )
        return conn
    except (Exception, ps.Error) as error:
        print("Erro ao conectar ao banco de dados", error)
        raise

# Função para inserir dados no banco de dados
def inserir_dados(df):
    conn = conexao()
    try:
        df.to_sql('previsao2', conn, if_exists='append', index=False, method='multi', chunksize=1000)
        print("Inserção bem-sucedida.")
    except Exception as e:
        print(f"Erro ao inserir dados na tabela: {str(e)}")
    finally:
        conn.close()

# Função para obter o DataFrame existente do banco de dados
def obter_dataframe_existente(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM public.previsao2')
            existing_df = pd.DataFrame(cursor.fetchall(), columns=['data', 'preco'])
        return existing_df
    except Exception as e:
        print(f"Erro ao obter DataFrame existente: {str(e)}")
        return pd.DataFrame(columns=['data', 'preco'])

# Função para atualizar o DataFrame
def atualizar_dataframe(df, new_data):
    df['data'] = pd.to_datetime(df['data'], dayfirst=True)
    new_data['data'] = pd.to_datetime(new_data['data'], dayfirst=True)
    new_data['preco'] = new_data['preco'] / 100

    last_date = df['data'].max()
    new_rows = new_data[new_data['data'] > last_date]

    if not new_rows.empty:
        update_df = pd.concat([df, new_rows], ignore_index=True)
    else:
        update_df = df

    return update_df

# Requisição ao site do IPEA
url = 'http://www.ipeadata.gov.br/ExibeSerie.aspx?module=m&serid=1650971490&oper=view'
response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'id': 'grd_DXMainTable'})
    new_df = pd.read_html(str(table), header=0)[0]
    new_df = new_df.rename(columns={'Data': 'data', 'Preço - petróleo bruto - Brent (FOB)': 'preco'})

    connection = conexao()

    try:
        existing_df = obter_dataframe_existente(connection)
    except:
        existing_df = pd.DataFrame(columns=new_df.columns)

    update_df = atualizar_dataframe(existing_df, new_df)

    inserir_dados(update_df)
    connection.close()
else:
    print('Falha ao acessar a página: Status Code', response.status_code)


# Consulta ao banco de dados para verificar se a inserção foi bem-sucedida
bd_conn = conexao()
query = 'SELECT * FROM public.previsao2'
df = pd.read_sql_query(query, bd_conn)
df['data'] = pd.to_datetime(df['data'])
df_20 = df[df['data'] >= '2004-01-01']
df_10 = df[df['data'] >= '2018-01-01']
df = df.rename(columns = {'data':'Período','preco':'Valor (FOB US$)'})
df_20 = df_20.rename(columns = {'data':'Período','preco':'Valor (FOB US$)'})

### Modelo de ML adaptado do notebook pra rodar aqui no streamlit ###
#Renomeando as variáveis da base de dados pra que o modelo seja executado
df_10 = df_10.rename(columns={'data':'ds','preco':'y'})
df_10['ds'] = pd.to_datetime(df_10['ds']) #convertendo ds de object para datetime

#criando uma variável para o modelo
m_prop = Prophet(seasonality_prior_scale=10.0,changepoint_prior_scale=0.1, n_changepoints=25)
#treinando o modelo - efetuando o treinamento do modelo considerando o periodo dos ultimos 10 anos para previsões
m_prop.fit(df_10)
#Próximos 90 dias de previsão
future = m_prop.make_future_dataframe(periods=90)
#Realizando a previsão(forecast)
forecast = m_prop.predict(future)

graf_forecast = m_prop.plot(forecast)

prev = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
prev[['yhat', 'yhat_lower', 'yhat_upper']] = prev[[ 'yhat', 'yhat_lower', 'yhat_upper']].round(2).map('{:.2f}'.format)
prev = prev.rename(columns={'ds':'Período','yhat':'Previsão (FOB US$)','yhat_lower':'Mínima (FOB US$)','yhat_upper':'Máxima (FOB US$)'})
base = df_10.rename(columns={'ds':'Período','y':'Valor (FOB US$)'})
base['Período'] = pd.to_datetime(base['Período']).dt.date
prev['Período'] = pd.to_datetime(prev['Período']).dt.date
base_index= base.set_index('Período')
prev_index = prev.set_index('Período')
base_index['Valor (FOB US$)'] = base_index['Valor (FOB US$)'].round(2).map('{:.2f}'.format)

### Criando gráficos para plotar em produção ###
def grf_full():
    fig, ax = plt.subplots(figsize=(12,4))
    ax.plot(df_10['ds'], df_10['y'], label='Dados Históricos')
    ax.plot(forecast['ds'], forecast['yhat'], label='Previsão')
    # Personalizar o gráfico (adicionar rótulos, título, etc., conforme necessário)
    ax.set_xlabel("\nPeríodo")
    ax.set_ylabel("Valor Médio (FOB US$)\n")
    ax.set_title("Comportamento do modelo em relação à base - Somente Previsão\n")
    ax.legend()
    ax.grid(True)    
    return fig

st.set_page_config(layout = 'wide') #mantém o visual da página sem sobreposição

#Título do TechChallenge
st.title('Análise da série histórica do preço do barril de Petróleo Brent - FOB :oil_drum:')


# Mostrar o gráfico usando st.line_chart()
st.subheader("Evolução do Preço do Petróleo : 1987 - 2024  ")
st.line_chart(df, x='Período', y='Valor (FOB US$)')
st.subheader("Evolução do Preço do Petróleo : 2004 - 2024")
st.line_chart(df_20, x='Período', y='Valor (FOB US$)')

st.subheader("Evolução do Preço do Petróleo : 2018 - 2024 - Período de treino do Modelo")
st.line_chart(base, x = 'Período', y='Valor (FOB US$)')
st.write('Fonte - IPEA')

st.subheader("Gráfico gerado pelo Prophet - Previsão para 90 dias")
st.pyplot(graf_forecast)

figure = grf_full()
st.pyplot(figure)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Tabela com valores dos últimos 6 anos")
    st.dataframe(base_index)
with col2:
    st.subheader("Tabela com valores previstos pelo modelo")
    st.dataframe(prev_index)

container = st.container(border=True)
with container:
    st.markdown(""" ### Insights da análise: :white_check_mark:

- **1987 - 1989:** Apesar do barril de petróleo não oscilar e se manter a uma média de US\$20,00, esse período foi marcado por alguns acontecimentos históricos, como a mínima em sua série histórica que foi em 1988, resultado de uma desaceleração da demanda global e também o encerramento de um conflito entre Iraque e Irã, que estabilizou a produção de petróleo na região.

- **1990 - 2004:** Período complicado no começo dos anos 1990, entre 1990 e 1991 ocorreu a "Guerra do Golfo", conflito armado na principal região produtora de petróleo mundial, o que fez com que o preço do barril saltasse da casa dos US\$ 20,00 para US\$ 40,00 em dois anos. Após esse conflito, o valor se estabilizou novamente na casa dos US\$ 20,00, caindo no período de 1996 a 2000, devido a uma série de fatores geopolíticos, como a crise do Tigres Asiáticos, voltando a ter um cenário muito parecido com o de 1987-1989, mas ganhando força após esse momento, de novo entre 2000 e 2004, fechando na casa dos US\$ 30,00.

- **2005 - 2014:** Período de maior ascensão e quedas consecutivas no preço do petróleo. Influenciado por eventos geopolíticos, uma crescente demanda global impulsionada pela China, o descobrimento de reservas de petróleo do Pré-Sal no Brasil e a segunda maior crise financeira mundial em 2008.

- **2015 - 2023:** Continuação do período de instabilidade no preço do petróleo, marcado pela crise econômica no Brasil em 2014/15, os impactos da pandemia de Covid-19 em 2020 e conflitos armados na Europa e Oriente Médio. Esse período representa o mais "perturbado" desde o início da série histórica.

- **Previsão:** Consideramos que o modelo se mostrou eficiente na previsão com os hiperparâmetros propostos, apesar de ter sido um período com alguns outliers, o Prophet conseguiu realizar uma boa previsão, gerando um bom grau de confiança.
""")


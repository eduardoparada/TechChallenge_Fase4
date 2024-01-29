import streamlit as st

st.title('Modelo de Previsão - PROPHET :chart_with_upwards_trend:')

container = st.container(border=True)

with container:
    st.header("Desafios do Tech Challenge")
    st.write('''
* Criar um Dashboard interativo com ferramentas à sua escolha.
* Seu Dashboard deve fazer parte de um Storytelling que traga insights relevantes sobre a variação do preço do petróleo, como situações geopolíticas, crises econômicas, demanda global por energia e etc. Isso pode te ajudar com seu modelo. É obrigatório que você traga pelo menos 4 insights neste desafio.
* Criar um modelo de Machine Learning que faça a previsão do preço do petróleo diariamente(lembre-se de time series). Esse modelo deve estar contemplado em seu Storytelling e deve conter o código que você trabalhou, analisando as performances do modelo.
* Criar um plano para fazer o deploy em produção do modelo, com as ferramentas que são necessárias. Faça um MVP do seu modelo em produção uilizando o Streamlit.
''')
    st.header("Sobre o modelo utilizado")
    st.write('''O modelo de previsão selecionado para essa Tech Challenge foi o PROPHET da empresa 
                Meta, o motivo da utilização desse modelo se da pela facilidade da construção e alto poder 
                de previsibilidade.''')
    st.write('''Os arquivos desta análise se encontram no repositório [GitHub](https://github.com/eduardoparada/TechChallenge_Fase4). Lá você irá
                encontrar também o arquivo Tech_Challenge_Fase_4.ipynb, onde foi desenvolvido o racional para implementação no dashboard e também um arquivo
                para consumo de um dashboard alternativo no PowerBI com o nome Dashboard_Tech4 - Grupo 56.pbix''')

# Carrega a imagem
fluxo = 'Fluxo.jpeg'

# Exibe a imagem do fluxograma
st.image(fluxo, channels="RGB", output_format="auto")

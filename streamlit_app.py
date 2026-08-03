import re
import pandas as pd
import fitz
import io
import tempfile
import streamlit as st
import os
from datetime import datetime
from colorama import Fore, Style  # Se você quiser usar cores

#rr
# URL da imagem
image_url = "https://www.fab.mil.br/om/logo/mini/dirad2.jpg"

#Código HTML e CSS para ajustar a largura da imagem para 20% da largura da coluna e centralizar
html_code = f'<div style="display: flex; justify-content: center;"><img src="{image_url}" alt="Imagem" style="width:8vw;"/></div>'

data_geracao = datetime.now().strftime('%Y-%m-%d')
data_geracao2 = datetime.now().strftime('%d/%m/%Y')


# Exibir a imagem usando HTML
st.markdown(html_code, unsafe_allow_html=True)


# Centralizar o texto abaixo da imagem
st.markdown("<h1 style='text-align: center; font-size: 1.5em;'>DIRETORIA DE ADMINISTRAÇÃO DA AERONÁUTICA</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; font-size: 1.2em;'>SUBDIRETORIA DE PAGAMENTO DE PESSOAL</h2>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; font-size: 1em; text-decoration: underline;'>PP1 - DIVISÃO DE DESCONTOS</h3>", unsafe_allow_html=True)

# Texto explicativo
st.write("Desconto Externo Civil - Extração dados PDF SIAPE para SIAFI")

def remove_newlines(text):
    # Expressão regular para lidar com diferentes formas de nova linha
    newline_patterns = [r'\n', r'\r\n', r'\r']

    # Itera sobre os padrões e substitui cada ocorrência por uma string vazia
    for pattern in newline_patterns:
        text = re.sub(pattern, '', text)

    return text

# Função para processar o PDF e exibir o resultado
def processar_pdf(pdf_content):
  
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(pdf_content)
        temp_pdf_path = temp_pdf.name

    pdf_reader = fitz.open(temp_pdf_path)

    if pdf_reader.needs_pass:
        st.error("O arquivo PDF possui senha.Você precisa desbloqueá-lo primeiro.")
        os.remove(temp_pdf_path)
        return
    text = ""
    num_pages = pdf_reader.page_count

    for i in range(num_pages):
        page = pdf_reader.load_page(i)
        text += page.get_text()
        text = remove_newlines(text)
    match = re.search(r'VALOR\s+LIQUIDO\.{3,}:\s*([\d.,]+)', text)

    if match:
        valor_liquido = match.group(1)
        valor_liquido = valor_liquido.replace('.', '').replace(',', '.')
        #st.success(f"Valor Líquido: {valor_liquido}")
    else:
        st.warning("Valor Líquido não encontrado.")

    cnpj_pattern = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
    cnpjs = re.findall(cnpj_pattern, text)
    text_parts = re.split(cnpj_pattern, text)
  
    def formatar_moeda(valor):
        try:
            valor = float(valor)
            return f'R$ {valor:,.2f}'.replace(',', 'temp').replace('.', ',').replace('temp', '.')
        except ValueError:
            return valor  # Em caso de erro, retorna o valor original
   

    def get_binary_file_downloader_html(bin_file, file_label='File', button_label='Save as', key='download_link'):
        bin_str = bin_file.getvalue()
        bin_str = bin_str.decode()
        href = f'data:application/octet-stream;base64,{bin_str}'
        return f'<a href="{href}" download="{file_label}.xml"><button>{button_label}</button></a>'

    data = {'CNPJ': cnpjs, 'Texto_Após_CNPJ': text_parts[1:]}
    df = pd.DataFrame(data)
    df['Empresa'] = df['Texto_Após_CNPJ'].str[:33]
    df['Qtd.Serv'] = df['Texto_Após_CNPJ'].str[38:46]
    df['Valor Bruto'] = df['Texto_Após_CNPJ'].str[46:60]
    df['Rubrica'] = df['Texto_Após_CNPJ'].str[60:65]
    df['tipo'] = df['Texto_Após_CNPJ'].str[86:112]
    df['Qtd.Linha'] = df['Texto_Após_CNPJ'].str[116:122]
    df['ValorLinha'] = df['Texto_Após_CNPJ'].str[127:138]
    df['ValorSerpro'] = df['Texto_Após_CNPJ'].str[208:216]
    df['BCO'] = df['Texto_Após_CNPJ'].str[216:219]
    df['AG'] = df['Texto_Após_CNPJ'].str[221:225]
    df['Conta'] = df['Texto_Após_CNPJ'].str[227:240]
    df['Valor Líquido'] = df['Texto_Após_CNPJ'].str[279:295]

    # Remova os pontos dos milhares e substitua a vírgula pelo ponto
    df['Valor Líquido'] = df['Valor Líquido'].str.replace('.', '').str.replace(',', '.')
    df['ValorLinha'] = df['ValorLinha'].str.replace('.', '').str.replace(',', '.')
    df['ValorSerpro'] = df['ValorSerpro'].str.replace('.', '').str.replace(',', '.')
    df['Qtd.Serv'] = df['Qtd.Serv'].str.replace('.', '').str.replace(',', '.')
    df['Qtd.Linha'] = df['Qtd.Linha'].str.replace('.', '').str.replace(',', '.')
    df['Valor Bruto'] = df['Valor Bruto'].str.replace('.', '').str.replace(',', '.')
    # Converta a coluna para tipo float
    df['Valor Líquido'] = df['Valor Líquido'].astype(float)
    df['ValorSerpro'] = df['ValorSerpro'].astype(float)
    df['Qtd.Serv'] = df['Qtd.Serv'].astype(float)
    df['Qtd.Linha'] = df['Qtd.Linha'].astype(float)
    df['Valor Bruto'] = df['Valor Bruto'].astype(float)
    # Use a função str.replace() para remover "." (ponto), "/" (barra) e "-" (hífen) da coluna 'CNPJ'
    df['CNPJ'] = df['CNPJ'].str.replace('.', '').str.replace('/', '').str.replace('-', '')
    # inserindo rubricas que não devem sair no XML

    valores_para_filtrar = ['34685', '34447', '30846', '34742', '32623']
    ano_atual=datetime.now().year
    mes_atual = datetime.now().strftime('%m')
    # Filtrar o DataFrame
    df_rubricas_excluidas = df[df['Rubrica'].isin(valores_para_filtrar)][['Rubrica','Empresa','Valor Líquido']]
    df_final=df.drop('Texto_Após_CNPJ', axis=1)

    # Obter o índice da primeira linha do DataFrame df_final
    primeiro_indice = df_final.index[0]

    # Obter a posição do índice
    posicao_indice = df_final.index.get_loc(primeiro_indice)

    # Somar 1 à posição do índice
    indice_mais_um = posicao_indice + 1

    #numero de linhas
    
    # Calcula a soma da coluna 'Valor Líquido'
    soma_valor_liquido = df_final['Valor Líquido'].sum()
    # Calcula a diferença entre a soma da coluna 'Valor Líquido' e o valor extraído
    diferenca_valor = soma_valor_liquido - float(valor_liquido)
    # Função para formatar um valor como moeda brasileira (R$)
    

    # Formatação dos valores
    valor_formatado = formatar_moeda(valor_liquido)
    soma_valor_formatado = formatar_moeda(soma_valor_liquido)
    diferenca_valor_formatado = formatar_moeda(diferenca_valor)

    # Exibe os valores formatados
    # Sequência de escape ANSI para cor vermelha
    RED = Fore.RED
    RESET = Style.RESET_ALL
    st.warning(f"Valor Líquido SIAPE: {valor_formatado}")
    st.success(f"Soma da coluna Valor Líquido': {soma_valor_formatado}")
    st.error(f"Diferença: {diferenca_valor_formatado}")
    st.dataframe(df_final)
    st.write("Rubricas que serão excluídas do SIAFI")
    st.dataframe(df_rubricas_excluidas)
    df_final = df_final[~df_final['Rubrica'].isin(valores_para_filtrar)]
    valor_liquido_ajustado = round(df_final['Valor Líquido'].sum(),2)
    st.success(f"Valor Líquido sem as Rubricas excluídas: {formatar_moeda(round(df_final['Valor Líquido'].sum(),2))}")
    st.subheader("Formulário para Geração de Arquivos .XML")
       # Adicione um formulário para capturar variáveis
    with st.form(key='my_form'):
        # Organize os elementos do formulário em duas colunas
        col1, col2 = st.columns(2)

        # Coluna 1
        with col1:
            
            # Criando o campo de entrada de texto com placeholder colorido
            numero_ne = st.text_input("Número da NE: :red[(PARA FL)]", value=str(ano_atual)+'NE', max_chars=12, key='numero_ne')
            numero_sb = st.text_input("Número do Subelemento: :red[(PARA FL)]", max_chars=2, key='numero_sb')
            numero_fl= st.text_input("Número da FL:", max_chars=6, key='numero_fl')
            ano_empenho = st.text_input("Ano de Referência (4 dígitos): :red[(PARA FL)]",  value=str(ano_atual), max_chars=4, key='ano_empenho')
            sequencial_fl = st.text_input("Número Sequencial da FL: :red[(PARA FL)]", max_chars=4, key='sequencial_fl')
            texto_obs = st.text_input("Texto Observação:",value='DESC.EXT.CV', key='texto_obs')
            mes_referencia_cc = st.text_input("Número Mês Referência CC : :red[(PARA FL)]",value=str(mes_atual),max_chars=2, key='mes_referencia_cc')
            
        # Coluna 2
        with col2:
            cpf_responsavel = st.text_input("CPF do Responsável:",max_chars=11, key='cpf_responsavel')
            data_previsao_pagamento = st.date_input("Data de Previsão de Pagamento - (1° dia útil mês seguinte)", key='data_previsao_pagamento')
            data_vencimento = st.date_input("Data Vencimento", key='data_vencimento')
            sequencial_deducao = st.text_input("Número Sequencial da Dedução:", max_chars=4, key='sequencial_deducao')
            processo = st.text_input("Processo:", key='processo')
            ano_referencia_cc = st.text_input("Número Ano Referência CC : :red[(PARA FL)]",value=str(ano_atual),max_chars=4, key='ano_referencia_cc')
        # Botão para enviar o formulário
        submit_button = st.form_submit_button(label='Gerar XML')

    # Remover o arquivo temporário após o processamento
    os.remove(temp_pdf_path)

    # Se o formulário foi enviado, chame a função para exportar XML
    if submit_button:
        exportar_xml(df_final, numero_ne, numero_sb,ano_empenho, cpf_responsavel,data_previsao_pagamento,valor_liquido,data_vencimento,sequencial_fl,sequencial_deducao,texto_obs,processo,indice_mais_um,soma_valor_liquido,mes_referencia_cc,ano_referencia_cc,numero_fl,valor_liquido_ajustado)
        
# Função para exportar o DataFrame para um arquivo XML
def exportar_xml(df_final, numero_ne, numero_sb,ano_empenho, cpf_responsavel, data_previsao_pagamento,valor_liquido,data_vencimento,sequencial_fl,sequencial_deducao,texto_obs,processo,indice_mais_um,soma_valor_liquido,mes_referencia_cc,ano_referencia_cc,numero_fl,valor_liquido_ajustado):
   
    xml_content = f"""
            <sb:arquivo xmlns:ns2="http://services.docHabil.cpr.siafi.tesouro.fazenda.gov.br/" xmlns:sb="http://www.tesouro.gov.br/siafi/submissao">
            <sb:header>
                <sb:codigoLayout>DH001</sb:codigoLayout>
                <sb:dataGeracao>{data_geracao2}</sb:dataGeracao>
                <sb:sequencialGeracao>{sequencial_fl}</sb:sequencialGeracao>
                <sb:anoReferencia>{ano_empenho}</sb:anoReferencia>
                <sb:ugResponsavel>120052</sb:ugResponsavel>
                <sb:cpfResponsavel>{cpf_responsavel}</sb:cpfResponsavel>
            </sb:header>
            <sb:detalhes>
                <sb:detalhe>
                <ns2:CprDhCadastrar>
                    <codUgEmit>120052</codUgEmit>
                    <anoDH>{ano_empenho}</anoDH>
                    <codTipoDH>FL</codTipoDH>
                    <numDH>{numero_fl}</numDH>
                    <dadosBasicos>
                    <dtEmis>{data_geracao}</dtEmis>
                    <dtVenc>{data_vencimento}</dtVenc>
                    <codUgPgto>120052</codUgPgto>
                    <vlr>{valor_liquido_ajustado}</vlr>
                    <txtObser>{texto_obs}</txtObser>
                    <txtProcesso>{processo}</txtProcesso>
                    <dtAteste>{data_vencimento}</dtAteste>
                    <codCredorDevedor>120052</codCredorDevedor>
                    <dtPgtoReceb>{data_previsao_pagamento}</dtPgtoReceb>
                    <docOrigem>
                        <codIdentEmit>120052</codIdentEmit>
                        <dtEmis>{data_geracao}</dtEmis>
                        <numDocOrigem>DESC.EXT.CV</numDocOrigem>
                        <vlr>{valor_liquido_ajustado}</vlr>
                    </docOrigem>
                    </dadosBasicos>
                    <pco>
                    <numSeqItem>{indice_mais_um}</numSeqItem>
                    <codSit>DFL001</codSit>
                    <codUgEmpe>120052</codUgEmpe>
                    <pcoItem>
                        <numSeqItem>1</numSeqItem>
                        <numEmpe>{numero_ne}</numEmpe>
                        <codSubItemEmpe>{numero_sb}</codSubItemEmpe>
                        <indrLiquidado>1</indrLiquidado>
                        <vlr>{valor_liquido_ajustado}</vlr>
                        <numClassA>311110100</numClassA>
                    </pcoItem>
                    </pco>
                    <centroCusto>
                    <numSeqItem>1</numSeqItem>
                    <codCentroCusto>310200</codCentroCusto>
                    <mesReferencia>{mes_referencia_cc}</mesReferencia>
                    <anoReferencia>{ano_referencia_cc}</anoReferencia>
                    <codUgBenef>120052</codUgBenef>
                    <codSIORG>2332</codSIORG>
                    <relPcoItem>
                        <numSeqPai>1</numSeqPai>
                        <numSeqItem>1</numSeqItem>
                        <vlr>{valor_liquido_ajustado}</vlr>
                    </relPcoItem>
                    </centroCusto>
                </ns2:CprDhCadastrar>
                </sb:detalhe>
            </sb:detalhes>
            <sb:trailler>
                <sb:quantidadeDetalhe>1</sb:quantidadeDetalhe>
            </sb:trailler>
            </sb:arquivo>"""
    
    xml_content_modelo2 = f"""
                <sb:arquivo xmlns:sb="http://www.tesouro.gov.br/siafi/submissao" xmlns:cpr="http://services.docHabil.cpr.siafi.tesouro.fazenda.gov.br/">
                <sb:header>
                    <sb:codigoLayout>DH002</sb:codigoLayout>
                    <sb:dataGeracao>{data_geracao2}</sb:dataGeracao>
                    <sb:sequencialGeracao>{sequencial_deducao}</sb:sequencialGeracao>
                    <sb:anoReferencia>{ano_empenho}</sb:anoReferencia>
                    <sb:ugResponsavel>120052</sb:ugResponsavel>
                    <sb:cpfResponsavel>{cpf_responsavel}</sb:cpfResponsavel>
                </sb:header>
                <sb:detalhes>
                    """
    # Itera sobre as linhas do DataFrame e adiciona as informações de dedução
    for seq_item, (index, row) in enumerate(df_final.iterrows(), start=1):
        # Definição de codTipoOB, conta, banco_fab e txtCit de acordo com os CNPJs específicos
        if row['CNPJ'] == '00000000000191':
            codTipoOB = 'OBF'
            txtCit = '120052ECFP310270014'
            conta = 'FOPAG'
            banco_fab = '002'
        elif row['CNPJ'] == '00360305000104':
            codTipoOB = 'OBF'
            txtCit = '120052ECFPC128910'
            conta = 'FOPAG'
            banco_fab = '002'
        else:
            codTipoOB = 'OBC'
            conta = 'UNICA'
            banco_fab = ''
            txtCit = None

    # Construção do XML com condição para <txtCit>
        numDomiBancFavo = f"""<numDomiBancFavo>
                                <banco>{row['BCO']}</banco>
                                <agencia>{row['AG']}</agencia>
                                <conta>{conta if codTipoOB == 'OBF' else row['Conta']}</conta>
                            </numDomiBancFavo>"""

        numDomiBancPgto = f"""<numDomiBancPgto>
                                {f'<banco>{banco_fab}</banco>' if banco_fab else ''}
                                <conta>UNICA</conta>
                            </numDomiBancPgto>"""

        # Somente incluir a tag <txtCit> se codTipoOB for 'OBF' e txtCit não for None
        if codTipoOB == 'OBF' and txtCit is not None:
            txtCit_tag = f"<txtCit>{txtCit}</txtCit>"
        else:
            txtCit_tag = ""  # Não inclui <txtCit> no XML

        

        xml_content_modelo2 += f"""<sb:detalhe>
                        <cpr:CprDhAlterarDHIncluirItens>
                            <codUgEmit>120052</codUgEmit>
                            <anoDH>{ano_empenho}</anoDH>
                            <codTipoDH>FL</codTipoDH>
                            <numDH>{numero_fl}</numDH>
                            <dtEmis>{data_geracao}</dtEmis>
                            <txtMotivo>{texto_obs}</txtMotivo>
                                <deducao>
                                    <numSeqItem>{seq_item}</numSeqItem>
                                    <codSit>DOB005</codSit>
                                    <dtVenc>{data_vencimento}</dtVenc>
                                    <dtPgtoReceb>{data_previsao_pagamento}</dtPgtoReceb>
                                    <codUgPgto>120052</codUgPgto>
                                    <vlr>{f'{row["Valor Líquido"]:.2f}'}</vlr>
                                    <txtInscrA>{row['CNPJ']}</txtInscrA>
                                    <numClassA>218810199</numClassA>
                                    <predoc>
                                        <txtObser>{texto_obs}</txtObser>
                                        <predocOB>
                                            <codTipoOB>{codTipoOB}</codTipoOB>
                                            <codCredorDevedor>{row['CNPJ']}</codCredorDevedor>
                                            <txtCit>{txtCit}</txtCit>
                                            {numDomiBancFavo}
                                            {numDomiBancPgto}
                                        </predocOB>
                                    </predoc>
                                </deducao>                                
                </cpr:CprDhAlterarDHIncluirItens>
            </sb:detalhe>"""

                      
    xml_content_modelo2 += """
        </sb:detalhes>
        <sb:trailler>
            <sb:quantidadeDetalhe>linhas_totais</sb:quantidadeDetalhe>
        </sb:trailler>
    </sb:arquivo>
        """
    xml_content_modelo2 = xml_content_modelo2.replace('linhas_totais', str(len(df_final)))
    # Remover apenas as tags <txtCit> cujo valor seja "None"
    xml_content = re.sub(r'<txtCit>None</txtCit>', '', xml_content)
    xml_content_modelo2 = re.sub(r'<txtCit>None</txtCit>', '', xml_content_modelo2)
    st.success(f"Arquivo XML com DataFrame gerado com sucesso.") 
    # Adiciona um botão de download para o arquivo XML
    # Cria um objeto BytesIO para armazenar o conteúdo do XML
    xml_io = io.BytesIO(xml_content.encode())

    # Adiciona um botão de download para o arquivo XML
    st.download_button(
        label="Baixar XML para FL",
        data=xml_io,
        key='download_button',
        file_name=f"xml_FL_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xml",
        mime="text/xml"
    )
    st.download_button(
        label="Baixar XML para DEDUÇÃO",
        data=io.BytesIO(xml_content_modelo2.encode()),
        key='download_button_modelo2',
        file_name=f"xml_deducao_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xml",
        mime="text/xml"
    )

# Função auxiliar para criar um link de download

# Solicitar ao usuário o upload do arquivo PDF
uploaded_file = st.file_uploader("Faça o UPLOAD do arquivo PDF do SIAPE gerado na transação GRCOCGRECO", type="pdf")

# Obter o conteúdo do arquivo PDF
if uploaded_file:
    pdf_content = uploaded_file.read()
    processar_pdf(pdf_content)

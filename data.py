import pandas as pd
import numpy as np

from plotly import graph_objects as go
import plotly.figure_factory as ff
import plotly.express as px


#servidores 
servidores = pd.read_csv('servidores_federais.csv')
servidores['first_name'] = servidores['Nome'].apply(lambda x: x.strip().split()[0])
#nomes
nomes = pd.read_csv('nomes.csv')

#merge
merged = pd.merge(servidores, nomes[['first_name','classification']], on='first_name')
merged.rename(columns={'first_name': 'PrimeiroNome', 'classification': 'Sexo'}, inplace=True)


colors = ['#ff8503','#4fdb54','#49f2e7','#593feb','#b31ff2','#f5205c']
# retornar contagem de servidores em cada tipo
def contagem_servidores():
    cont = merged.groupby('Tipo')[['Tipo']].count()
    # ax = go.Bar(
    #     name="bar0",
    #     x=cont.index,
    #     y=cont['Tipo'],
    #     marker={'color':colors[1:3]},
    #     offsetgroup=0,
    # )
    
    data1 = go.Indicator(
        mode="number",
        value=merged.shape[0],
        title="TOTAL SERVIDORES FEDERAIS",)

    layout1 = dict( 
            showlegend = False,
            height = 500,
            width = 500,
            font={'color': colors[0]}
            )

    fig1 = dict(data = [data1], layout = layout1)
    #-------------------------------------------
    data2 = go.Pie(labels=cont.index, values=cont.Tipo.values, hole=.3,
                textinfo='label+percent',insidetextorientation='radial',
                marker_colors=colors[1:3] ) 

    layout2 = dict(title = 'PROPORÇÃO POR TIPO DE SERVIDOR', 
            showlegend = False,
            height = 500,
            width = 500,
            font={'color': colors[0]}
            )

    fig2 = dict(data = [data2], layout = layout2)

    return fig1,fig2


# retornar contagem de sexo por tipo
def contagem_por_sexo_servidores():

    contagem_sexo = merged.groupby(['Tipo','Sexo'])[['Sexo']].count().unstack()
    contagem_sexo.columns = [tup[1] for tup in contagem_sexo.columns]
    contagem_sexo = contagem_sexo.transpose()

    data = [
        go.Bar(
            name="Servidores civis",
            x=contagem_sexo.index,
            y=contagem_sexo['Civil'],
            marker={'color':colors[1]},
            offsetgroup=0,
            ),
        go.Bar(
            name="Servidores militares",
            x=contagem_sexo.index,
            y=contagem_sexo['Militar'],
            marker={'color':colors[2]},
            offsetgroup=1,
        ),
    ]
    
    layout = dict(title = 'CONTAGEM DE SEXO POR TIPO', 
            showlegend = True,
            height = 500,
            width = 700,
            font={'color': colors[3]}
            )

    fig = dict(data = data, layout = layout)
   
    return fig

# retornar media salarial entre sexos
def media_salarial_sexos():
    media_salarial_civil = merged[merged.Tipo =='Civil'].groupby('Sexo')[['RemuneracaoBruta','RemuneracaoFinal']].mean()
    media_salarial_militar = merged[merged.Tipo =='Militar'].groupby('Sexo')[['RemuneracaoBruta','RemuneracaoFinal']].mean()
    
    hist_civil =  merged[merged.Tipo =='Civil'][['RemuneracaoBruta','RemuneracaoFinal','Sexo']].dropna()

    # hist_militar = merged[merged.Tipo =='Militar'][['RemuneracaoBruta','RemuneracaoFinal']]

    data1 = [
        go.Bar(
            name="Remuneração bruta",
            x=media_salarial_civil.index,
            y=media_salarial_civil['RemuneracaoBruta'],
            marker={'color':colors[1]},
            offsetgroup=0,
            ),
        go.Bar(
            name="Remuneração final",
            x=media_salarial_civil.index,
            y=media_salarial_civil['RemuneracaoFinal'],
            marker={'color':colors[2]},
            offsetgroup=1,
        ),
    ]
    layout1 = dict(title = 'MEDIA SALARIAL POR SEXO (R$): CIVIL', 
            showlegend = True,
            height = 500,
            width = 700,
            font={'color': colors[4]}
            )

    fig1 = dict(data = data1, layout = layout1)
    # -------------------------------------------------------
    data2 = [
        go.Bar(
            name="Remuneração bruta",
            x=media_salarial_militar.index,
            y=media_salarial_militar['RemuneracaoBruta'],
            marker={'color':colors[1]},
            offsetgroup=0,
            ),
        go.Bar(
            name="Remuneração final",
            x=media_salarial_militar.index,
            y=media_salarial_militar['RemuneracaoFinal'],
            marker={'color':colors[2]},
            offsetgroup=1,
        ),
    ]
    layout2 = dict(title = 'MEDIA SALARIAL POR SEXO (R$): MILITAR', 
            showlegend = True,
            height = 500,
            width = 700,
            font={'color': colors[4]}
            )

    fig2 = dict(data = data2, layout = layout2)

    # -------------------------------------------------------
    data3 = []

    for c,sexo in enumerate(hist_civil.Sexo.unique()):
        data3.append(    
            go.Histogram(
                x=hist_civil[hist_civil.Sexo == sexo].RemuneracaoBruta,
                opacity=.75,
                name=sexo,
                histnorm='density',
                xbins=dict(
                        start=np.min(hist_civil[hist_civil.Sexo == sexo].RemuneracaoFinal),
                        end=np.max(hist_civil[hist_civil.Sexo == sexo].RemuneracaoFinal),
                        size=700),
                marker={'color':colors[c+1]}

            )
        )   
    layout3 = dict(title = 'DISTRIBUIÇÃO DE SALÁRIOS BRUTOS ENTRE SEXOS: CIVIL', 
            showlegend = True,
            height = 500,
            width = 800,
            barmode='stack',
            font={'color': colors[5]}
            )

    fig3 = dict(data = data3, layout = layout3)
    # -------------------------------------------------------
    data4 = []

    for c,sexo in enumerate(hist_civil.Sexo.unique()):
        data4.append(    
            go.Histogram( 
                x=hist_civil[hist_civil.Sexo == sexo].RemuneracaoFinal,
                opacity=.85,
                name=sexo,
                histnorm='density',
                xbins=dict(
                        start=np.min(hist_civil[hist_civil.Sexo == sexo].RemuneracaoFinal),
                        end=np.max(hist_civil[hist_civil.Sexo == sexo].RemuneracaoFinal),
                        size=700),
                marker={'color':colors[c+1]}

            )
        )   
    layout4 = dict(title = 'DISTRIBUIÇÃO DE SALÁRIOS FINAIS ENTRE SEXOS: CIVIL', 
            showlegend = True,
            height = 500,
            width = 800,
            barmode='stack',
            font={'color': colors[5]}
            )

    fig4 = dict(data = data4, layout = layout4)

    return fig1,fig2,fig3,fig4



# retornar media salarial por orgaos
def media_salarial_orgaos():
    orgaos_civil = merged.groupby(['Tipo','orgaoServidorExercicio'])[['RemuneracaoBruta']].mean().loc['Civil']
    orgaos_civil.sort_values(by = 'RemuneracaoBruta', ascending=False, inplace=True)
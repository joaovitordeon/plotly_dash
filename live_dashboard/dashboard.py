#!/usr/bin/env python
# coding: utf-8

import pyodbc
import pandas as pd
import json
import requests
import time
from urllib.parse import quote_plus

import datetime

import dash
from dash import dcc
from dash import html

import plotly.express as px
import plotly
import plotly.graph_objects as go
import matplotlib.pyplot as plt

from dash.dependencies import Input, Output


def connection(): #conect to DB
    global CURSOR
    global CNXN

    try:
        server = '187.60.66.245,81'
        database = 'Prospects'
        username = 'Devops'
        password = '4ec96adb9cc39333f3d2024b28f2503f'
    
        CNXN = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
        CURSOR = CNXN.cursor()
    
    except Exception as e:
        raise Exception('conect to database Error >>>>',e)

    else:
        return 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password

def execute(sql):
    CURSOR.execute(sql)
    CNXN.commit()
    
def fetch(sql):
    return pd.read_sql_query(sql, CNXN)

def get_calls(data):
    token = "d35a65d1-c1db-47fc-aa93-8e484d3a70e6"

    headers = {
      "Content-Type": "application/json",
      "token_exact": token
    }
    
    get = requests.get(f"""https://api.exactspotter.com/v3/callsHistory?$filter=year(startDate) eq {data.split('-')[0]} 
                            and month(startDate) eq {data.split('-')[1]} and day(startDate) eq {data.split('-')[-1]} """, 
                      headers=headers)
    
    js = get.content.decode('utf-8').replace('\n','')
    js = json.loads(js)
    
    return js['value']


def get_calls_today():
    '''
    Função para pegar as chamadas feitas pela exact sales no dia atual
    '''
    dt = datetime.datetime.today()
    date = f"{dt.year}-{str(dt.month).zfill(2)}-{str(dt.day).zfill(2)}"

    df = get_calls(date)
    df = pd.DataFrame(df)

    df.fillna('', inplace=True)
    df.replace(False,0, inplace=True)
    df.replace(True,1, inplace=True)
    df.startDate = pd.to_datetime(df.startDate).astype(str)
    df.startDate = df.startDate.apply(lambda x: x.split('.')[0].split('+')[0].replace(' ','T'))
    df.endDate = pd.to_datetime(df.endDate).astype(str).apply(lambda x: x.split('.')[0])
    df.endDate = df.endDate.apply(lambda x: x.split('.')[0].split('+')[0].replace(' ','T'))
    df.replace('NaT','', inplace=True)
    df.fillna('', inplace=True)
    df.talkingDurationSeconds = df.talkingDurationSeconds.replace('',0)
    df.talkingDurationSeconds = df.talkingDurationSeconds.astype(float)
    
    df.userEmail.replace({'gustavo.pereira@inovall.com.br':'Gustavo',
                          'contato@inovall.com.br':'Fabricio'} , 
                         inplace=True)

    return df


def get_stage(op: str):
    '''
    função para capturar os leads que estao na etapa de apresentação no dia atual
    '''
    token = "d35a65d1-c1db-47fc-aa93-8e484d3a70e6"

    headers = {
      "Content-Type": "application/json",
      "token_exact": token
    }
    
    dt = datetime.datetime.today()
    data = f"{dt.year}-{str(dt.month).zfill(2)}-{str(dt.day).zfill(2)}"
    
    if op == 'dia':    
        get = requests.get(f"""https://api.exactspotter.com/v3/Leads?$filter= stage eq 'Apresentação/Agendamento' 
                            and year(updateDate) eq {data.split('-')[0]} 
                            and month(updateDate) eq {data.split('-')[1]} 
                            and day(updateDate) eq {data.split('-')[-1]} """, 
                            headers=headers)

        js = get.content.decode('utf-8').replace('\n','')
        js = json.loads(js)
        
        df = pd.DataFrame(js['value'])

    elif op == 'mes':
        get = requests.get(f"""https://api.exactspotter.com/v3/Leads?$filter= stage eq 'Apresentação/Agendamento' 
                            and year(updateDate) eq {data.split('-')[0]} 
                            and month(updateDate) eq {data.split('-')[1]} """, 
                            headers=headers)

        js = get.content.decode('utf-8').replace('\n','')
        js = json.loads(js)
        
        df = pd.DataFrame(js['value'])
    
    else:
        df = pd.DataFrame()

    try:
        res = df.lead.nunique()
    except:
        return 0
    else:
        return res
        

def update_data():
    '''
    Função para atualizar os dados a serem utilizados pelos gráficos
    '''
    global ligs_hoje, ligs_mes, n_ligacoes_hoje, n_ligacoes_mes, tempo_total_hoje, tempo_total_mes, n_reunioes_hoje, n_reunioes_mes
 
    #ligacoes feitas no dia atual
    ligs_hoje = get_calls_today()
    ligs_hoje.columns = [c.lower().capitalize() for c in ligs_hoje.columns]
    ligs_hoje['Callhour'] = pd.to_datetime(ligs_hoje.Startdate).dt.hour
    ligs_hoje['Day'] = pd.to_datetime(ligs_hoje.Startdate).dt.day

    #ligacoes feitas no mes atual
    ligs_mes = fetch("""SELECT * FROM ExactCallLog
                    WHERE MONTH(CONVERT(DATE,startDate)) = MONTH(CONVERT(DATE,getdate()))
                    AND YEAR(CONVERT(DATE,startDate)) = YEAR(CONVERT(DATE,getdate()))
                    """)
    ligs_mes.columns = [c.lower().capitalize() for c in ligs_mes.columns]
    ligs_mes.Useremail.replace({'gustavo.pereira@inovall.com.br':'Gustavo',
                            'contato@inovall.com.br':'Fabricio'} , 
                            inplace=True)
    ligs_mes['Callhour'] = pd.to_datetime(ligs_mes.Startdate).dt.hour
    ligs_mes['Day'] = pd.to_datetime(ligs_mes.Startdate).dt.day
    ligs_mes = pd.concat([ligs_mes,ligs_hoje], axis=0)

    # numeros de ligaçoes unicas de cada SDR no dia
    n_ligacoes_hoje = ligs_hoje.pivot_table(index='Useremail', columns='Callhour', values='Leadid', aggfunc='nunique').fillna(0)
    n_ligacoes_hoje.columns = [str(c).zfill(2) for c in n_ligacoes_hoje.columns]

    # numeros de ligaçoes unicas de cada SDR no mes
    n_ligacoes_mes = ligs_mes.pivot_table(index='Useremail', columns='Day', values='Leadid', aggfunc='nunique').fillna(0)
    n_ligacoes_mes.columns = [str(c).zfill(2) for c in n_ligacoes_mes.columns]

    # tempo em minutos de ligações de cada SDR no dia
    tempo_total_hoje = (ligs_hoje.groupby(['Useremail'])[['Talkingdurationseconds']].sum()/60).round(2)
    tempo_total_hoje.columns = ['Talkingdurationminutes']

    # tempo em minutos de ligações de cada SDR no mes
    tempo_total_mes = (ligs_mes.groupby(['Useremail'])[['Talkingdurationseconds']].sum()/60).round(2)
    tempo_total_mes.columns = ['Talkingdurationminutes']

    # numero de reunioes marcadas no dia
    n_reunioes_hoje = get_stage('dia')

    # numero de reunioes marcadas no mes
    n_reunioes_mes = get_stage('mes')

#------------------------------------MAIN------------------------------------

connection()

# analise diaria: 'dia' / analise mensal : 'mes'
MODE='dia'

ligs_hoje =  None
ligs_mes = None 
n_ligacoes_hoje = None
n_ligacoes_mes = None
tempo_total_hoje = None
tempo_total_mes = None
n_reunioes_hoje = None
n_reunioes_mes = None

update_data()

#-----------------------------------------------
plot1 = px.bar(n_ligacoes_hoje.T, x = n_ligacoes_hoje.columns, y = n_ligacoes_hoje.index ,barmode='group',
               template='plotly_white', labels={'value': 'Ligações', 'index':'hora'},
               color_discrete_sequence = px.colors.qualitative.Plotly,
               )

plot1.update_layout(
    title={
        'text': "Quantidade de ligações únicas no dia",
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'})

plot1.update(layout_coloraxis_showscale=False)
plot1.update_yaxes(tickprefix='<b>', ticksuffix='<b>')
plot1.update_xaxes(tickprefix='<b>', ticksuffix='<b>', tickangle=0)

plot1.layout.update(margin=dict(l=20,r=20,b=20,t=30))
plot1.add_hline(y=6, line_width=4, line_dash="dot", line_color="grey", 
                annotation_text="Meta de ligações por hora", 
                annotation_position="top left",
                annotation_font_size=14,
                annotation_font_color="grey")


#-----------------------------------------------
plot2 = px.bar(tempo_total_hoje,
               template='plotly_white', labels={'value': 'Tempo em minutos', 'Useremail':''},
               color_discrete_sequence = px.colors.qualitative.Plotly,
               color = tempo_total_hoje.index,
               )

plot2.update_layout(
    title={
        'text': "Total de minutos em ligações no dia",
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'})

texts = tempo_total_hoje.values
for i, t in enumerate(texts):
    plot2.data[i].text = t
    plot2.data[i].textposition = 'outside'

plot2.update(layout_coloraxis_showscale=False)
plot2.update_yaxes(tickprefix='<b>', ticksuffix='<b>')
plot2.update_xaxes(tickprefix='<b>', ticksuffix='<b>', tickangle=0)
plot2.update_traces(width=.2)

plot2.layout.update(margin=dict(l=20,r=20,b=20,t=50))
plot2.add_hline(y=120, line_width=4, line_dash="dot", line_color="grey", 
                annotation_text="Meta de minutos falados", 
                annotation_position="top right",
                annotation_font_size=14,
                annotation_font_color="grey")

#-----------------------------------------------
plot3 = go.Figure(go.Indicator(
    mode = "number+delta",
    value = tempo_total_hoje.sum().values[0],
    #domain = {'x': [0, 0.5], 'y': [0, 0.5]},
    delta = {'reference': 240, 'relative': False, 'position' : "bottom"},
    title = {"text": "Total de ligações no dia<br>"},
    )
)
#-----------------------------------------------

plot4 = go.Figure(go.Indicator(
    mode = "number+delta",
    value = n_reunioes_hoje,
    #domain = {'x': [0, 0.5], 'y': [0, 0.5]},
    delta = {'reference': 3, 'relative': False, 'position' : "bottom"},
    title = {"text": "Total de reuniões <br> marcadas no dia<br>"},
    )
)

#-----------------------------------------------
plot5 = go.Figure(go.Indicator(
    mode = "number+delta",
    value = int(n_ligacoes_hoje.sum().sum()),
    #domain = {'x': [0, 0.5], 'y': [0, 0.5]},
    delta = {'reference': int(n_ligacoes_hoje.sum().sum()), 'relative': False, 'position' : "bottom"},
    title = {"text": "Total de ligações únicas <br> feitas no dia<br>"},
    )
)


#-----------------------------------------------------DASH-----------------------------------------------------------

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    html.Div(
        children=[
            dcc.RadioItems(
                id = 'radio_item',
                options=[
                    {'label': 'Análise diária', 'value': 'dia'},
                    {'label': 'Análise mensal', 'value': 'mes'},
                ],
                value='dia',
                labelStyle={'width': '8%', 'display': 'inline-block'},
            ),

            html.Div(
                children = dcc.Graph(
                    id = 'gauge_total_calls',
                    figure = plot5,
                    #config={"displayModeBar": False},
                ),
                style={'width': '33%', 'display': 'inline-block'},
            ),

            html.Div(
                children = dcc.Graph(
                    id = 'gauge_meetings',
                    figure = plot4,
                    #config={"displayModeBar": False},
                ),
                style={'width': '33%', 'display': 'inline-block'},
            ),

            html.Div(
                children = dcc.Graph(
                    id = 'gauge_time_calls',
                    figure = plot3,
                    #config={"displayModeBar": False},
                ),
                style={'width': '33%', 'display': 'inline-block'},
            ),

            html.Div(
                children = dcc.Graph(
                    id = 'total_calls',
                    figure = plot1,
                  #  config={"displayModeBar": False},
                ),
                style={'width': '70%', 'display': 'inline-block'},
            ),

            html.Div(
                children = dcc.Graph(
                    id = 'time_calls',
                    figure = plot2,
                    #config={"displayModeBar": False},
                ),
                style={'width': '30%', 'display': 'inline-block'},
            ),

            dcc.Interval(
                id='interval-component',
                interval=60*60*1000, # in milliseconds
                n_intervals=0
            ),
        ]
    )
)

# Multiple components can update everytime interval gets fired.
@app.callback([Output('total_calls', 'figure'),
               Output('time_calls', 'figure'), 
               Output('gauge_time_calls', 'figure'), 
               Output('gauge_meetings', 'figure'),
               Output('gauge_total_calls', 'figure')],
              [Input('radio_item', 'value'),Input('interval-component', 'n_intervals')])
def update_graph_to_month(radio_item_val , n):
    
    global MODE, n_ligacoes_mes, tempo_total_mes, n_reunioes_mes, n_ligacoes_hoje, tempo_total_hoje, n_reunioes_hoje

    MODE = radio_item_val

    if MODE == 'mes':
        #------------------------------------------------------------
        fig = px.bar(n_ligacoes_mes.T, x = n_ligacoes_mes.columns, y = n_ligacoes_mes.index ,barmode='group',
                template='plotly_white', labels={'value': 'Ligações', 'index':'dia'},
                color_discrete_sequence = px.colors.qualitative.Plotly,
                )

        fig.update_layout(
            title={
                'text': f"Quantidade de ligações únicas no mes",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'})

        fig.update(layout_coloraxis_showscale=False)
        fig.update_yaxes(tickprefix='<b>', ticksuffix='<b>')
        fig.update_xaxes(tickprefix='<b>', ticksuffix='<b>', tickangle=0)

        fig.layout.update(margin=dict(l=20,r=20,b=20,t=30))


        #------------------------------------------------
        fig2 = px.bar(tempo_total_mes,
                template='plotly_white', labels={'value': 'Tempo em minutos', 'Useremail':''},
                color_discrete_sequence = px.colors.qualitative.Plotly,
                color = tempo_total_mes.index,
                )

        fig2.update_layout(
            title={
                'text': f"Total de minutos em ligações no mes",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'})

        texts = tempo_total_mes.values
        for i, t in enumerate(texts):
            fig2.data[i].text = t
            fig2.data[i].textposition = 'outside'

        fig2.update(layout_coloraxis_showscale=False)
        fig2.update_yaxes(tickprefix='<b>', ticksuffix='<b>')
        fig2.update_xaxes(tickprefix='<b>', ticksuffix='<b>', tickangle=0)
        fig2.update_traces(width=.2)

        fig2.layout.update(margin=dict(l=20,r=20,b=20,t=50))


        #----------------------------------
        fig3 = go.Figure(go.Indicator(
                    mode = "number+delta",
                    value = tempo_total_mes.sum().values[0],
                    #domain = {'x': [0, 0.5], 'y': [0, 0.5]},
                    delta = {'reference': 4800, 'relative': False, 'position' : "bottom"},
                    title = {"text": "Tempo em ligações no mês <br> (minutos)<br>"},
                )
        )

        #--------------------------------------------
        fig4 = go.Figure(go.Indicator(
                    mode = "number+delta",
                    value = n_reunioes_mes,
                    #domain = {'x': [0, 0.5], 'y': [0, 0.5]},
                    delta = {'reference': 60, 'relative': False, 'position' : "bottom"},
                    title = {"text": "Total de reuniões <br> marcadas no mês<br>"},
            )
        )

        #-------------------------------------------
        fig5 = go.Figure(go.Indicator(
                    mode = "number+delta",
                    value = int(n_ligacoes_mes.sum().sum()),
                    #domain = {'x': [0, 0.5], 'y': [0, 0.5]},
                    delta = {'reference': int(n_ligacoes_mes.sum().sum()), 'relative': False, 'position' : "bottom"},
                    title = {"text": "Total de ligações únicas <br> feitas no mês<br>"},
            )
        )

        return [fig, fig2, fig3, fig4, fig5]

    else:
        # update_data
        update_data()

        # upgrade graphs with new updated data
        #------------------------------------------------------------
        fig = px.bar(n_ligacoes_hoje.T, x = n_ligacoes_hoje.columns, y = n_ligacoes_hoje.index ,barmode='group',
                template='plotly_white', labels={'value': 'Ligações', 'index':'hora'},
                color_discrete_sequence = px.colors.qualitative.Plotly,
                )

        fig.update_layout(
            title={
                'text': f"Quantidade de ligações únicas no dia             | n° {n}",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'})

        fig.update(layout_coloraxis_showscale=False)
        fig.update_yaxes(tickprefix='<b>', ticksuffix='<b>')
        fig.update_xaxes(tickprefix='<b>', ticksuffix='<b>', tickangle=0)

        fig.layout.update(margin=dict(l=20,r=20,b=20,t=30))
        fig.add_hline(y=6, line_width=4, line_dash="dot", line_color="grey", 
                        annotation_text="Meta de ligações por hora", 
                        annotation_position="top left",
                        annotation_font_size=14,
                        annotation_font_color="grey")

        #------------------------------------------------
        fig2 = px.bar(tempo_total_hoje,
                template='plotly_white', labels={'value': 'Tempo em minutos', 'Useremail':''},
                color_discrete_sequence = px.colors.qualitative.Plotly,
                color = tempo_total_hoje.index,
                )

        fig2.update_layout(
            title={
                'text': f"Total de minutos em ligações no dia              | n° {n}",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'})

        texts = tempo_total_hoje.values
        for i, t in enumerate(texts):
            fig2.data[i].text = t
            fig2.data[i].textposition = 'outside'

        fig2.update(layout_coloraxis_showscale=False)
        fig2.update_yaxes(tickprefix='<b>', ticksuffix='<b>')
        fig2.update_xaxes(tickprefix='<b>', ticksuffix='<b>', tickangle=0)
        fig2.update_traces(width=.2)

        fig2.layout.update(margin=dict(l=20,r=20,b=20,t=50))
        fig2.add_hline(y=120, line_width=4, line_dash="dot", line_color="grey", 
                        annotation_text="Meta de minutos falados", 
                        annotation_position="top right",
                        annotation_font_size=14,
                        annotation_font_color="grey")


        #----------------------------------
        fig3 = go.Figure(go.Indicator(
                    mode = "number+delta",
                    value = tempo_total_hoje.sum().values[0],
                    #domain = {'x': [0, 0.5], 'y': [0, 0.5]},
                    delta = {'reference': 240, 'relative': False, 'position' : "bottom"},
                    title = {"text": "Tempo em ligações no dia <br> (minutos)<br>"},
                )
        )

        #--------------------------------------------
        fig4 = go.Figure(go.Indicator(
                    mode = "number+delta",
                    value = n_reunioes_hoje,
                    #domain = {'x': [0, 0.5], 'y': [0, 0.5]},
                    delta = {'reference': 3, 'relative': False, 'position' : "bottom"},
                    title = {"text": "Total de reuniões <br> marcadas no dia<br>"},
            )
        )   
        
        #-------------------------------------------
        fig5 = go.Figure(go.Indicator(
                    mode = "number+delta",
                    value = int(n_ligacoes_hoje.sum().sum()),
                    #domain = {'x': [0, 0.5], 'y': [0, 0.5]},
                    delta = {'reference': int(n_ligacoes_hoje.sum().sum()), 'relative': False, 'position' : "bottom"},
                    title = {"text": "Total de ligações únicas <br> feitas no dia<br>"},
            )
        )

        return [fig, fig2, fig3, fig4, fig5]

if __name__ == '__main__':
    app.run_server(debug=True)
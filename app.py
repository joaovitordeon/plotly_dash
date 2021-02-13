import dash
import dash_core_components as dcc
import dash_html_components as dhtml


from matplotlib import pyplot as plt
from plotly.offline import init_notebook_mode,plot
import plotly.graph_objs as go
import plotly.tools as tls

from data import contagem_servidores, contagem_por_sexo_servidores, media_salarial_sexos

init_notebook_mode(connected=True)

#sets
external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
]

#initiaize ---------------------------------------------------------
app =  dash.Dash(__name__,external_stylesheets=external_stylesheets)
app.css.config.serve_locally = False

#get data -----------------------------------------------------------
indicador,contagem_tipo = contagem_servidores()

contagem_sexo_por_tipo = contagem_por_sexo_servidores()

media_salarial_civil, media_salarial_militar, hist_rem_bruta, hist_rem_final = media_salarial_sexos()

# app layout
app.layout = dhtml.Div([

    dhtml.Div(dhtml.H1(children="Análise de servidores federais",  style={'textAlign': 'center', 'color': '#3464eb'})),

    dhtml.Div([
        dhtml.Div([
            dcc.Graph(id = 'indicator',
                    figure = indicador
            ),
        ],className="six columns"),
        dhtml.Div([
            dcc.Graph(id = 'contagem por tipo',
                    figure = contagem_tipo
            )
        ],className="six columns"),

    ],className = 'row'),

    dhtml.Div([
        dhtml.Div([
            dhtml.Div([
                dcc.Graph(id = 'contagem de sexo por tipo',
                        figure = contagem_sexo_por_tipo
                ),
            ])
        ]),
    ]),

    dhtml.Div([
        dhtml.Div([
            dcc.Graph(id = 'media salarial por tipo civil',
                    figure = media_salarial_civil
            ),
        ],className="six columns"),
        dhtml.Div([
            dcc.Graph(id = 'media salarial por tipo Militar',
                    figure = media_salarial_militar
            )
        ],className="six columns"),

    ],className = 'row'),

    dhtml.Div([
        dhtml.Div([
            dcc.Graph(id = 'hist bruta',
                    figure = hist_rem_bruta
            ),
        ],className="six columns"),
        dhtml.Div([
            dcc.Graph(id = 'hist final',
                    figure = hist_rem_final
            )
        ],className="six columns"),

    ],className = 'row'),
])


# run
if __name__ == "__main__":
    app.run_server(debug=True)
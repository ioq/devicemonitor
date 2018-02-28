import dash
from dash.dependencies import Input, Output, State, Event
import dash_core_components as dcc
import dash_html_components as html
import datetime
import plotly.graph_objs as go
import numpy as np
import threading
import queue
import subprocess
import time
import re
import pandas as pd
from deviceinfo import Meminfo

CSS_MDL_BUTTON_CLASS = "mdl-button mdl-js-button mdl-button--raised mdl-js-ripple-effect mdl-button--accent"

app = dash.Dash()
app.layout = html.Div([
    html.Div([
        dcc.Graph(id='live-graph'),
        dcc.Interval(id='wind-speed-update', interval=1000),
        html.Button('PAUSE', id='pause-button',
            className=CSS_MDL_BUTTON_CLASS, 
            style={
                "position": "relative",
                "float": "right",
                "right":"5%"
            })
    ])
])

@app.callback(Output('pause-button', 'children'),
              [Input('pause-button', 'n_clicks')],
              )
def pause_live(n_clicks):
    print(n_clicks)
    if n_clicks is None:
        return "PAUSE"

    if n_clicks % 2 is 0:
        return "PAUSE"

    return "START"

@app.callback(Output('wind-speed-update', 'interval'),
              [Input('pause-button', 'n_clicks')],
              )
def pause_live(n_clicks):
    print(n_clicks)
    if n_clicks is None:
        return 1000

    if n_clicks % 2 is 0:
        return 1000

    return 3600*1000

XRANGE = 10
@app.callback(Output('live-graph', 'figure'),
              [],[],
              [Event('wind-speed-update', 'interval')])
def update_metrics():
    df = meminfo.get_info()
    if len(df) is 0:
        return None

    data = []
    for i in df.columns:
        trace = go.Scatter(
            x = df.index,
            y = df[i],
            name = i,
        )

        data.append(trace)

    if len(df.index) < XRANGE:
        s = df.index[0]
    else:
        s = df.index[-XRANGE]
    e = df.index[-1]

    layout = go.Layout(
        title = "Device MemInfo",
        xaxis = dict(
            range = [s, e]
        ),
        yaxis = dict(
                title = "memory usage(MB)"
        ),
    )
    
    fig = go.Figure(data=data, layout=layout)
    
    return fig 

external_css = [
    "https://code.getmdl.io/1.3.0/material.indigo-pink.min.css",
    "https://fonts.googleapis.com/icon?family=Material+Icons",
    #"https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css",
    ]

for css in external_css:
    app.css.append_css({"external_url": css})

external_js = [
    "https://code.getmdl.io/1.3.0/material.min.js",
    #"https://code.jquery.com/jquery-3.2.1.min.js",
    #"https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js"
    ]

for js in external_js:
    app.scripts.append_script({"external_url": js})

meminfo = MemInfo()
meminfo.start()

if __name__ == '__main__':
    app.run_server()
    #app.run_server(host='0.0.0.0')
    meminfo.join()


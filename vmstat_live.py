import dash
from dash.dependencies import Input, Output, State, Event
import dash_core_components as dcc
import dash_html_components as html
import datetime
import plotly.graph_objs as go
from plotly import tools
import numpy as np
import threading
import queue
import subprocess
import time
import re
import pandas as pd
from deviceinfo import VmStat 

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
    df = vmstat.get_info()
    if len(df) is 0:
        return None
       
    data_cpu = []
    name = ["us", "sy", "wa", "cpu_u"]
    for i in name:
        trace = go.Scatter(
            x = df.index,
            y = df[i],
            name = i,
        )

        data_cpu.append(trace)


    data_memory = []
    name = ["swap","free","buffer","cache"]
    for i in name:
        trace = go.Scatter(
            x = df.index,
            y = df[i],
            name = i,
        )

        data_memory.append(trace)
    
    data_io = []
    name = ["si","so","bi","bo"]
    for i in name:
        trace = go.Scatter(
            x = df.index,
            y = df[i],
            name = i,
        )

        data_io.append(trace)


    if len(df.index) < XRANGE:
        s = df.index[0]
    else:
        s = df.index[-XRANGE]
    e = df.index[-1]
        
    fig = tools.make_subplots(
        rows=3, 
        cols=1,
        subplot_titles=(
            'CPU Info', 
            'Memory Info',
            'IO Info', )
        )
    fig['layout']['yaxis1'].update(title='Usage(%)')
    fig['layout']['yaxis2'].update(title='Memory Usage(MB)')
    fig['layout']['yaxis3'].update(title='IO Through(KB)')
    fig['layout']['xaxis1'].update(range = [s, e])
    fig['layout']['xaxis2'].update(range = [s, e])
    fig['layout']['xaxis3'].update(range = [s, e])

    for i in data_cpu:
        fig.append_trace(i, 1,1)
    for i in data_memory:
        fig.append_trace(i, 2,1)
    for i in data_io:
        fig.append_trace(i, 3,1)

    '''
        xaxis = dict(
            range = [s, e]
        ),
    '''
    
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

vmstat = VmStat()
vmstat.start()

if __name__ == '__main__':
    app.run_server()
    #app.run_server(host='0.0.0.0')
    vmstat.join()


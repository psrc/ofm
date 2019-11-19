import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly
import plotly.graph_objects as go
import pandas as pd
import os
import pyodbc
import numpy as np
from functions import *
from app import app
from tabs import tab_county


banner = dbc.Jumbotron(
    [
        dbc.Container(
            [
                html.H1('Office of Financial Management (OFM), Small Area Estimates', className="display-head"),
                html.H2('For the Central Puget Sound Region', className="lead")
            ],
            fluid=True
        )
    ],
    fluid=True
)

tabs = dbc.Tabs(
        [
            dbc.Tab(label='County', tab_id='tab-county'),
            dbc.Tab(label='Region', tab_id='tab-region')
        ],
        id="tabs",
        active_tab="tab-county"
        )

content = html.Div(id='tabs-content')

app.layout = html.Div([banner, tabs, content])

@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'active_tab')])
def render_content(tab):
    if tab == 'tab-county':
        return tab_county.tab_county_layout
    #elif tab == 'tab-region':
    #    return tab_region.tab_2_layout

if __name__ == '__main__':
    app.run_server(debug=True)



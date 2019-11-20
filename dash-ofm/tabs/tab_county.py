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

cnty_checklist = dbc.FormGroup(
    [
         html.Legend("County"),
         dbc.Checklist(
            id='county-id-checklist',
            options=[
                 {'label':'King', 'value':'033'},
                 {'label':'Kitsap', 'value':'035'},
                 {'label':'Pierce', 'value':'053'},
                 {'label':'Snohomish', 'value':'061'}
             ],
            value=['033'],
            className = 'selector'
        )
    ] 
)

est_type_radioitem = dbc.FormGroup(
    [
         html.Legend("Estimate Type"),
         dbc.RadioItems(
            id='estimate-type-radioitem',
            options=[
                {'label':'Total Population', 'value':'Total Population'},
                {'label':'Household Population', 'value':'Household Population'},
                {'label':'Group Quarter Population', 'value':'Group Quarter Population'},
                {'label':'Household', 'value':'Household'},
                {'label':'Housing Unit', 'value':'Housing Unit'}
                ],
            value='Total Population',
            className = 'selector'
        )
    ]
)

body = dbc.Container(
    [
 
        dbc.Row(
            [
                 dbc.Col(className="pretty-container", children=[dbc.Form([cnty_checklist, est_type_radioitem])], width=2),
                 dbc.Col(children=[
                     html.Div(dcc.Graph(id='county-graph'), className="pretty-container-graph"), 
                     html.Div(dcc.Graph(id='county-growth-graph'), className="pretty-container-graph")
                              ], 
                         width=10)
            ],
         className="body")
    ],
    #className="body",
    className="body-container",
    fluid=True
)

#app.layout = html.Div([banner, body])
tab_layout = body

@app.callback(
       [Output(component_id='county-graph', component_property='figure'),
        Output(component_id='county-growth-graph', component_property='figure')
        ],
       [Input(component_id='estimate-type-radioitem', component_property='value'),
        Input(component_id='county-id-checklist', component_property='value')
       ]
       )
def update_graphs(attribute, countyids):
    data1 = create_county_bar_traces(df, 'Year', 'Estimate', attribute, countyids)
    data2 = create_county_bar_traces(df_growth, 'Label', 'Delta', attribute, countyids)
    layout1 = create_bar_layout('stack', 'Year', list(range(2000,2020)), 'Estimate')
    layout2 = create_bar_layout('stack', 'Year', df_growth_label, 'Growth')
    return {'data': data1, 'layout': layout1}, {'data': data2, 'layout': layout2}

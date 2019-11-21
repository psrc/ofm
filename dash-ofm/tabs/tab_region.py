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

region_est_type_radioitem = dbc.FormGroup(
    [
         html.Legend("Estimate Type"),
         dbc.RadioItems(
            id='region-estimate-type-radioitem',
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

region_body = dbc.Container(
    [
 
        dbc.Row(
            [
                 dbc.Col(className="pretty-container", children=[dbc.Form([region_est_type_radioitem])], width=2),
                 #dbc.Col(children=[
                 #    html.Div(dcc.Graph(id='region-graph'), className="pretty-container-graph"), 
                 #    html.Div(dcc.Graph(id='region-growth-graph'), className="pretty-container-graph")
                 #             ], 
                 #        width=10)
                 dbc.Col(
                     [
                     dbc.Row(children=[
                         dbc.Col(html.Div(dcc.Graph(id='region-graph'), className="pretty-container-graph"), width=8),
                         dbc.Col(html.Div(dcc.Graph(id='region-pie'), className="pretty-container-graph"), width=4)
                         ]),
                     html.Div(dcc.Graph(id='region-growth-graph'), className="pretty-container-graph")
                     ],
                     width=10
                     )
            ],
         className="body")
    ],
    className="body-container",
    fluid=True
)

region_tab_layout = region_body

@app.callback(
       [Output(component_id='region-graph', component_property='figure'),
        Output(component_id='region-growth-graph', component_property='figure'),
        Output(component_id='region-pie', component_property='figure')
        ],
       [Input(component_id='region-estimate-type-radioitem', component_property='value')]
       )
def update_region_graphs(attribute):
    chart_title1 = "Regional Annual Estimates for " + attribute
    chart_title2 = "Regional Annual Change for " + attribute
    data1 = create_region_bar_traces(df_region, 'Year', 'Estimate', attribute)
    data2 = create_region_bar_traces(df_growth_region, 'Label', 'Delta', attribute)
    layout1 = create_bar_layout('stack', 'Year', list(range(2000,2020)), 'Estimate', chart_title1)
    layout2 = create_bar_layout('stack', 'Year', df_growth_label, 'Growth', chart_title2)
    data3 = create_region_pie(df, 'CountyName', 'Estimate', attribute, ['2019'])
    layout3 = create_pie_layout(attribute)
    return {'data': data1, 'layout': layout1}, {'data': data2, 'layout': layout2}, {'data': data3, 'layout':layout3}


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

cnty_code_dict = {'033':'King', '035':'Kitsap', '053':'Pierce', '061':'Snohomish'}

def sqlconn(dbname):
    # create Elmer connection
    con = pyodbc.connect('DRIVER={SQL Server};SERVER=AWS-PROD-SQL\COHO;DATABASE=' + dbname + ';trusted_connection=true')
    return(con)

def query_tblOfmSaep():
    # retrieve ofm county data from Elmer
    con = sqlconn('Sandbox')
    table_name = 'Christy.tblOfmSaep'
    query = "SELECT CountyID, Year, AttributeDesc, sum(Estimate) as Estimate FROM " + table_name + " GROUP BY CountyID, Year, AttributeDesc"
    df = pd.read_sql(query, con)
    con.close()
    df['CountyName'] = df['CountyID'].map(cnty_code_dict)
    return(df)

#def create_growth_tblOfmSaep(table):
#    table = table.sort_values(by='Year')

df = query_tblOfmSaep()
#df.sort_values(by='Year')

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])

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
            value=['033', '035', '053', '061'],
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
                 dbc.Col(className="card border-secondary mb-3", children=[dbc.Form([cnty_checklist, est_type_radioitem])], width={"size":2}),
                 dbc.Col(dcc.Graph(id='county-graph'), width=10)
            ]
         )
    ],
    className="body",
    fluid=True
)

app.layout = html.Div([banner, body])


@app.callback(
       Output(component_id='county-graph', component_property='figure'),
       [Input(component_id='estimate-type-radioitem', component_property='value'),
        Input(component_id='county-id-checklist', component_property='value')
       ]
       )
def update_county_graph(attribute, countyids):
    filtered_df = df[(df.AttributeDesc == attribute) & (df['CountyID'].isin(countyids))]
    traces = []
    for i in df['CountyName'].unique():
        df_by_county = filtered_df[filtered_df['CountyName'] == i]
        traces.append(go.Bar(
            x = df_by_county['Year'],
            y = df_by_county['Estimate'],
            name = i
            ))

    return {
        'data': traces,
        'layout':go.Layout(
                barmode='stack',
                xaxis={'title': 'Year', 'type': 'category', 'categoryorder':'array', 'categoryarray': list(range(2000,2020))},
                yaxis={'title': ''},
                font=dict(family='Segoe UI', color='#7f7f7f'), 
                showlegend=True
                )
        }

if __name__ == '__main__':
    app.run_server(debug=True)
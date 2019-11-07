import dash
import dash_core_components as dcc
import dash_html_components as html
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

df = query_tblOfmSaep()

app = dash.Dash(__name__)

app.layout = html.Div(children=[

    html.Header(className="jumbotron", children=[ 
        html.H1(className="display-head",
        children='Office of Financial Management (OFM), Small Area Estimates'
        ),

        html.H2(className="lead", children='''
                Counties in the Central Puget Sound Region
            ''')]),

    
    html.Div(className='content-box', children=[
            html.Aside(className="card border-secondary mb-3", children=[
                html.Section(className="form-check", children=[ 
                    html.Legend('County'),
                      dcc.Checklist(id='county-id-checklist',
                                  className="selector",
                        options=[
                            {'label':'King', 'value':'033'},
                            {'label':'Kitsap', 'value':'035'},
                            {'label':'Pierce', 'value':'053'},
                            {'label':'Snohomish', 'value':'061'}
                            ],
                        value=['033', '035', '053', '061']
                      )]
                      ), # end Section
                html.Section(className="form-check", children=[ 
                    html.Legend('Estimate Type'),
                    dcc.RadioItems(id='estimate-type-radioitem',
                                   className="selector",
                        options=[
                            {'label':'Total Population', 'value':'Total Population'},
                            {'label':'Household Population', 'value':'Household Population'},
                            {'label':'Group Quarter Population', 'value':'Group Quarter Population'},
                            {'label':'Household', 'value':'Household'},
                            {'label':'Housing Unit', 'value':'Housing Unit'}
                            ],
                        value='Total Population'
              )])         
            ]) # end Aside
            , 
        html.Main(children=[
            dcc.Graph(id='county-graph')
            ]) # end Main
    ]) # end Div.content-box
     
]) # end parent

@app.callback(
       Output(component_id='county-graph', component_property='figure'),
       [Input(component_id='estimate-type-radioitem', component_property='value'),
        Input(component_id='county-id-checklist', component_property='value')
        #Input(component_id='county-id-radioitem', component_property='value')
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
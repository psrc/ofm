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

def create_growth_tblOfmSaep(countytable):
    df_growth = countytable.sort_values(by=['CountyName', 'AttributeDesc','Year'])
    df_growth['Delta'] = df_growth.groupby(['CountyName', 'AttributeDesc']).transform(lambda x:x.diff())
    df_growth = df_growth.reset_index(drop=True)
    years = list((range(2000, 2020)))
    years = [str(x) for x in years]
    years_combo = [i + '-' + j for i, j in zip(years[:-1], years[1:])]
    label_dict = dict(zip(years[1:], years_combo))
    df_growth['Label'] = df_growth['Year'].map(label_dict)
    df_growth = df_growth.loc[~df_growth['Delta'].isna()]
    return(df_growth)

def create_county_bar_traces(table, xcol, ycol, attribute, countyids):
    filtered_df = table[(table.AttributeDesc == attribute) & (table['CountyID'].isin(countyids))]
    traces = []
    for i in table['CountyName'].unique():
        df_by_county = filtered_df[filtered_df['CountyName'] == i]
        traces.append(go.Bar(
            x = df_by_county[xcol],
            y = df_by_county[ycol],
            name = i
            ))
    return(traces)

def create_bar_layout(mode, xtitle, catarray, ytitle):
    layout = go.Layout(
        barmode=mode,
        xaxis={'title': xtitle, 'type': 'category', 'categoryorder':'array', 'categoryarray': catarray},
        yaxis={'title': ytitle},
        font=dict(family='Segoe UI', color='#7f7f7f'), 
        showlegend=True,
        autosize=True
        )
    return(layout)

df = query_tblOfmSaep()
df_growth = create_growth_tblOfmSaep(df)
df_growth_label = df_growth['Label'].unique()


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

app.layout = html.Div([banner, body])

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

if __name__ == '__main__':
    app.run_server(debug=True)
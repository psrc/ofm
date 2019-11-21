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
geog_color_dict = {'King':'#933890', #purple
                   'Kitsap': '#f05a28', #orange
                   'Pierce': '#9ac75c', #green
                   'Snohomish': '#45a8a3', #teal
                   'Region': '#76787a' #grey
                   }

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

def create_growth_tblOfmSaep(geog, table):
    # calculate and label deltas. Table is either county level or regional level
    if geog == 'county':
        df_growth = table.sort_values(by=['CountyName', 'AttributeDesc','Year'])
        df_growth['Delta'] = df_growth.groupby(['CountyName', 'AttributeDesc']).transform(lambda x:x.diff())
    elif geog == 'region':
        df_growth = table.sort_values(by=['AttributeDesc','Year'])
        df_growth['Delta'] = df_growth.groupby(['AttributeDesc']).transform(lambda x:x.diff())  
    df_growth = df_growth.reset_index(drop=True)
    years = list((range(2000, 2020)))
    years = [str(x) for x in years]
    years_combo = [i + '-' + j for i, j in zip(years[:-1], years[1:])]
    label_dict = dict(zip(years[1:], years_combo))
    df_growth['Label'] = df_growth['Year'].map(label_dict)
    df_growth = df_growth.loc[~df_growth['Delta'].isna()]
    return(df_growth)

def create_region_pie(table, labelscol, valuescol, attribute, year):
    filtered_df = table[(table.AttributeDesc == attribute) & (table['Year'].isin(year))]
     #create array
    colors = np.array(['']*len(filtered_df[labelscol]), dtype = object)
    for i in np.unique(filtered_df[labelscol]):
        colors[np.where(filtered_df[labelscol] == i)] = geog_color_dict[str(i)]

    fig = [go.Pie(
        labels=filtered_df[labelscol],
        values=filtered_df[valuescol],
        marker={'colors':colors, 
                'line':{'color':'#ffffff', 'width':2}}
        
        )]
    return(fig)

def create_pie_layout(attribute):
    layout = go.Layout(
        title = 'Percent of ' + attribute + ' in Region',
        font=dict(family='Segoe UI', color='#7f7f7f'), 
        showlegend=True,
        autosize=True
        )
    return(layout)

def create_county_bar_traces(table, xcol, ycol, attribute, countyids):
    filtered_df = table[(table.AttributeDesc == attribute) & (table['CountyID'].isin(countyids))]
    traces = []
    for i in table['CountyName'].unique():
        df_by_county = filtered_df[filtered_df['CountyName'] == i]
        traces.append(go.Bar(
            x = df_by_county[xcol],
            y = df_by_county[ycol],
            name = i,
            marker = {'color':geog_color_dict[i]}
            ))
    return(traces)

def create_region_bar_traces(table, xcol, ycol, attribute):
    filtered_df = table[table.AttributeDesc == attribute]
    traces = []
    traces.append(go.Bar(
        x = filtered_df[xcol],
        y = filtered_df[ycol],
        name = 'Region',
        marker = {'color':geog_color_dict['Region']}
        ))
    return(traces)

def create_bar_layout(mode, xtitle, catarray, ytitle, charttitle):
    layout = go.Layout(
        barmode=mode,
        title = charttitle,
        xaxis={'title': xtitle, 'type': 'category', 'categoryorder':'array', 'categoryarray': catarray},
        yaxis={'title': ytitle},
        font=dict(family='Segoe UI', color='#7f7f7f'), 
        showlegend=True,
        autosize=True
        )
    return(layout)

# county tables
df = query_tblOfmSaep()
#df_growth = create_growth_tblOfmSaep(df)
df_growth = create_growth_tblOfmSaep('county', df)
df_growth_label = df_growth['Label'].unique()

# regional tables
df_region = df.groupby(['Year', 'AttributeDesc'])['Estimate'].sum().reset_index()
df_growth_region = create_growth_tblOfmSaep('region', df_region)


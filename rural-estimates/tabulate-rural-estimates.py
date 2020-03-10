import os
import pandas as pd
from datetime import date

dir = r'J:\OtherData\OFM\SAEP\SAEP Extract_2019-10-15\requests\beccah_rural'
years = [x for x in range(2012,2018)]
est_cols = ['parcel_tot', 'parcel_gq', 'parcel_hhp', 'parcel_hu', 'parcel_ohu']
est_cols_alias = ['Total Population', 'Group Quarters Population', 'Household Population', 'Housing Units', 'Households']
est_cols_dict = dict(zip(est_cols, est_cols_alias))

juris_lookup = pd.read_csv(os.path.join(dir, 'juris_lookup.csv'))
master_df = pd.DataFrame()

for year in years:
    print('reading file: ' + 'rural_parcelized_ofm_' + str(year) + '_vintage_2019.csv')
    df = pd.read_csv(os.path.join(dir, 'rural_parcelized_ofm_' + str(year) + '_vintage_2019.csv'))
    df_sum = df.groupby('JURIS')[est_cols].sum().reset_index()
    df_melt = df_sum.melt(id_vars = ['JURIS'], value_vars = est_cols)
    df_melt['year'] = year
    if master_df.empty == True:
        master_df = df_melt.copy()
    else:
        print('appending df to master')
        master_df = pd.concat([master_df, df_melt])

master_df['variable'] = master_df['variable'].map(est_cols_dict)
master_join = master_df.merge(juris_lookup, how = 'left', on = 'JURIS')
df_agg = master_join.groupby(['COUNTY', 'variable', 'year'])['value'].sum().reset_index()
df_agg['COUNTY'] = df_agg['COUNTY'] + ' Rural'
df_agg = df_agg.rename(columns = {'COUNTY': 'County', 'variable':'EstimateType', 'year':'Year', 'value':'Estimate'})
df_agg['Version'] = 'September 2019'

df_final = df_agg.loc[(df_agg['County'] != 'King Rural')]
df_final['EstimateType'] = pd.Categorical(df_final['EstimateType'], est_cols_alias)
df_final = df_final.sort_values(['County', 'EstimateType', 'Year'])
df_final.to_excel(os.path.join(dir, 'rural_estimates_county_year_' + str(date.today()) + '.xlsx'), index = False)


#QC
#df_agg.loc[(df_agg['year'] == 2017) & (df_agg['variable'] == 'Total Population'), 'value'].sum()
#df_agg.loc[(df_agg['year'] == 2017) & (df_agg['variable'] == 'Total Population') & (df_agg['COUNTY'] == 'Pierce Rural'), 'value'].sum()
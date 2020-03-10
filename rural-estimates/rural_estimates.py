# This script will read parcelized block estimates by year, 
# spatial join against rural areas, 
# and export results to csv for further data wrangling

import os
import pandas as pd
import geopandas as gpd

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

dir = r'J:\OtherData\OFM\SAEP\SAEP Extract_2019-10-15\parcelized'
out_dir = r'J:\OtherData\OFM\SAEP\SAEP Extract_2019-10-15\requests\beccah_rural'

years = [x for x in range(2012, 2018)]

est_cols = ['parcel_tot', 'parcel_gq', 'parcel_hhp', 'parcel_hu', 'parcel_ohu']
sub_cols = [x for x in est_cols]
sub_cols.append('geometry')

rural_shp_dir = r'W:\geodata\political\PSRC_region.gdb'
r_shp = gpd.read_file(rural_shp_dir, driver = 'FileGDB', layer = 'rural')
r_shp = r_shp[['JURIS', 'geometry']]

for year in years:
    print('Reading file: parcelized_ofm_' + str(year) + '_vintage_2019.shp')
    p_shp = gpd.read_file(os.path.join(dir, 'parcelized_ofm_' + str(year) + '_vintage_2019.shp'))
    p_shp.crs = {'init':'epsg:2285'}
    p_shp = p_shp.to_crs({'init':'epsg:2285'})
    print('subset for impt columns')
    p_shp_sub = p_shp[sub_cols]
    print('intersecting with rural shapefile')
    int_shp = gpd.sjoin(p_shp_sub, r_shp)
    int_shp.to_csv(os.path.join(out_dir, 'rural_parcelized_ofm_' + str(year) + '_vintage_2019.csv'), index = False)
    #int_shp.to_file(os.path.join(out_dir, 'rural_parcelized_ofm_' + str(year) + '_vintage_2019.shp'))
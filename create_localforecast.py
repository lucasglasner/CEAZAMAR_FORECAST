'''
 # @ Author: lucas
 # @ Create Time: 2022-08-01 12:13:57
 # @ Modified by: lucas
 # @ Modified time: 2022-08-01 12:14:03
 # @ Description:
 Script para crear la tabla con los pronosticos de las localidades
 en /data/SITIOS.csv
 '''

# ---------------------------------------------------------------------------- #
#                                    IMPORT                                    #
# ---------------------------------------------------------------------------- #
from joblib import Parallel, delayed
from multiprocessing import Pool

import sys
import os
from glob import glob

import xarray as xr
import pandas as pd
import numpy as np
import datetime
import time

from load import forecast_path, load_forecast_data
from numerics import coastwinddir, deg2compass, beaufort_scale, filter_timeseries
from numerics import grabpoint
from params import *
# ---------------------------------------------------------------------------- #
#                                GLOBAL VARIABLES                              #
# ---------------------------------------------------------------------------- #
    
def createlocal_data(name, lat, lon, atm, waves, ocean):
# ----------------------------------- atm ------------------------------- #
    atm_local  = grabpoint(atm,lat,lon)[[windspeed_name,'WDIR','COASTANGLE',
                                         uwnd_name,vwnd_name]]
# ----------------------------------- waves ------------------------------ #
    waves_local = grabpoint(waves,lat,lon)[[waveperiod_name,
                                            waveheight_name,
                                            wavedir_name]]  
    #fill 3h to 1h
    waves_local = waves_local.resample('h').interpolate(method='linear')
    
# ------------------------------------ SST ------------------------------- #
    sst_local = grabpoint(ocean,lat,lon)[sst_name]
    #interpolate from xx:30 to xx:00
    sst_local = sst_local.resample('h').bfill()
  
    # #Anomaly respect to satellite
    # sstclim_local = grabpoint(clim,lat,lon)[sst_name]
    # sst_anomaly_local = sst_local.to_xarray().groupby('leadtime.dayofyear')
    # sst_anomaly_local = (sst_anomaly_local-sstclim_local.to_xarray()).to_series()
    # sst_anomaly_local.name = 'thetao_anomaly'
    
    #Synoptic anomalies
    #sst_sanomaly_local = sst_local-filter_timeseries(sst_local, 5, 1/30/24)
    #sst_sanomaly_local = sst_sanomaly_local.reindex(waves_local.index)
    #sst_local = sst_local.reindex(waves_local.index)
    #sst_sanomaly_local = sst_sanomaly_local.resample('d').mean()
    #sst_sanomaly_local.index = sst_sanomaly_local.index+pd.Timedelta(hours=12)
    #sst_sanomaly_local = sst_sanomaly_local.resample('h').interpolate('cubic')
    #sst_sanomaly_local.name = 'thetao_synoptic_anomaly'
 
# ----------------------------------- MERGE ---------------- ------------- #
    data = pd.concat([atm_local,waves_local,sst_local], axis=1)
    data['WDIR_STR'] = data['WDIR'].map(lambda x: deg2compass(x))
    data['VMDR_STR'] = data[wavedir_name].map(lambda x: deg2compass(x))
    data['BEAUFORT'] = (data[windspeed_name]*1.94).map(lambda x: beaufort_scale(x))
    data.name = name
    data = data.loc[FORECAST_DATE:]
    # print('         Creating data for: '+name)
    return data

def create_localforecast(idate, locations, n_jobs=10, save=True):
    fdate = pd.to_datetime(idate)+pd.Timedelta(hours=NHOURS_LOCAL)
    fdate = fdate.strftime('%F')
    
    atm_path = forecast_path(idate,'atm')    
    ocean_path = forecast_path(idate,'ocean')
    waves_path = forecast_path(idate,'wave')
    
    atm  = load_forecast_data(atm_path,'atm').squeeze().sel(
        leadtime=slice(idate,fdate))
    
    waves = load_forecast_data(waves_path,'wave').squeeze().sel(
        leadtime=slice(idate,fdate))
    
    hindcast = sorted(glob(ocean_hindcast_dir+'/*.nc'))[-120:]
    hindcast = [load_forecast_data(p,'ocean').chunk({'leadtime':1})[sst_name].squeeze().load()
                for p in hindcast]
    hindcast = xr.concat(hindcast,'leadtime')
    
    sst   = load_forecast_data(ocean_path,'ocean')[sst_name].squeeze()
    sst   = xr.concat([hindcast,sst],'leadtime').sortby('leadtime').drop_duplicates(dim='leadtime')
    
    # sstclim = xr.open_dataset(ocean_climatology_dir)[sst_name]
    # ------------------------ compute extra variables------------------------ #
    atm[windspeed_name] = np.hypot(atm.U10,atm.V10)
    atm['COASTANGLE'] = coastwinddir(atm.U10,atm.V10,atm.LANDMASK)
    atm['WDIR'] = (90-np.rad2deg(np.arctan2(-atm.V10,-atm.U10)))%360
    atm = atm.where(~atm.LANDMASK.values[0].astype(bool))
    # ----------------------------- select point ----------------------------- #
    # ---------------- transform variables to local time UTC-4 --------------- #

    DATA=Parallel(n_jobs=n_jobs)(delayed(createlocal_data)(n,i,j,
                                                       atm,
                                                       waves,
                                                       sst) 
                             for n,i,j in zip(locations.index,
                                              locations.lat,
                                              locations.lon))
    if save:
        print('Saving data...')
        for name,data in zip(locations.index,DATA):
            data = data.reindex(pd.date_range(idate,fdate,freq='h'))
            data = data.loc[idate:fdate]
            data.to_csv('tmp/'+name.replace("_","")+'_FORECAST_CURRENT.csv')
        print('Done\n')
    return DATA

if __name__=='__main__':
    locations=pd.read_csv('data/COASTAL_POINTS.csv', index_col=0).iloc[:1,:]
    create_localforecast(idate=FORECAST_DATE,locations=locations)
    sys.exit()

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
import os
from glob import glob
from joblib import Parallel, delayed
from multiprocessing import Pool

import xarray as xr
import pandas as pd
import numpy as np
import datetime
import time

from scipy.signal import argrelmax, argrelmin
from load import forecast_path, load_forecast_data, load_tpxo
from numerics import coastwinddir, deg2compass, beaufort_scale, filter_timeseries
from numerics import grabpoint, fill_borders, egbert_correct, modified_julian_day
from numerics import utc_to_local
from params import *

import sys
sys.path.append('./pytides/pytides/')

from pytides.pytides.tide import Tide
from pytides.pytides.constituent import TPXO7

# ---------------------------------------------------------------------------- #
#                                GLOBAL VARIABLES                              #
# ---------------------------------------------------------------------------- #
    
def createlocal_data(name, lat, lon, atm, waves, ocean):
# ----------------------------------- atm ------------------------------- #
    atm_local  = grabpoint(atm,lat,lon)[[windspeed_name,'WDIR','COASTANGLE',
                                         uwnd_name,vwnd_name]]
# ----------------------------------- waves ----------------------------- #
    waves_local = grabpoint(waves,lat,lon)[[waveperiod_name,
                                            waveheight_name,
                                            wavedir_name]]  
    #fill 3h to 1h

    waves_local = waves_local.resample('h').interpolate(method='linear')
    
# ------------------------------------ SST ----------------------------- #
    sst_local = grabpoint(ocean[sst_name],lat,lon)[sst_name]
    #interpolate from xx:30 to xx:00
    sst_local = sst_local.resample('h').bfill()

# ----------------------------------- TIDES ---------------------------- #
    #Get harmonics
    tides_harmonics_local = grabpoint(ocean[['tssh_amplitude',
                                             'tssh_phase']],
                                      lat,lon)
    tides_harmonics_local = tides_harmonics_local[['tssh_amplitude',
                                                   'tssh_phase']]
    #Create tide model from harmonics and constituents
    tidemodel = Tide(TPXO7,
                     list(tides_harmonics_local['tssh_amplitude'].values),
                     list(tides_harmonics_local['tssh_phase'].values))
    
    #Build time series from harmonics and the fourier series at every minute
    _times = pd.date_range(sst_local.index[0], sst_local.index[-1],
                           freq='1min')
    tides_local = pd.Series(tidemodel.at(_times),
                            index=_times, name='ssh_tides')
    tides_local      = tides_local-tides_local.mean()
    
    #Get time of local high and low tide
    hightides_time   = tides_local.index[argrelmax(tides_local.values,
                                              order=120)]
    hightides        = pd.Series(np.ones(len(sst_local.index))*np.nan,
                                 index=sst_local.index,name='hightides')
    for h in hightides_time:
        f = abs((hightides.index-h).total_seconds())
        hightides.iloc[np.where(f==np.min(f))] = h-pd.Timedelta(hours=4)
        
    lowtides_time    = tides_local.index[argrelmin(tides_local.values,
                                              order=120)]
    lowtides         = pd.Series(np.ones(len(sst_local.index))*np.nan,
                                 index=sst_local.index,name='lowtides')
    for h in lowtides_time:
        f = abs((lowtides.index-h).total_seconds())
        lowtides.iloc[np.where(f==np.min(f))] = h-pd.Timedelta(hours=4)

    #Reshape tide series to hourly frequency    
    tides_local      = tides_local.reindex(sst_local.index)

# ----------------------------------- MERGE ---------------------------- #
    data = pd.concat([atm_local,waves_local,sst_local], axis=1)
    data['WDIR_STR'] = data['WDIR'].map(lambda x: deg2compass(x))
    data['VMDR_STR'] = data[wavedir_name].map(lambda x: deg2compass(x))
    data['BEAUFORT'] = (data[windspeed_name]*1.94).map(
        lambda x: beaufort_scale(x))
    data = pd.concat([data,tides_local,hightides,lowtides], axis=1)
    data.name = name
    data = utc_to_local(data)
    # data = data.loc[FORECAST_DATE:]
    # print('         Creating data for: '+name)
    return data

def create_localforecast(idate, locations, n_jobs=10, save=True):
    fdate = pd.to_datetime(idate)+pd.Timedelta(hours=NHOURS_LOCAL)
    fdate = (fdate).strftime('%Y-%m-%d %H:%M:%S')
    
    atm_path = forecast_path(idate,'atm')      #Path to operational weather forecast
    ocean_path = forecast_path(idate,'ocean')  #Path to operational ocean forecast
    waves_path = forecast_path(idate,'wave')   #Path to operational wave forecast
    
    # --------------------------- Load weather forecast ---------------------- #
    atm  = load_forecast_data(atm_path,'atm').squeeze()
    atm  = atm.sortby('leadtime').drop_duplicates(dim='leadtime')
    
    # ---------------------------- Load wave forecast ------------------------ #
    waves = load_forecast_data(waves_path,'wave').squeeze()
    waves = waves.sortby('leadtime').drop_duplicates(dim='leadtime')
    
    # ---------------------------- Load ocean forecast ----------------------- #
    ocean   = load_forecast_data(ocean_path,'ocean').squeeze()
    ocean   = ocean.sortby('leadtime').drop_duplicates(dim='leadtime')
    
    tides   = fill_borders(load_tpxo(idate))
    tides   = tides[['tssh_amplitude','tssh_phase']].interp({'lat':ocean.lat,
                                                             'lon':ocean.lon})

    
    pf,pu,t0,phase_mkB  = egbert_correct(modified_julian_day(
                                         pd.to_datetime(idate).date()),
                                         0,0,0)
    pf = pf.loc[tides.name.values]
    pu = pu.loc[tides.name.values]
    
    tides['tssh_amplitude'] = tides['tssh_amplitude']*pf.to_xarray().rename(
        {'index':'name'})
    tides['tssh_phase']     = np.mod(-tides['tssh_phase']-pu.to_xarray().rename(
        {'index':'name'}),360)
    
    ocean   = xr.merge([ocean,tides])

    # ------------------------ compute extra variables------------------------ #
    atm[windspeed_name] = np.hypot(atm.U10,atm.V10)
    atm['COASTANGLE'] = coastwinddir(atm.U10,atm.V10,atm.LANDMASK)
    atm[winddir_name] = (90-np.rad2deg(np.arctan2(-atm.V10,-atm.U10)))%360
    atm = atm.where(~atm.LANDMASK.values[0].astype(bool))
    # ----------------------------- select point ----------------------------- #
    # ---------------- transform variables to local time UTC-4 --------------- #

    DATA=Parallel(n_jobs=n_jobs)(delayed(createlocal_data)(n,i,j,
                                                           atm,
                                                           waves,
                                                           ocean) 
                             for n,i,j in zip(locations.index,
                                              locations.lat,
                                              locations.lon))
    DATA = [data.reindex(pd.date_range(idate,fdate,freq='h'))
            for data in DATA]
    if save:
        print('Saving data...')
        for name,data in zip(locations.index,DATA):
            # data = data.reindex(pd.date_range(idate,fdate,freq='h'))
            # data = data.loc[idate:fdate]
            data.to_csv('tmp/'+name.replace("_","")+'_FORECAST_CURRENT.csv')
        print('Done\n')
    return DATA

if __name__=='__main__':
    locations=pd.read_csv('data/COASTAL_POINTS.csv', index_col=0).iloc[:1]
    create_localforecast(idate=FORECAST_DATE,locations=locations)
    sys.exit()

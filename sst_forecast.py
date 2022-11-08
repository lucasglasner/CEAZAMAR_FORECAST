'''
 # @ Author: lucas
 # @ Create Time: 2022-07-01 12:42:01
 # @ Modified by: Your lucas
 # @ Modified time: 2022-07-25 18:21:52
 # @ Description: 
 # Script for making the CEAZAMAR sea surface temperature forecast.
 # Maps and time series.
 '''

# ---------------------------------------------------------------------------- #
#                                    IMPORTS                                   #
# ---------------------------------------------------------------------------- #
import os
import sys
import locale
from glob import glob
locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')

import pandas as pd
import xarray as xr
import numpy as np
import geopandas as gpd
import regionmask

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import cmocean

from graphical import make_forecast_plot, make_maps
from numerics import bias_correct_SST, fill_borders, filter_xarray
from load import load_forecast_data, forecast_path, load_forecast_ini
from params import *

def sst_forecast(idate,fix_bias=False):
    fdate = pd.to_datetime(idate)+pd.Timedelta(days=NDAYS_REGIONAL)
    fdate = fdate.strftime('%F')
    # --------------------------------- load data -------------------------------- #
    print('Loading SST forecast data...')
    forecast = forecast_path(idate,'ocean')
    print('          Forecast data: '+forecast)
    init     = load_forecast_ini(forecast,'ocean')
    forecast = load_forecast_data(forecast,'ocean')
    forecast = forecast[sst_name].squeeze().load()

    print('Loading SST hindcast data...')
    hindcast = sorted(glob(ocean_hindcast_dir+'/*.nc'))[-120:]
    print('          Hindcast data: '+ocean_hindcast_dir)
    hindcast = [load_forecast_data(p,'ocean').chunk({'leadtime':1})[sst_name].squeeze().load()
                for p in hindcast]
    hindcast = xr.concat(hindcast,'leadtime')
    
    SST_H = xr.concat([hindcast,forecast],'leadtime').sortby('leadtime')
    SST_H = SST_H.sel(lat=slice(*sorted(ocean_mapsextent[2:])),
                      lon=slice(*sorted(ocean_mapsextent[:-2])))

    coastmask = gpd.read_file(COASTLINE_MASK_PATH)
    coastmask = regionmask.mask_geopandas(coastmask,SST_H.lon.values,SST_H.lat.values)
    coastmask = coastmask==0
    # ------------------------------ bias correction ----------------------------- #
    if fix_bias:
        print('Performing bias correction...')
        SST_H = bias_correct_SST(SST_H)
    # --------------------------------- anomalies -------------------------------- #
    print('Computing SST synoptic anomalies...')
    SST_ANOMALY_H = filter_xarray(SST_H, dim='leadtime', order=5, cutoff=1/30/24)
    SST_ANOMALY_H = SST_H-SST_ANOMALY_H
    # ---------------------------------------------------------------------------- #
    SST_ANOMALY_H = fill_borders(SST_ANOMALY_H)
    SST = fill_borders(SST_H)
    SST = SST_H.resample({'leadtime':'d'}).mean().reindex(
        {'leadtime':pd.date_range(idate,fdate,freq='d')})
    SST_ANOMALY = SST_ANOMALY_H.resample({'leadtime':'d'}).mean().reindex(
        {'leadtime':pd.date_range(idate,fdate,freq='d')})
    # ---------------------------------------------------------------------------- #
    #                                     PLOTS                                    #
    # ---------------------------------------------------------------------------- #
    print('Plotting...')
    plt.rc('font',size=12)
    # ------------------------------------ SST ----------------------------------- #
    vmin,vmax = SST.min()-SST.min()%0.5,SST.max()-SST.max()%0.5
    fig,ax,cax,cbar = make_forecast_plot(var=SST,
                                        cmap=cmocean.cm.thermal,
                                        cbar_label='Temperatura superficial\n'+
                                        'del mar (°C)',
                                        xticks=[-72.5,-71],
                                        yticks=[-33,-32,-31,-30,-29,-28,-27],
                                        vmin=vmin,vmax=vmax,level_step=0.25,
                                        extent=ocean_mapsextent)
    cbar.ax.tick_params(labelsize=14)
    for i,axis in enumerate(ax.ravel()):
        axis.set_title(pd.to_datetime(SST.leadtime[i].values).strftime('%a %d-%b'),
                    loc='left', fontsize=13.5)
    ax[-1,0].text(0,-0.15,'Inicio pronóstico océanico: '+ocean_model_name+' '+init+'\n',
                  fontsize=10, transform=ax[-1,0].transAxes, va='top', ha='left')
    
    ax[0,0].set_title(pd.to_datetime(SST.leadtime[0].values).strftime('%Y\n%a %d-%b'),
                    loc='left',fontsize=13.5)
    plt.savefig('plots/SST_FORECASTMAP_CURRENT.png',dpi=150,bbox_inches='tight')
    plt.close()
    # -------------------------------- sst_anomaly ------------------------------- #
    c = plt.cm.get_cmap('RdBu_r',500)
    c1 = c(np.linspace(0,0.45,250))
    c2 = plt.cm.get_cmap('Reds',500)(np.linspace(0,1,250))
    newcmp = ListedColormap(np.vstack([c1,c2]))
    vmin,vmax = -3,3
    fig,ax,cax,cbar = make_forecast_plot(var=SST_ANOMALY,
                                        cmap=newcmp,
                                        cbar_label='Anomalia sinóptica* de temperatura\nsuperficial '+
                                        'del mar (°C)',
                                        xticks=[-72.5,-71],
                                        yticks=[-33,-32,-31,-30,-29,-28,-27],
                                        vmin=vmin,vmax=vmax,level_step=0.25,
                                        extent=ocean_mapsextent)
    cbar.ax.tick_params(labelsize=14)
    for i,axis in enumerate(ax.ravel()):
        axis.set_title(pd.to_datetime(SST.leadtime[i].values).strftime('%a %d-%b'),
                    loc='left', fontsize=13.5)
        # cs=axis.contourf(SST_H.lon,SST_H.lat,SST_ANOMALY.isel(leadtime=i).where(coastmask),
        #               colors='none',
        #               levels=[-5,-1.25,0], hatches=["...","",""])
    ax[0,0].set_title(pd.to_datetime(SST.leadtime[0].values).strftime('%Y\n%a %d-%b'),
                    loc='left',fontsize=13.5)
    
    ax[-1,0].text(0,-0.15,'Inicio pronóstico océanico: '+ocean_model_name+' '+init+'\n'+
                  '*Perturbaciones esperadas debido a la variabilidad menor a 30 días',
                  fontsize=10, transform=ax[-1,0].transAxes, va='top', ha='left')

    plt.savefig('plots/SST_ANOMALY_FORECASTMAP_CURRENT.png',dpi=150,bbox_inches='tight')
    plt.close('all')
    
    print('Done')
    return

if __name__=='__main__':
    sst_forecast(FORECAST_DATE,fix_bias=True)
    sys.exit()

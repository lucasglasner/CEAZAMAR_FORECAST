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

def sst_forecast(idate):
    fdate = pd.to_datetime(idate)+pd.Timedelta(days=NDAYS_REGIONAL)
    fdate = fdate.strftime('%F')
    # --------------------------------- load data -------------------------------- #
    print('Loading SST forecast data...')
    forecast = forecast_path(idate,'ocean')
    print('          Forecast data: '+forecast)
    init     = load_forecast_ini(forecast,'ocean')
    forecast = load_forecast_data(forecast,'ocean')
    forecast = forecast[sst_name].squeeze().load()

    SST_H = forecast.sortby('leadtime')
    SST_H = SST_H.sel(lat=slice(*sorted(ocean_mapsextent[2:])),
                      lon=slice(*sorted(ocean_mapsextent[:-2])))

    # ---------------------------------------------------------------------------- #
    SST = fill_borders(SST_H)
    SST = SST_H.resample({'leadtime':'d'}).mean().reindex(
        {'leadtime':pd.date_range(idate, fdate, freq='d')})
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
                                        xticks=[-74,-72],
                                        yticks=[-34,-33,-32,-31,-30,-29,-28],
                                        vmin=vmin,vmax=vmax,level_step=0.25,
                                        extent=ocean_mapsextent)
    cbar.ax.tick_params(labelsize=12)
    cbar.ax.set_yticks(np.arange(vmin,vmax+1,1))
    for i,axis in enumerate(ax.ravel()):
        axis.set_title(pd.to_datetime(SST.leadtime[i].values).strftime('%a %d-%b'),
                    loc='left', fontsize=13.5)
    ax[-1,0].text(0,-0.15,'Inicio pronóstico océanico: '+ocean_model_name+' '+init+'\n',
                  fontsize=10, transform=ax[-1,0].transAxes, va='top', ha='left')
    
    ax[0,0].set_title(pd.to_datetime(SST.leadtime[0].values).strftime('%Y\n%a %d-%b'),
                    loc='left',fontsize=13.5)
    plt.savefig('plots/SST_FORECASTMAP_CURRENT.png',dpi=150,bbox_inches='tight')
    plt.close('all')
    
    print('Done')
    return

if __name__=='__main__':
    sst_forecast(FORECAST_DATE)
    sys.exit()

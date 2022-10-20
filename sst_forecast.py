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
import sys
import locale
locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')

import pandas as pd
import xarray as xr

import matplotlib.pyplot as plt
import cmocean

from graphical import make_forecast_plot
from numerics import bias_correct_SST, fill_borders, compute_anomalies
from load import load_forecast_data, forecast_path, load_forecast_ini
from params import *

def sst_forecast(idate,fix_bias=True):
    fdate = pd.to_datetime(idate)+pd.Timedelta(days=NDAYS_REGIONAL)
    fdate = fdate.strftime('%F')
    # --------------------------------- load data -------------------------------- #
    print('Loading SST forecast data...')
    forecast = forecast_path(idate,'ocean')
    print('          Forecast data: '+forecast)
    init  = load_forecast_ini(forecast,'ocean')
    SST_H = load_forecast_data(forecast,'ocean')
    SST_H = SST_H[sst_name].squeeze()
    SST = SST_H.resample({'leadtime':'d'}).mean().load()
    SST = SST.reindex({'leadtime':pd.date_range(idate,fdate,freq='d')})
    SST = SST.sel(lat=slice(*sorted(ocean_mapsextent[2:])),
                  lon=slice(*sorted(ocean_mapsextent[:-2])))
    del SST_H
    # ------------------------------ bias correction ----------------------------- #
    if fix_bias:
        print('Performing bias correction...')
        SST = bias_correct_SST(SST)
    # --------------------------------- anomalies -------------------------------- #
    print('Computing SST anomalies...')
    sst_clim = xr.open_dataset(ocean_climatology_dir)[sst_name].squeeze()
    sst_clim = sst_clim.reindex({'lat':SST.lat,'lon':SST.lon}, method='nearest') 
    SST_ANOMALY = compute_anomalies(SST, sst_clim)
    # ---------------------------------------------------------------------------- #
    SST_ANOMALY = fill_borders(SST_ANOMALY)
    SST = fill_borders(SST)
    # ---------------------------------------------------------------------------- #
    #                                     PLOTS                                    #
    # ---------------------------------------------------------------------------- #
    print('Plotting...')
    plt.rc('font',size=12)
    # ------------------------------------ SST ----------------------------------- #
    vmin,vmax = SST.min().round(1),SST.max().round(1)
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
    vmin,vmax = -3.0,3.0
    fig,ax,cax,cbar = make_forecast_plot(var=SST_ANOMALY,
                                        cmap='RdBu_r',
                                        cbar_label='Anomalia* de temperatura\nsuperficial '+
                                        'del mar (°C)',
                                        xticks=[-72.5,-71],
                                        yticks=[-33,-32,-31,-30,-29,-28,-27],
                                        vmin=vmin,vmax=vmax,level_step=0.25,
                                        extent=ocean_mapsextent)
    cbar.ax.tick_params(labelsize=14)
    for i,axis in enumerate(ax.ravel()):
        axis.set_title(pd.to_datetime(SST.leadtime[i].values).strftime('%a %d-%b'),
                    loc='left', fontsize=13.5)

    ax[0,0].set_title(pd.to_datetime(SST.leadtime[0].values).strftime('%Y\n%a %d-%b'),
                    loc='left',fontsize=13.5)
    
    ax[-1,0].text(0,-0.15,'Inicio pronóstico océanico: '+ocean_model_name+' '+init+'\n'+
                  'Climatologia de referencia: OSTIA 2006-2021\n'+
                  '*Diferencia del dato pronosticado y el valor promedio '+
                  'histórico de cada día del año.\n',
                  fontsize=10, transform=ax[-1,0].transAxes, va='top', ha='left')

    plt.savefig('plots/SST_ANOMALY_FORECASTMAP_CURRENT.png',dpi=150,bbox_inches='tight')
    plt.close('all')
    print('Done')
    return

if __name__=='__main__':
    sst_forecast(FORECAST_DATE,fix_bias=True)
    sys.exit()

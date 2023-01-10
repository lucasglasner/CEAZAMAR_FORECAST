'''
 # @ Author: lucas
 # @ Create Time: 2022-07-25 16:39:35
 # @ Modified by: lucas
 # @ Modified time: 2022-07-25 16:39:41
 # @ Description: validation for the last N forecasts
 '''

# ---------------------------------------------------------------------------- #
# ---------------------------------- Imports --------------------------------- #
# ---------------------------------------------------------------------------- #
import os
import sys

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs

import xarray as xr
from load import target_date,forecast_path, load_forecast_data, load_ascat
from numerics import regrid, compute_metrics, fill_borders
from graphical import make_maps, make_forecast_plot
from params import *


def wind_validation(N=30, offset=3):
    # ----------------------- Define times for the analysis ---------------------- #
    time = target_date("data/FORECAST/WRF/U10V10/*.nc","data/ASCAT/*.nc")
    time = time-pd.Timedelta(days=offset)
    target_times = [time-pd.Timedelta(days=n) for n in range(N)]
    date_interval = target_times[-1].strftime("%F"),target_times[0].strftime("%F")
    date_interval = " ; ".join(date_interval)
    print('Loading last '+str(N)+' days of '+atm_model_name+' forecast data...')
    # --------------------------------- Load data -------------------------------- #
    paths = [forecast_path(d.strftime('%F'),'atm') for d in target_times]
    WWRF  = []
    for p in paths:
        wrf = load_forecast_data(p, 'atm').resample({'leadtime':'d'}).mean()
        wrf.coords['leadtime'] = np.arange(len(wrf.leadtime))
        WWRF.append(wrf)
    WWRF  = xr.concat(WWRF,'time').drop_duplicates('time').squeeze()
    
    print('Loading last '+str(N)+' days of '+atm_validation_name+' data')
    WASCAT = [load_ascat(d.strftime('%F')) for d in target_times]
    WASCAT = [x for x in WASCAT if x is not None]
    WASCAT = xr.concat(WASCAT, 'time').drop_duplicates('time').squeeze()
    WASCAT = WASCAT.sel(lat=slice(WWRF.XLAT.min()-0.5,WWRF.XLAT.max()+0.5),
                        lon=slice(WWRF.XLONG.min()-0.5,WWRF.XLAT.max()+0.5))
    # ---------------------------------------------------------------------------- #
    #                                  PROCESS DATA                                #
    # ---------------------------------------------------------------------------- #
    # -------------------------------- Match Grids ------------------------------- #
    lon1,lon2,lat1,lat2 = atm_mapsextent
    print('Performing horizontal regridding...')
    husk = xr.Dataset(coords={'lat':np.arange(lat1,lat2+0.1,0.1),
                              'lon':np.arange(lon1,lon2+0.1,0.1)})
    lat,lon = husk.lat.values,husk.lon.values
    lon2d,lat2d = np.meshgrid(lon,lat)
    WASCAT = regrid(WASCAT,husk)
    WASCAT = WASCAT.where(WASCAT!=0)
    WASCAT['MASK'] = ~np.isnan(WASCAT[windspeed_name])
    WWRF = regrid(WWRF,husk)
    WWRF = WWRF.where(WWRF!=0)
    # ----------------- Compute bias and model evaluation metrics ---------------- #
    WWRF['WS'] = np.sqrt(WWRF.U10**2+WWRF.V10**2)
    WASCAT['WS'] = np.sqrt(WASCAT.U10**2+WASCAT.V10**2)
    print('Computing skill metrics...')
    METRICS = compute_metrics(WWRF['WS'],WASCAT['WS'])
    # ---------------------------------------------------------------------------- #
    #                                     PLOTS                                    #
    # ---------------------------------------------------------------------------- #
    print('Plotting...')
    plt.rc('font',size=12)
    # ------------------------------ make MBIAS maps ----------------------------- #
    label='Sesgo promedio '+r'($\overline{\Delta})$'+'\n'+\
        '$\Delta = U_{pronostico}-U_{satelite}$'+'\n'+'(m/s)'
    fig,ax,cax,cbar = make_forecast_plot(var=METRICS['MBIAS'],
                                         cmap='RdBu_r',
                                         cbar_label=label,
                                         vmin=-3,vmax=3,level_step=0.1,
                                         xticks=[-74,-72],
                                         yticks=[-34,-33,-32,-31,-30,-29,-28],
                                         extent=atm_mapsextent)
    
    for i,axis in enumerate(ax.ravel()):
        axis.set_title("Dia "+str(i+1), loc='left')

    cbar.ax.set_yticks(np.arange(-3,3+0.5,0.5))
    cbar.ax.tick_params(labelsize=12)
    
    ax[-1,0].text(0,-0.15,'Estadistica para el periodo: '+date_interval,
                  fontsize=10, transform=ax[-1,0].transAxes, va='top', ha='left')
    plt.savefig('plots/VIENTO_MBIAS_DIAPRONOSTICO_CURRENT.png',
                dpi=150,bbox_inches='tight')
    # ------------------------------ make RMSE maps ------------------------------ #
    label='Raiz del error cuadratico medio '+r'($\sqrt{\overline{\Delta^2}})$'+\
        '\n'+'$\Delta = U_{pronostico}-U_{satelite}$'+'\n(m/s)'

    fig,ax,cax,cbar = make_forecast_plot(var=METRICS['RMSE'],
                                         cmap='ocean_r',
                                         cbar_label=label,
                                         vmin=0,vmax=6,level_step=0.1,
                                         xticks=[-74,-72],
                                         yticks=[-34,-33,-32,-31,-30,-29,-28],
                                         extent=atm_mapsextent)
    
    for i,axis in enumerate(ax.ravel()):
        axis.set_title("Dia "+str(i+1), loc='left')

    cbar.ax.set_yticks(np.arange(0,6+0.5,0.5))
    cbar.ax.tick_params(labelsize=12)
    
    ax[-1,0].text(0,-0.15,'Estadistica para el periodo: '+date_interval,
                  fontsize=10, transform=ax[-1,0].transAxes, va='top', ha='left')
    plt.savefig('plots/VIENTO_RMSE_DIAPRONOSTICO_CURRENT.png',
                dpi=150,bbox_inches='tight')
    
    # ----------------------- make pearson correlation maps ---------------------- #
    label='Raiz del error cuadratico medio '+r'($\sqrt{\overline{\Delta^2}})$'+\
        '\n'+'$\Delta = U_{pronostico}-U_{satelite}$'+'\n(m/s)'

    fig,ax,cax,cbar = make_forecast_plot(var=METRICS['CORR'],
                                         cmap='turbo',
                                         cbar_label=label,
                                         vmin=0,vmax=1,level_step=0.025,
                                         xticks=[-74,-72],
                                         yticks=[-34,-33,-32,-31,-30,-29,-28],
                                         extent=atm_mapsextent)
    
    for i,axis in enumerate(ax.ravel()):
        axis.set_title("Dia "+str(i+1), loc='left')

    cbar.ax.set_yticks(np.arange(0,1+0.1,0.1))
    cbar.ax.tick_params(labelsize=12)
    
    ax[-1,0].text(0,-0.15,'Estadistica para el periodo: '+date_interval,
                  fontsize=10, transform=ax[-1,0].transAxes, va='top', ha='left')
    plt.savefig('plots/VIENTO_CORR_DIAPRONOSTICO_CURRENT.png',
                dpi=150,bbox_inches='tight')
    print('Done')
if __name__=="__main__":
   wind_validation(N=30)
   sys.exit()

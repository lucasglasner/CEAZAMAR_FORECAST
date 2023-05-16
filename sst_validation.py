'''
 # @ Author: lucas
 # @ Create Time: 2022-07-22 13:10:52
 # @ Modified by: lucas
 # @ Modified time: 2022-07-22 13:27:49
 # @ Description: Validacion ultimos 30 dias de pronostico TSM CEAZAMAR
 '''

# ---------------------------------------------------------------------------- #
# ---------------------------------- Imports --------------------------------- #
# ---------------------------------------------------------------------------- #
import sys

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs

import xarray as xr

from load import target_date, forecast_path, load_forecast_data, load_ostia
from numerics import regrid, compute_metrics, fill_borders, bias_correct_SST
from graphical import make_maps, make_forecast_plot
from params import *


# ------------------------- Script specific functions ------------------------ #
def sst_validation(N=30, offset=3):
    # ----------------------- Define times for the analysis ---------------------- #
    time = target_date(ocean_forecast_dir+'/*.nc',"data/OSTIA/*.nc")
    time = time-pd.Timedelta(days=offset)
    target_times = [time-pd.Timedelta(days=n) for n in range(N)]
    date_interval = target_times[-1].strftime("%F"),target_times[0].strftime("%F")
    date_interval = " ; ".join(date_interval)
    print('Loading last '+str(N)+' days of '+ocean_model_name+' forecast data...')
    # --------------------------------- Load data -------------------------------- #
    SST_MERCATOR = []
    for d in target_times:
        p = forecast_path(d.strftime('%F'), 'ocean')
        sst_mercator = load_forecast_data(p, 'ocean').squeeze()[sst_name]
        sst_mercator = sst_mercator.resample({'leadtime':'d'}).mean()
        sst_mercator.coords['leadtime'] = np.arange(len(sst_mercator['leadtime']))
        SST_MERCATOR.append(sst_mercator)
    SST_MERCATOR = xr.concat(SST_MERCATOR, 'time').drop_duplicates('time')
    SST_MERCATOR = SST_MERCATOR.interpolate_na(dim='lat', method='nearest',limit=3)
    SST_MERCATOR = SST_MERCATOR.interpolate_na(dim='lon', method='nearest',limit=3)
    print('Loading last '+str(N)+' days of '+ocean_validation_name+' data')
    SST_OSTIA = [load_ostia(d.strftime('%F')) for d in target_times]
    SST_OSTIA = [x for x in SST_OSTIA if x is not None]
    SST_OSTIA = xr.concat(SST_OSTIA, 'time').drop_duplicates('time').squeeze()
    SST_OSTIA = SST_OSTIA.sel(lat=slice(SST_MERCATOR.lat.min()-0.5,
                                        SST_MERCATOR.lat.max()+0.5),
                              lon=slice(SST_MERCATOR.lon.min()-0.5,
                                        SST_MERCATOR.lon.max()+0.5))

    # ---------------------------------------------------------------------------- #
    #                                  PROCESS DATA                                #
    # ---------------------------------------------------------------------------- #
    # -------------------------------- Match Grids ------------------------------- #
    lon1,lon2,lat1,lat2 = ocean_mapsextent
    print('Performing horizontal regridding...')
    husk = xr.Dataset(coords={'lat':np.arange(lat1,lat2+0.1,0.1),
                              'lon':np.arange(lon1,lon2+0.1,0.1)})
    lat,lon = husk.lat.values,husk.lon.values
    lon2d,lat2d = np.meshgrid(lon,lat)
    SST_OSTIA = regrid(SST_OSTIA,husk)
    SST_OSTIA = SST_OSTIA.where(SST_OSTIA!=0)
    SST_OSTIA['MASK'] = ~np.isnan(SST_OSTIA)
    SST_MERCATOR = regrid(SST_MERCATOR,husk)
    SST_MERCATOR = SST_MERCATOR.where(SST_MERCATOR!=0)
    

    # ----------------- Compute bias and model evaluation metrics ---------------- #
    print('Computing skill metrics...')
    METRICS = compute_metrics(SST_MERCATOR,SST_OSTIA)

    # ---------------------------------------------------------------------------- #
    #                                     PLOTS                                    #
    # ---------------------------------------------------------------------------- #
    print('Plotting...')
    plt.rc('font',size=12)
    # ------------------------------ make MBIAS maps ----------------------------- #
    label='Sesgo promedio '+r'($\overline{\Delta})$'+'\n'+\
        '$\Delta = TSM_{pronostico}-TSM_{satelite}$'+'\n'+'(°C)'
    fig,ax,cax,cbar = make_forecast_plot(var=METRICS['MBIAS'],
                                         cmap='RdBu_r',
                                         cbar_label=label,
                                         vmin=-2.5,vmax=2.5,level_step=0.1,
                                         xticks=[-74,-72],
                                         yticks=[-34,-33,-32,-31,-30,-29,-28],
                                         extent=ocean_mapsextent)
    
    for i,axis in enumerate(ax.ravel()):
        axis.set_title("Dia "+str(i+1), loc='left')

    cbar.ax.set_yticks(np.arange(-2.5,2.5+0.5,0.5))
    cbar.ax.tick_params(labelsize=12)
    
    ax[-1,0].text(0,-0.15,'Estadistica para el periodo: '+date_interval,
                  fontsize=10, transform=ax[-1,0].transAxes, va='top', ha='left')
    plt.savefig('plots/SST_MBIAS_DIAPRONOSTICO_MEJOR_CURRENT.png',
                dpi=150,bbox_inches='tight')
    # ------------------------------ make RMSE maps ------------------------------ #
    label='Raiz del error cuadratico medio '+r'($\sqrt{\overline{\Delta^2}})$'+\
        '\n'+'$\Delta = TSM_{pronostico}-TSM_{satelite}$'+'\n(°C)'

    fig,ax,cax,cbar = make_forecast_plot(var=METRICS['RMSE'],
                                         cmap='ocean_r',
                                         cbar_label=label,
                                         vmin=0,vmax=3,level_step=0.1,
                                         xticks=[-74,-72],
                                         yticks=[-34,-33,-32,-31,-30,-29,-28],
                                         extent=atm_mapsextent)
    
    for i,axis in enumerate(ax.ravel()):
        axis.set_title("Dia "+str(i+1), loc='left')

    cbar.ax.set_yticks(np.arange(0,3+0.5,0.5))
    cbar.ax.tick_params(labelsize=12)
    
    ax[-1,0].text(0,-0.15,'Estadistica para el periodo: '+date_interval,
                  fontsize=10, transform=ax[-1,0].transAxes, va='top', ha='left')
    plt.savefig('plots/SST_RMSE_DIAPRONOSTICO_MEJOR_CURRENT.png',
                dpi=150,bbox_inches='tight')
    
    # ----------------------- make pearson correlation maps ---------------------- #
    label='Raiz del error cuadratico medio '+r'($\sqrt{\overline{\Delta^2}})$'+\
        '\n'+'$\Delta = TSM_{pronostico}-TSM_{satelite}$'+'\n(°C)'

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
    plt.savefig('plots/SST_CORR_DIAPRONOSTICO_MEJOR_CURRENT.png',
                dpi=150,bbox_inches='tight')
    print('Done')
    return
if __name__=="__main__":
    sst_validation(N=30)
    sys.exit()
   

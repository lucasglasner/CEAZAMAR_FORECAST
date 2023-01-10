'''
 # @ Author: lucas
 # @ Create Time: 2022-08-01 11:28:36
 # @ Modified by: lucas
 # @ Modified time: 2022-08-01 11:28:49
 # @ Description:
 Script for making the CEAZAMAR wave height, direction and period forecast.
 '''

# ---------------------------------------------------------------------------- #
#                                    IMPORTS                                   #
# ---------------------------------------------------------------------------- #
import sys
import locale
locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import cartopy.crs as ccrs


from load import load_forecast_data,forecast_path, load_forecast_ini
from graphical import make_forecast_plot
from params import *

# ---------------------------------------------------------------------------- #
def wave_forecast(idate):
    fdate = pd.to_datetime(idate)+pd.Timedelta(days=NDAYS_REGIONAL)
    fdate = fdate.strftime('%F')
    print('Loading wave forecast data...')
    forecast = forecast_path(idate,'wave')
    print('          Forecast data: '+forecast)
    init  = load_forecast_ini(forecast,'wave')
    waves = load_forecast_data(forecast,'wave').isel(leadtime=slice(0,-1))
    waves = waves.resample({'leadtime':'d'}).mean()
    waves = waves.reindex({'leadtime':pd.date_range(idate,fdate,freq='d')})
    waves = waves.sel(lat=slice(*sorted(wave_mapsextent[2:])),
                      lon=slice(*sorted(wave_mapsextent[:-2])))
    
    u = np.cos(((270-waves[wavedir_name]+180)%360+180)*np.pi/180)
    v = np.sin(((270-waves[wavedir_name]+180)%360+180)*np.pi/180)
# ---------------------------------------------------------------------------- #
#                                     PLOTS                                    #
# ---------------------------------------------------------------------------- #
    print('Plotting...')
# ------------------------------------ Hm0 ----------------------------------- #
    plt.rc('font',size=12)
    vmin,vmax=1.0, 5.5
    cmap = mcolors.ListedColormap(plt.cm.nipy_spectral(np.linspace(0.1,0.95,
                                                                   1000)))
    fig,ax,cax,cbar = make_forecast_plot(var=waves[waveheight_name],
        cmap=cmap,
        cbar_label='Altura significativa \nde ola (m)',
        vmin=vmin,vmax=vmax,level_step=0.1,
        xticks=[-74,-72],
        yticks=[-34,-33,-32,-31,-30,-29,-28],
        extent=wave_mapsextent)
    
    
    cbar.ax.tick_params(labelsize=14)
    cbar.ax.set_yticks(np.arange(vmin,vmax+0.5,0.5))
    for i,axis in enumerate(ax.ravel()):
        axis.set_title(pd.to_datetime(waves.leadtime[i].values).strftime('%a %d-%b'),
                    loc='left', fontsize=13.5)
        axis.quiver(waves.lon,waves.lat,u[i].values,v[i].values, scale=12,width=0.0075,
                transform=ccrs.PlateCarree(), regrid_shape=12, alpha=0.5,
                zorder=0)
    ax[-1,0].text(0,-0.15,'Inicio pronóstico de olas: '+wave_model_name+' '+init+'\n',
                  fontsize=10, transform=ax[-1,0].transAxes, va='top', ha='left')
    ax[0,0].set_title(pd.to_datetime(waves.leadtime[0].values).strftime('%Y\n%a %d-%b'),
                    loc='left',fontsize=13.5)
    
    plt.savefig('plots/WAVEHEIGHT_FORECASTMAP_CURRENT.png',
                dpi=150,bbox_inches='tight')
    
# ---------------------------------- periodo --------------------------------- #
    plt.rc('font',size=12)
    vmin,vmax=8,21
    fig,ax,cax,cbar = make_forecast_plot(var=waves[waveperiod_name],
        cmap=sns.color_palette('mako_r', as_cmap=True),
        cbar_label='Período peak (s)',
        vmin=vmin,vmax=vmax,level_step=0.25,
        xticks=[-74,-72],
        yticks=[-34,-33,-32,-31,-30,-29,-28],
        extent=wave_mapsextent)
    

    cbar.ax.tick_params(labelsize=12)
    cbar.ax.set_yticks(np.arange(vmin,vmax+1,1))
    for i,axis in enumerate(ax.ravel()):
        axis.set_title(pd.to_datetime(waves.leadtime[i].values).strftime('%a %d-%b'),
                    loc='left', fontsize=13.5)
        axis.quiver(waves.lon,waves.lat,u[i].values,v[i].values, scale=12,width=0.0075,
                transform=ccrs.PlateCarree(), regrid_shape=12, alpha=0.5,
                zorder=0, lw=0.5)
    ax[-1,0].text(0,-0.15,'Inicio pronóstico de olas: '+wave_model_name+' '+init+'\n',
                  fontsize=10, transform=ax[-1,0].transAxes, va='top', ha='left')
    ax[0,0].set_title(pd.to_datetime(waves.leadtime[0].values).strftime('%Y\n%a %d-%b'),
                    loc='left',fontsize=13.5)
    

    plt.savefig('plots/PERIOD_FORECASTMAP_CURRENT.png',
                dpi=150,bbox_inches='tight')
    print('Done')
    return

if __name__=='__main__':
    wave_forecast(FORECAST_DATE)
    sys.exit()

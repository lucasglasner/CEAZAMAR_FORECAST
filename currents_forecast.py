'''
 # @ Author: lucas
 # @ Create Time: 2022-08-09 17:09:59
 # @ Modified by: lucas
 # @ Modified time: 2022-08-09 17:59:21
 # @ Description:
  Script for making the CEAZAMAR surface currents and SSH forecast.
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
import cmocean
import seaborn as sns
import cartopy.crs as ccrs

from load import load_forecast_data,forecast_path,load_forecast_ini
from graphical import make_forecast_plot
from params import *

# ---------------------------------------------------------------------------- #
def currents_forecast(idate):
    print('Loading currents and SSH forecast data...')
    forecast = forecast_path(idate,'ocean')
    print('          Forecast data: '+forecast)
    fdate = pd.to_datetime(idate)+pd.Timedelta(days=NDAYS_REGIONAL)
    fdate = fdate.strftime('%F')
    init  = load_forecast_ini(forecast,'ocean')
    

    data = load_forecast_data(forecast,'ocean')[[uo_name,
                                                 vo_name,
                                                 ssh_name]]
    data = data.resample({'leadtime':'d'}).mean()
    data = data.reindex({'leadtime':pd.date_range(idate,fdate,freq='d')})
    uo,vo = data[uo_name],data[vo_name]
    data['cs'] = np.hypot(uo,vo)


# ---------------------------------------------------------------------------- #
#                                     PLOTS                                    #
# ---------------------------------------------------------------------------- #
    print('Plotting...')
# ------------------------------------ SSH ----------------------------------- #
    plt.rc('font',size=12)
    vmin,vmax=-15,15
    fig,ax,cax,cbar = make_forecast_plot(var=data[ssh_name]*100,
        cmap=cmocean.cm.balance,
        cbar_label='Anomalía del nivel del mar (cm)',
        vmin=vmin,vmax=vmax,level_step=0.5,
        xticks=[-73,-71],
        yticks=[-34,-33,-32,-31,-30,-29,-28,-27],
        extent=[-74,-70.5,-34,-27])
    
    
    cbar.ax.tick_params(labelsize=14)
    cbar.ax.set_yticks(np.arange(vmin,vmax+2.5,2.5))
    for i,axis in enumerate(ax.ravel()):
        axis.set_title(pd.to_datetime(data.leadtime[i].values).strftime('%a %d-%b'),
                    loc='left', fontsize=13.5)
        axis.quiver(data.lon,data.lat,uo[i].values,vo[i].values, scale=3,width=0.008,
                transform=ccrs.PlateCarree(), regrid_shape=14, alpha=0.7,
                zorder=0)

    ax[-1,0].text(0,-0.15,'Inicio pronóstico océanico: '+ocean_model_name+' '+init+'\n',
                  fontsize=10, transform=ax[-1,0].transAxes, va='top', ha='left')
    
    ax[0,0].set_title(pd.to_datetime(data.leadtime[0].values).strftime('%Y\n%a %d-%b'),
                    loc='left',fontsize=13.5)
    
    plt.savefig('plots/SEALEVEL_ANOMALY_FORECASTMAP_CURRENT.png',
                dpi=150,bbox_inches='tight')
# --------------------------------- CURRENTS --------------------------------- #
    plt.rc('font',size=12)
    vmin,vmax=0,50
    fig,ax,cax,cbar = make_forecast_plot(var=data['cs']*100,
        cmap='PuBu',
        cbar_label='Líneas de corriente y velocidad (cm/s)',
        vmin=vmin,vmax=vmax,level_step=0.5,
        xticks=[-73,-71],
        yticks=[-34,-33,-32,-31,-30,-29,-28,-27],
        extent=[-74,-70.5,-34,-27])
    
    cbar.ax.tick_params(labelsize=14)
    cbar.ax.set_yticks(np.arange(vmin,vmax+5,5))
    for i,axis in enumerate(ax.ravel()):
        axis.set_title(pd.to_datetime(data.leadtime[i].values).strftime('%a %d-%b'),
                    loc='left', fontsize=13.5)
        # axis.quiver(data.lon,data.lat,uo[i].values,vo[i].values, scale=3,width=0.008,
        #         transform=ccrs.PlateCarree(), regrid_shape=14, alpha=0.7,
        #         zorder=0)
        axis.streamplot(data.lon,data.lat,uo[i].values, vo[i].values, density=1.5,
                transform=ccrs.PlateCarree(), zorder=0, color='k', linewidth=0.5,
                arrowsize=0.5)

    ax[-1,0].text(0,-0.15,'Inicio pronóstico océanico: '+ocean_model_name+' '+init+'\n',
                  fontsize=10, transform=ax[-1,0].transAxes, va='top', ha='left')
    
    ax[0,0].set_title(pd.to_datetime(data.leadtime[0].values).strftime('%Y\n%a %d-%b'),
                    loc='left',fontsize=13.5)
    
    plt.savefig('plots/SURFACECURRENTS_FORECASTMAP_CURRENT.png',
                dpi=150,bbox_inches='tight')
    print('Done')
    
    return

if __name__=='__main__':
    currents_forecast(FORECAST_DATE)
    sys.exit()
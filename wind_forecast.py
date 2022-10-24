'''
 # @ Author: lucas
 # @ Create Time: 2022-08-01 11:28:36
 # @ Modified by: lucas
 # @ Modified time: 2022-08-01 11:28:49
 # @ Description:
 Script for making the CEAZAMAR wind speed and direction forecast.
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
from colormap import Colormap
import cartopy.crs as ccrs


from load import load_forecast_data,forecast_path, load_forecast_ini
from graphical import make_forecast_plot
from params import *


# ---------------------------------------------------------------------------- #
def wind_forecast(idate):
    print('Loading wind forecast data...')
    forecast = forecast_path(idate,'atm')
    print('          Forecast data: '+forecast)
    fdate = pd.to_datetime(idate)+pd.Timedelta(days=NDAYS_REGIONAL)
    fdate = fdate.strftime('%F')
    
    
    wind = load_forecast_data(forecast,'atm')[[uwnd_name,vwnd_name]]
    wind = wind.resample({'leadtime':'d'}).mean()
    wind = wind.reindex({'leadtime':pd.date_range(idate,fdate,freq='d')})
    init  = load_forecast_ini(forecast,'atm')
    # wind = wind.sel(lat=slice(*sorted(atm_mapsextent[2:])),
    #                 lon=slice(*sorted(atm_mapsextent[:-2])))
    
    
    wind['WS'] = np.hypot(wind[uwnd_name],wind[vwnd_name])
    u = wind[uwnd_name]/wind['WS']
    v = wind[vwnd_name]/wind['WS']
# ---------------------------------------------------------------------------- #
#                                     PLOTS                                    #
# ---------------------------------------------------------------------------- #
    print('Plotting...')
# ------------------------------------ wind ---------------------------------- #
    plt.rc('font',size=12)
    vmin,vmax=0,15.
    fig,ax,cax,cbar = make_forecast_plot(var=wind['WS'],
        cmap='viridis',
        cbar_label='Velocidad del viento (m/s)',
        vmin=vmin,vmax=vmax,level_step=0.1,
        xticks=[-73,-71],
        yticks=[-34,-33,-32,-31,-30,-29,-28],
        extent=atm_mapsextent)
    
    
    cbar.ax.tick_params(labelsize=14)
    cbar.ax.set_yticks(np.arange(vmin,vmax+1,1))
    for i,axis in enumerate(ax.ravel()):
        axis.set_title(pd.to_datetime(wind.leadtime[i].values).strftime('%a %d-%b'),
                    loc='left', fontsize=13.5)
        axis.quiver(wind.lon,wind.lat,u[i].values,v[i].values, scale=12,width=0.01,
                transform=ccrs.PlateCarree(), regrid_shape=12, alpha=0.7,
                zorder=0)

    ax[0,0].set_title(pd.to_datetime(wind.leadtime[0].values).strftime('%Y\n%a %d-%b'),
                    loc='left',fontsize=13.5)
    
    ax[-1,0].text(0,-0.15,'Inicio pronóstico atmosférico: '+atm_model_name+' '+init+'\n',
                  fontsize=10, transform=ax[-1,0].transAxes, va='top', ha='left')
    plt.savefig('plots/WINDSPEED_FORECASTMAP_CURRENT.png',
                dpi=150,bbox_inches='tight')
    
    print('Done')
    return

if __name__=='__main__':
    wind_forecast(FORECAST_DATE)
    sys.exit()
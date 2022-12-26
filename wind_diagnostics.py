'''
 # @ Author: lucasg
 # @ Create Time: 2022-12-26 16:33:10
 # @ Modified by: lucasg
 # @ Modified time: 2022-12-26 16:33:18
 # @ Description:
  Script for making wind diagnostics based on altimeter data and 
 ASCAT L4 NRT gridded dataset.
 '''

 



# ---------------------------------------------------------------------------- #
#                                    IMPORTS                                   #
# ---------------------------------------------------------------------------- #
import sys
from glob import glob
import datetime
import locale
locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')

import pandas as pd
import numpy as np
import xarray as xr

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs


from load import load_altimeters, load_ascat
from graphical import make_maps
from numerics import fill_borders
from params import *


def wind_diagnostics(idate):
    now = datetime.datetime.now()
    # --------------------------------- load data -------------------------------- #
    print('Loading ASCAT wind data...')
    winds = load_ascat(idate)
    winds = winds.squeeze()

    # u = -np.cos(winds[winddir_name]*np.pi/180)
    # v = -np.sin(winds[winddir_name]*np.pi/180)
    
    altimeters_data = load_altimeters(idate, centerhour=12, hwidth=6)[['lat','lon', windspeed_name]]
    # ---------------------------------------------------------------------------- #
    # ----------------------------------- PLOTS ---------------------------------- #
    # ---------------------------------------------------------------------------- #
    print('Plotting...')
    plt.rc('font',size=12)
    vmin,vmax=0, 15
    fig, ax, cax =  make_maps((1,1), figsize=(14,8), 
                              extent=diagnostics_mapsextent)
    
    m=ax.contourf(winds.lon, winds.lat, fill_borders(winds[windspeed_name]),
                  cmap='viridis', extend='both', levels=np.arange(vmin,vmax+0.5,0.5))

    cbar=fig.colorbar(m, cax=cax, label='Velocidad del viento (m/s)')
    
    # ax.set_title(pd.to_datetime(winds.time.item()), loc='left', fontsize=13.5)
    ax.set_title('DIAGNOSTICO DE VELOCIDAD DEL VIENTO\nASCAT: '+
                 pd.to_datetime(winds.time.item()).strftime('%F %H:%M'),
                 loc='left', fontsize=13.5)
    cbar.ax.tick_params(labelsize=14)
    cbar.ax.set_yticks(np.arange(vmin,vmax+1,1))
    
    for a in altimeters_data.index.get_level_values(0).unique():
        data = altimeters_data.loc[a]
        data = data.where(data['lon']>=diagnostics_mapsextent[0])
        data = data.where(data['lon']<=diagnostics_mapsextent[1])
        data = data.where(data['lat']>=diagnostics_mapsextent[2])
        data = data.where(data['lat']<=diagnostics_mapsextent[3])
        data = data.dropna()

        ax.plot(data.lon+0.1, data.lat, color='k', zorder=1,
                transform=ccrs.Geodetic(), lw=1.5)
        ax.plot(data.lon-0.1, data.lat, color='k', zorder=1,
                transform=ccrs.Geodetic(), lw=1.5)
        
        ax.scatter(data.lon,data.lat,c=data[windspeed_name],
                    cmap='viridis', vmin=vmin, vmax=vmax, s=40,
                    marker='s', zorder=2)

        n = len(data)
        if n==0:
            continue
        text = data.sort_values(by='lat')
        text = text[5:-5].iloc[::40]
        for i,lon,lat in zip(range(len(text)),
                            text.lon,
                            text.lat):
            ax.text(lon-0.2, lat,
                    a.upper()+'\n'+text.index[i].strftime("%H:%M:%S"),
                    transform=ax.transData,
                    fontsize=8, ha='right')

    
    plt.savefig('plots/WINDSPEED_DIAGNOSTICMAP_CURRENT.png',
                dpi=150,bbox_inches='tight')
    
    print('Done')
    return
    
    
if __name__=='__main__':
    wind_diagnostics((pd.to_datetime(FORECAST_DATE)-pd.Timedelta(days=2)).strftime('%F'))
    sys.exit()

    
'''
 # @ Author: lucasg
 # @ Create Time: 2022-12-23 16:03:22
 # @ Modified by: lucasg
 # @ Modified time: 2022-12-23 16:03:51
 # @ Description:
 Script for making wave diagnostics based on altimeter data and 
 MERCATOR hindcast.
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


from load import load_forecast_data, load_altimeters
from graphical import make_maps
from numerics import fill_borders
from params import *


def wave_diagnostics(idate):
    now = datetime.datetime.now()
    # --------------------------------- load data -------------------------------- #
    print('Loading wave hindcast data...')
    hindcast = wave_hindcast_dir+'/'+idate+'.nc'
    print('          Hindcast data: '+hindcast)
    waves = load_forecast_data(hindcast, 'wave')
    waves = waves.sel(leadtime=idate+'T{:02d}'.format(now.hour), method='nearest')
    
    u = -np.cos(waves[wavedir_name]*np.pi/180)
    v = -np.sin(waves[wavedir_name]*np.pi/180)
    
    altimeters_data = load_altimeters(idate)[['lat','lon',waveheight_name]]
    # altimeters_data = altimeters_data.where(altimeters_data['lon']>=extent[0])
    # altimeters_data = altimeters_data.where(altimeters_data['lon']<=extent[1])
    # altimeters_data = altimeters_data.where(altimeters_data['lat']>=extent[2])
    # altimeters_data = altimeters_data.where(altimeters_data['lat']<=extent[3])
    # altimeters_data = altimeters_data.dropna()

    # ---------------------------------------------------------------------------- #
    # ----------------------------------- PLOTS ---------------------------------- #
    # ---------------------------------------------------------------------------- #
    print('Plotting...')
    plt.rc('font',size=12)
    vmin,vmax=1.0, 5.5
    cmap = mcolors.ListedColormap(plt.cm.nipy_spectral(np.linspace(0.1,0.95,
                                                                   1000)))
    fig, ax, cax =  make_maps((1,1), figsize=(14,8), 
                              extent=diagnostics_mapsextent)
    
    m=ax.contourf(waves.lon, waves.lat, fill_borders(waves[waveheight_name]),
                  cmap=cmap, extend='both', levels=np.arange(1,5.5+0.1,0.1))
    cbar=fig.colorbar(m, cax=cax, label='Altura significativa de ola (m)')
    

    ax.quiver(waves.lon,waves.lat,u.values,v.values, scale=25,width=0.003,
              transform=ccrs.PlateCarree(), regrid_shape=25, alpha=0.35)
    # ax.set_title(pd.to_datetime(waves.time.item()), loc='left', fontsize=13.5)
    ax.set_title('DIAGNOSTICO DE ALTURA DE OLAS\n'+wave_model_name+' Hindcast: '+
                 pd.to_datetime(waves.leadtime.item()).strftime('%F %H:%M:%S'),
                loc='left',fontsize=13.5)
    cbar.ax.tick_params(labelsize=14)
    cbar.ax.set_yticks(np.arange(vmin,vmax+0.5,0.5))
    
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
        
        ax.scatter(data.lon,data.lat,c=data[waveheight_name],
                    cmap=cmap, vmin=vmin, vmax=vmax, s=40,
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
                    fontsize=10, ha='right')

    
    plt.savefig('plots/WAVEHEIGHT_DIAGNOSTICMAP_CURRENT.png',
                dpi=150,bbox_inches='tight')
    
    print('Done')
    return
    
    
if __name__=='__main__':
    wave_diagnostics((pd.to_datetime(FORECAST_DATE)-pd.Timedelta(days=4)).strftime('%F'))
    sys.exit()

    
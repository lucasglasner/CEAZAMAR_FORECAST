'''
 # @ Author: lucasg
 # @ Create Time: 2022-12-30 16:59:29
 # @ Modified by: lucasg
 # @ Modified time: 2022-12-30 16:59:42
 # @ Description:
 This script uses the latest forecast data to create a figure 
 with the regional condition of the current hour.
 '''

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
import cmocean
import cartopy.crs as ccrs


from load import forecast_path, load_forecast_data
from graphical import make_maps
from numerics import fill_borders, utc_to_local
from params import *

import fuckit

@fuckit
def nrt_forecast(idate):
    now = datetime.datetime.now()
    extent = [-75, -70.5, -34, -28]
    # --------------------------------- load data -------------------------------- #
    #Load ocean data
    print('Loading SST and currents forecast data...')
    ocean = forecast_path(idate, 'ocean')
    print('          Ocean forecast data: '+ocean)
    ocean = load_forecast_data(ocean, 'ocean').squeeze().load()
    ocean.coords['leadtime'] = ('leadtime',
                                utc_to_local(ocean.leadtime.to_series()).index)
    time  = pd.date_range(idate+'T00:00',idate+'T23:59', freq='h')
    ocean = ocean.reindex({'leadtime':time}, method='nearest')
    ocean = ocean.sel(leadtime=idate+'T{:02d}'.format(now.hour), method='nearest')
    ocean = ocean.sel(lat=slice(extent[2], extent[3]),
                      lon=slice(extent[0], extent[1]))
    sst   = ocean[sst_name]
    cs    = np.hypot(ocean[uo_name],ocean[vo_name])
    #Load wave data
    print('Loading wave forecast data...')
    waves = forecast_path(idate,'wave')
    print('          Waves forecast data: '+waves)
    waves = load_forecast_data(waves, 'wave').isel(leadtime=slice(0,-1))
    waves.coords['leadtime'] = ('leadtime',
                                utc_to_local(waves.leadtime.to_series()).index)
    waves = waves.reindex({'leadtime':time}, method='nearest')
    waves = waves.sel(leadtime=idate+'T{:02d}'.format(now.hour), method='nearest')
    
    #Load wind data
    print('Loading wind forecast data...')
    winds = forecast_path(idate, 'atm')
    print('          Atmosphere forecast data: '+winds)
    winds = load_forecast_data(winds, 'atm')[[uwnd_name,vwnd_name]]  
    winds.coords['leadtime'] = ('leadtime',
                                utc_to_local(winds.leadtime.to_series()).index)
    winds = winds.reindex({'leadtime':time}, method='nearest') 
    winds = winds.sel(leadtime=idate+'T{:02d}'.format(now.hour), method='nearest')
    winds[windspeed_name] = np.hypot(winds[uwnd_name],winds[vwnd_name])
    # ---------------------------------------------------------------------------- #
    # ----------------------------------- PLOTS ---------------------------------- #
    # ---------------------------------------------------------------------------- #
    print('Plotting...')
    fig, ax, cax =  make_maps((1,3), figsize=(18,9),
                              extent=extent)
    cax.axis('off')
    vmin,vmax=0, 15
    cmap='viridis'
    m=ax[0,0].contourf(winds.XLONG, winds.XLAT, fill_borders(winds[windspeed_name]),
                     cmap=cmap, extend='both', levels=np.arange(vmin,vmax+0.5,0.5))
    ax[0,0].quiver(winds.lon,winds.lat,
                   winds[uwnd_name].values,
                   winds[vwnd_name].values,
              scale=220,width=0.0035,
              transform=ccrs.PlateCarree(), regrid_shape=30, alpha=0.5)

    fig.colorbar(m, ax=ax[0,0], orientation='horizontal', pad=0.01,
                 label='Velocidad del viento (m/s)')
    
    vmin,vmax = sst.min()-sst.min()%0.5+0.5,sst.max()-sst.max()%0.5
    cmap = cmocean.cm.thermal
    m=ax[0,1].contourf(sst.lon, sst.lat, fill_borders(sst),
                  cmap=cmap, extend='both', levels=np.arange(vmin,
                                                             vmax+0.1,
                                                             0.1))
    fig.colorbar(m, ax=ax[0,1], orientation='horizontal', pad=0.01,
                 label='Temperatura superficial del mar (°C)')
    
    vmin,vmax=1.0, 5.5
    cmap = mcolors.ListedColormap(plt.cm.nipy_spectral(np.linspace(0.1,0.95,
                                                                   1000)))
    m=ax[0,2].contourf(waves.lon, waves.lat, fill_borders(waves[waveheight_name]),
                  cmap=cmap, extend='both', levels=np.arange(vmin,vmax+0.1,0.1))
    u = -np.cos(waves[wavedir_name]*np.pi/180)
    v = -np.sin(waves[wavedir_name]*np.pi/180)
    ax[0,2].quiver(waves.lon,waves.lat,u.values,v.values, scale=25,width=0.003,
              transform=ccrs.PlateCarree(), regrid_shape=25, alpha=0.35)
    fig.colorbar(m, ax=ax[0,2], orientation='horizontal', pad=0.01,
                 label='Altura significativa de ola (m)')
    ax[0,1].text(0.5, 1.17,
                 'Condiciones atmosféricas y oceanográficas Chile Centro-Norte',
                 transform=ax[0,1].transAxes,
                 ha='center',
                 weight='bold', fontsize=13)
    
    text = (pd.to_datetime(idate)+pd.Timedelta(hours=now.hour)).strftime('%F\n%H:%M (UTC-4)')
    ax[0,1].text(0.5, 1.05,
                 text,
                 transform=ax[0,1].transAxes,
                 ha='center', fontsize=15)
    ax[0,1].text(0.5, 1.01,
                 'Fuente: WRF-Ceaza y MERCATOR-Ocean',
                 transform=ax[0,1].transAxes,
                 ha='center', fontsize=8)

    
    plt.savefig('plots/NRTFORECAST_CURRENT.png', dpi=150, bbox_inches='tight')
    print('Done')
    return

if __name__ == '__main__':
    nrt_forecast(FORECAST_DATE)

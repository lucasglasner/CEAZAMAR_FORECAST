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


from load import load_altimeters, load_ccmp, forecast_path, load_forecast_data
from graphical import make_maps
from numerics import fill_borders, utc_to_local
from params import *

import fuckit

@fuckit
def wind_diagnostics(idate):
    now = datetime.datetime.now()
    # --------------------------------- load data -------------------------------- #
    print('Loading CCMP wind data...')
    winds = load_ccmp(idate)
    winds.coords['leadtime'] = ('leadtime',
                                utc_to_local(winds.time.to_series()).index)
    time  = pd.date_range(idate+'T00:00',idate+'T23:59', freq='h')
    winds = winds.reindex({'time':time}, method='nearest')
    winds = winds.sel(time=idate+'T{:02d}'.format(now.hour), method='nearest')
    winds = winds.squeeze()
    
    altimeters_data = load_altimeters(idate)[['lat','lon', windspeed_name]]
    # ---------------------------------------------------------------------------- #
    # ----------------------------------- PLOTS ---------------------------------- #
    # ---------------------------------------------------------------------------- #
    print('Plotting...')
    plt.rc('font',size=12)
    vmin,vmax=0, 15
    cmap='viridis'
    fig, ax, cax =  make_maps((1,1), figsize=(14,8), 
                              extent=diagnostics_mapsextent)
    
    m=ax.contourf(winds.lon, winds.lat, fill_borders(winds[windspeed_name]),
                  cmap=cmap, extend='both', levels=np.arange(vmin,vmax+0.5,0.5))

    cbar=fig.colorbar(m, cax=cax, label='(m/s)')

    
    ax.quiver(winds.lon,winds.lat,winds[uwnd_name].values,winds[vwnd_name].values,
              scale=350,width=0.0025,
              transform=ccrs.PlateCarree(), regrid_shape=30, alpha=0.5)
    # ax.set_title(pd.to_datetime(winds.time.item()), loc='left', fontsize=13.5)
    ax.set_title('Diagnóstico de\nvelocidad del viento.',
                 loc='left', fontsize=14)    
    ax.text(1, 1.01,
            pd.to_datetime(winds.time.item()).strftime('%Y-%m-%d\nHora: %H:%M'),
            transform=ax.transAxes, fontsize=14, ha='right')
    ax.text(0,-0.025, 'Fuente: Cross-Calibrated Multi-Platform '+
            '(CCMP) Wind analysis + Altimetros.',
            fontsize=10, ha='left',
            transform=ax.transAxes)

    cbar.ax.tick_params(labelsize=14)
    cbar.ax.set_yticks(np.arange(vmin,vmax+1,1))
    
     
    for a in altimeters_data.index.get_level_values(0).unique():
        try:
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
                        a.upper()+'\n'+text.index[i].strftime("%H:%M"),
                        transform=ax.transData,
                        fontsize=10, ha='right')
        except:
            pass
    
    plt.savefig('plots/WINDSPEED_DIAGNOSTICMAP_CURRENT.png',
                dpi=150,bbox_inches='tight')
    
    print('Done')
    return
    
    
if __name__=='__main__':
    wind_diagnostics((pd.to_datetime(FORECAST_DATE)-pd.Timedelta(days=1)).strftime('%F'))
    sys.exit()

    

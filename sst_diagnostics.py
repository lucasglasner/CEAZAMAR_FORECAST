'''
 # @ Author: Your name
 # @ Create Time: 2022-12-26 17:04:10
 # @ Modified by: Your name
 # @ Modified time: 2022-12-26 17:04:14
 # @ Description:
  Script for making SST diagnostics based on OSTIA dataset.
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


from load import load_ostia
from graphical import make_maps
from numerics import fill_borders
from params import *


def sst_diagnostics(idate):
    # --------------------------------- load data -------------------------------- #
    daysago = pd.to_datetime(idate)-pd.Timedelta(days=10)
    daysago = daysago.strftime('%F')
    print('Loading OSTIA SST data...')
    sst = [load_ostia(d) for d in pd.date_range(daysago, idate, freq='d')]
    sst = xr.concat(sst, 'time')
    sst.coords['days'] = ('time',np.arange(1,len(sst.time)+1,1))

    trend = sst.swap_dims({'time':'days'}).polyfit(dim='days', deg=1).sel(degree=1)
    trend = trend.polyfit_coefficients

    # ---------------------------------------------------------------------------- #
    # ----------------------------------- PLOTS ---------------------------------- #
    # ---------------------------------------------------------------------------- #
    # ---------------------------------- raw tsm --------------------------------- #
    print('Plotting...')
    plt.rc('font',size=12)
    vmin,vmax = sst.min()-sst.min()%0.5,sst.max()-sst.max()%0.5
    fig, ax, cax =  make_maps((1,1), figsize=(14,8), 
                              extent=diagnostics_mapsextent)
    
    m=ax.contourf(sst.lon, sst.lat, fill_borders(sst.isel(time=-1)),
                  cmap=cmocean.cm.thermal, extend='both', levels=np.arange(vmin,
                                                                           vmax+0.25,
                                                                           0.25))

    cbar=fig.colorbar(m, cax=cax, label='Temperatura superficial del mar (°C)')
    
    # ax.set_title(pd.to_datetime(ssts.time.item()), loc='left', fontsize=13.5)
    ax.set_title('DIAGNOSTICO DE TEMPERATURA SUPERFICIAL DEL MAR\nTSM (OSTIA): '+
                 pd.to_datetime(sst.time[-1].item()).strftime('%F'),
                 loc='left', fontsize=13.5)
    cbar.ax.tick_params(labelsize=14)
    cbar.ax.set_yticks(np.arange(vmin,vmax,1))

    plt.savefig('plots/SST_DIAGNOSTICMAP_CURRENT.png',
                dpi=150,bbox_inches='tight')
    
    # ---------------------------- last 10 days trend ---------------------------- #
    vmin,vmax = -0.5,0.5
    fig, ax, cax =  make_maps((1,1), figsize=(14,8), 
                              extent=diagnostics_mapsextent)
    
    m=ax.contourf(trend.lon, trend.lat, fill_borders(trend),
                  cmap='RdBu_r', extend='both', levels=np.arange(vmin,
                                                                 vmax+0.025,
                                                                 0.025))

    cbar=fig.colorbar(m, cax=cax, label='Tendencia de TSM (últimos 10 días) (°C/dia)')
    
    # ax.set_title(pd.to_datetime(ssts.time.item()), loc='left', fontsize=13.5)
    ax.set_title('DIAGNOSTICO DE TEMPERATURA SUPERFICIAL DEL MAR\nTendencia TSM (OSTIA): '+
                 pd.to_datetime(sst.time[0].item()).strftime('%F')+'  /  '+
                 pd.to_datetime(sst.time[-1].item()).strftime('%F'),
                 loc='left', fontsize=13.5)
    cbar.ax.tick_params(labelsize=14)
    cbar.ax.set_yticks(np.arange(vmin,vmax+0.1,0.1))

    plt.savefig('plots/SSTTREND_DIAGNOSTICMAP_CURRENT.png',
                dpi=150,bbox_inches='tight')
    
    print('Done')
    return
    
    
if __name__=='__main__':
    sst_diagnostics((pd.to_datetime(FORECAST_DATE)-pd.Timedelta(days=1)).strftime('%F'))
    sys.exit()

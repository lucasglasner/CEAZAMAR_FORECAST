'''
 # @ Author: Your name
 # @ Create Time: 2022-12-26 17:04:10
 # @ Modified by: Your name
 # @ Modified time: 2022-12-26 17:04:14
 # @ Description:
  Script for making SST diagnostics based on OSTIA dataset.
 '''

import os
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
    sst_clim = xr.open_dataset(ocean_climatology_file)['sst_ostia']
    sst = [load_ostia(d) for d in pd.date_range(daysago, idate, freq='d')]
    mask = [False if v is None else True for v in sst]
    sst = xr.concat(np.array(sst)[mask], 'time')
    sst.coords['days'] = ('time',np.arange(1,len(sst.time)+1,1))    
    
    sst_anomaly = sst.convert_calendar('noleap').groupby('time.dayofyear')-sst_clim
    
    trend = sst_anomaly.swap_dims({'time':'days'}).polyfit(dim='days',
                                                   deg=1).sel(degree=1)
    trend = trend.polyfit_coefficients
    
    

    # ---------------------------------------------------------------------------- #
    # ----------------------------------- PLOTS ---------------------------------- #
    # ---------------------------------------------------------------------------- #
    # ---------------------------------- raw tsm --------------------------------- #
    print('Plotting...')
    plt.rc('font',size=12)
    vmin,vmax = sst.min()-sst.min()%0.5+1,sst.max()-sst.max()%0.5-0.5
    fig, ax, cax =  make_maps((1,1), figsize=(14,8), 
                              extent=diagnostics_mapsextent)
    
    m=ax.contourf(sst.lon, sst.lat, fill_borders(sst.isel(time=-1)),
                  cmap=cmocean.cm.thermal, extend='both', levels=np.arange(vmin,
                                                                           vmax+0.25,
                                                                           0.25))

    cbar=fig.colorbar(m, cax=cax, label='(°C)')
    ax.set_title('Diagnóstico de temperatura\nsuperficial del mar.\n'+
                 pd.to_datetime(sst.time[-1].item()).strftime('%F'),
                 loc='left', fontsize=14)    
#    ax.text(1, 1.01,
#            pd.to_datetime(sst.time[-1].item()).strftime('%Y-%m-%d')+'\n',
#            transform=ax.transAxes, fontsize=14, ha='right')
    ax.text(0,-0.05, 'Fuente: Operational Sea Surface Temperature and Sea Ice\nAnalysis (OSTIA)',
            fontsize=10, ha='left',
            transform=ax.transAxes)
    cbar.ax.tick_params(labelsize=14)
    cbar.ax.set_yticks(np.arange(vmin,vmax+1,1))

    plt.savefig('plots/SST_DIAGNOSTICMAP_CURRENT.png',
                dpi=150,bbox_inches='tight')
    # -------------------------------- sstanomaly -------------------------------- #
    plt.rc('font',size=12)
    vmin,vmax = -4,4
    import cmaps
    fig, ax, cax =  make_maps((1,1), figsize=(14,8), 
                              extent=diagnostics_mapsextent)
    
    m=ax.contourf(sst.lon, sst.lat, fill_borders(sst_anomaly.isel(time=-1)),
                  cmap='RdBu_r', extend='both', levels=np.arange(vmin,
                                                                 vmax+0.1,
                                                                 0.1))

    cbar=fig.colorbar(m, cax=cax, label='(°C)')
 #   ax.set_title('Diagnóstico de anomalías de \ntemperatura superficial del mar.',
 #                loc='left', fontsize=14)    
    ax.set_title('Diagnóstico de anomalías de \ntemperatura superficial del mar.\n'+
                 pd.to_datetime(sst.time[-1].item()).strftime('%F'),
                 loc='left', fontsize=14)        
#    ax.text(1, 1.01,
#            pd.to_datetime(sst.time[-1].item()).strftime('%Y-%m-%d')+'\n',
#            transform=ax.transAxes, fontsize=14, ha='right')
    ax.text(0,-0.05, 'Fuente: Operational Sea Surface Temperature and Sea Ice\nAnalysis (OSTIA)',
            fontsize=10, ha='left',
            transform=ax.transAxes)
    cbar.ax.tick_params(labelsize=14)
    cbar.ax.set_yticks(np.arange(vmin,vmax+1,1))

    plt.savefig('plots/SSTANOMALY_DIAGNOSTICMAP_CURRENT.png',
                dpi=150,bbox_inches='tight')
    # ---------------------------- last 10 days trend ---------------------------- #
    vmin,vmax = -0.5,0.5
    fig, ax, cax =  make_maps((1,1), figsize=(14,8), 
                              extent=diagnostics_mapsextent)
    
    m=ax.contourf(trend.lon, trend.lat, fill_borders(trend),
                  cmap='RdBu_r', extend='both', levels=np.arange(vmin,
                                                                 vmax+0.025,
                                                                 0.025))

    cbar=fig.colorbar(m, cax=cax, label='(°C/dia)')
#   ax.set_title('Tendencia de temperatura\nsuperficial del mar (últimos 10 días).',
#                 loc='left', fontsize=14)    
#                 loc='left', fontsize=14)    
    ax.set_title('Tendencia de temperatura\nsuperficial del mar (últimos 10 días).\n'+
                 pd.to_datetime(sst.time[-1].item()).strftime('%F'),
                 loc='left', fontsize=14)          
#    ax.text(1, 1.01,
#            pd.to_datetime(sst.time[-1].item()).strftime('%Y-%m-%d')+'\n',
#            transform=ax.transAxes, fontsize=14, ha='right')
    ax.text(0,-0.05, 'Fuente: Operational Sea Surface Temperature and Sea\nIce Analysis (OSTIA)',
            fontsize=10, ha='left',
            transform=ax.transAxes)
    cbar.ax.tick_params(labelsize=14)
    cbar.ax.set_yticks(np.arange(vmin,vmax+0.1,0.1))

    plt.savefig('plots/SSTTREND_DIAGNOSTICMAP_CURRENT.png',
                dpi=150,bbox_inches='tight')
    
    
    #Concatenate images in one!
    sstdiag  = plt.imread('plots/SST_DIAGNOSTICMAP_CURRENT.png', format='png')
    sstdiag  = np.concatenate([sstdiag, np.ones(sstdiag.shape)[:,:100]],axis=1)
    
    sstadiag = plt.imread('plots/SSTANOMALY_DIAGNOSTICMAP_CURRENT.png', format='png')
    sstadiag = np.concatenate([sstadiag, np.ones(sstadiag.shape)[:,:100]],axis=1)
    
    ssttrend = plt.imread('plots/SSTTREND_DIAGNOSTICMAP_CURRENT.png', format='png')
    ssttrend = np.concatenate([ssttrend, np.ones(ssttrend.shape)[:,:100]],axis=1)
    
    fig=plt.figure(figsize=(14,8))
    img = np.concatenate([sstdiag, sstadiag, ssttrend], axis=1)
    plt.imshow(img)
    plt.axis('off')
    plt.savefig('plots/SST_DIAGNOSTICMAP_CURRENT.png', dpi=300, bbox_inches='tight')
    os.remove('plots/SSTANOMALY_DIAGNOSTICMAP_CURRENT.png')
    os.remove('plots/SSTTREND_DIAGNOSTICMAP_CURRENT.png')
    
    
    print('Done')
    return
    
    
if __name__=='__main__':
    sst_diagnostics((pd.to_datetime(FORECAST_DATE)-pd.Timedelta(days=1)).strftime('%F'))
#     sst_diagnostics("2022-05-01")
    sys.exit()

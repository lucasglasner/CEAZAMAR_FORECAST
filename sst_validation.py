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

from load import target_date, load_mercator
from numerics import regrid, compute_metrics, fill_borders, bias_correct_SST
from graphical import make_maps
from params import *


# ------------------------- Script specific functions ------------------------ #
def load_data(times, bbox=[-73,-70.67,-33,-27]):
    """
    Go to find forecast and validation data for a collection of 
    dates, and shrink them to the desired spatial extent.

    Args:
        times datetime:
         A collection of datetime objects
        bbox (list, optional): Bounding box (lat-lon).
         Defaults to [-73,-70.5,-33,-27].

    Returns:
        (tuple): Loaded forecast and validation data
    """
    lon1,lon2,lat1,lat2 = bbox
    SST_OSTIA = []
    SST_MERCATOR = []
    for p in times:
        ostia_path = 'data/OSTIA/'+p.strftime('%Y%m%d')+\
            '-UKMO-L4HRfnd-GLOB-v01-fv02-OSTIA.nc'
        forecast_path = ocean_forecast_dir+'/'+\
            p.strftime('%Y-%m-%d.nc')
        try:
            data = xr.open_dataset(ostia_path).analysed_sst;
            data = data.sel(lat=slice(lat1,lat2), lon=slice(lon1,lon2))-273.15
            data = data.resample({'time':'d'}).mean()
            SST_OSTIA.append(data)
        except Exception as e:
            print('         File "'+ostia_path+'" doesnt exist or is corrupted.')
        try:
            data = load_mercator(forecast_path).thetao.squeeze()
            data = data.resample({'leadtime':'d'}).mean()
            data.coords['leadtime'] = np.arange(len(data.leadtime))
            SST_MERCATOR.append(data)
        except Exception as e:
            print('         File "'+forecast_path+'" doesnt exist or is corrupted.')
    SST_OSTIA = xr.concat(SST_OSTIA,dim='time').sortby('time')
    SST_MERCATOR = xr.concat(SST_MERCATOR,dim='time').sortby('time')
    return SST_OSTIA,SST_MERCATOR

def make_sst_leadtime_plot(var, cmap, cbar_label, output_path,
              start_from0=False,
              level_step=0.1,
              date_interval="",
              **kwargs):
    fig,ax,cax = make_maps(MAPS_GRID,figsize=MAPS_FIGSIZE,
                        xticks=[-72.5,-71],
                        yticks=[-27,-28,-29,-30,-31,-32,-33],
                        **kwargs)
    var = fill_borders(var)
    lon,lat = var.lon,var.lat
    lon2d,lat2d = np.meshgrid(lon,lat)
    # lim = max(abs(var.quantile(0.01)),abs(var.quantile(0.99)))
    # lim = np.ceil((lim).round(1))
    lim = 2
    if start_from0==True:
        vmin,vmax = 0,lim
    else:
        vmin,vmax = -lim,lim
    for i,axis in enumerate(ax.ravel()):
        mapa = axis.contourf(lon2d,lat2d,var.sel(leadtime=i).values,
                            levels=np.arange(vmin,vmax+level_step,level_step),
                            norm=mcolors.Normalize(vmin,vmax),
                            cmap=cmap,
                            extend='both',
                            transform=ccrs.PlateCarree(),
                            zorder=0)
        axis.set_title('Dia '+str(i+1), fontsize=16, loc='left')
        axis.set_ylim(-33,-27)
    cbar=fig.colorbar(mapa,cax=cax)
    cbar.set_label(label=cbar_label,
                fontsize=18)
    cbar.ax.tick_params(labelsize=18)
    if len(date_interval)>0:
        ax[-1,0].text(0,-0.2,'Estadistica para el periodo: '+date_interval,
                    fontsize=12, transform=ax[-1,0].transAxes)
    plt.savefig(output_path,
                dpi=150,
                bbox_inches='tight')
    plt.close()
    return None

def sst_validation(N=30, bias_fix = False):
     
    # ----------------------------- global variables ----------------------------- #
    lon1,lon2,lat1,lat2 = [-73,-70.67,-33,-27] #Spatial extent lon1,lon2,lat1,lat2

    # ----------------------- Define times for the analysis ---------------------- #
    time = target_date("data/FORECAST/SST/DATAD/*.nc","data/OSTIA/*.nc")
    target_times = [time-pd.Timedelta(days=n) for n in range(N)]
    date_interval = target_times[-1].strftime("%F"),target_times[0].strftime("%F")
    date_interval = " ; ".join(date_interval)
    print('Loading data...')
    # --------------------------------- Load data -------------------------------- #
    SST_OSTIA,SST_MERCATOR = load_data(target_times,
                                       [lon1-0.1,lon2+0.1,lat1-0.1,lat2+0.1])

    # ---------------------------------------------------------------------------- #
    #                                  PROCESS DATA                                #
    # ---------------------------------------------------------------------------- #
    # ------------------------------ Bias correction ----------------------------- #
    if bias_fix:
        print('Performing bias correction...')
        SST_MERCATOR = bias_correct_SST(SST_MERCATOR, method='linregress')
    # -------------------------------- Match Grids ------------------------------- #
    print('Regriding...')
    husk = xr.Dataset(coords={'lat':np.arange(lat1,lat2+0.05,0.05),
                            'lon':np.arange(lon1,lon2+0.05,0.05)})
    lat,lon = husk.lat.values,husk.lon.values
    lon2d,lat2d = np.meshgrid(lon,lat)
    SST_OSTIA = regrid(SST_OSTIA,husk)
    SST_OSTIA = SST_OSTIA.where(SST_OSTIA!=0)
    SST_MERCATOR = regrid(SST_MERCATOR,husk)
    SST_MERCATOR = SST_MERCATOR.where(SST_MERCATOR!=0)
    # ----------------- Compute bias and model evaluation metrics ---------------- #
    print('Computing validation metrics...')
    METRICS = compute_metrics(SST_MERCATOR,SST_OSTIA)
    # ---------------------------------------------------------------------------- #
    #                                     PLOTS                                    #
    # ---------------------------------------------------------------------------- #
    print('Plotting...')
    # ------------------------------ make MBIAS maps ----------------------------- #
    plt.rc('font',size=12)
    label='Sesgo promedio '+r'($\overline{\Delta})$'+'\n'+\
        '$\Delta = TSM_{pronostico}-TSM_{satelite}$'+'\n'+r'$(\degree C)$'
    out  ='plots/SST_MBIAS_DIAPRONOSTICO_MEJOR_CURRENT.png'
    make_sst_leadtime_plot(var=METRICS.MBIAS,
                    cmap='RdBu_r',
                    cbar_label=label,
                    output_path=out,
                    start_from0=False,
                    date_interval=date_interval,
                    extent=ocean_mapsextent)
    # ------------------------------ make RMSE maps ------------------------------ #
    plt.rc('font',size=12)
    label='Raiz del error cuadratico medio '+r'($\sqrt{\overline{\Delta^2}})$'+\
        '\n'+'$\Delta = TSM_{pronostico}-TSM_{satelite}$'+'\n'+r'$(\degree C)$'
    out  ='plots/SST_RMSE_DIAPRONOSTICO_MEJOR_CURRENT.png'
    make_sst_leadtime_plot(var=METRICS.RMSE,
                    cmap='Purples',
                    cbar_label=label,
                    output_path=out,
                    level_step=0.1,
                    start_from0=True,
                    date_interval=date_interval,
                    extent=ocean_mapsextent)
    print('Done')
    return
if __name__=="__main__":
    sst_validation(N=30, bias_fix=False)
    sys.exit()
   

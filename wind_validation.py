'''
 # @ Author: lucas
 # @ Create Time: 2022-07-25 16:39:35
 # @ Modified by: lucas
 # @ Modified time: 2022-07-25 16:39:41
 # @ Description: validacion ultimos 30 dias pronostico viento CEAZAMAR
 '''

# ---------------------------------------------------------------------------- #
# ---------------------------------- Imports --------------------------------- #
# ---------------------------------------------------------------------------- #
import os
import sys

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs

import xarray as xr
from load import target_date, load_wrf
from numerics import regrid, compute_metrics, fill_borders
from graphical import make_maps
from params import *

#print('Iniciando validacion de viento...')
# ---------------------------------------------------------------------------- #
#                            DEFINE GLOBAL VARIABLES                           #
# ---------------------------------------------------------------------------- #
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
    WINDS_ASCAT = []
    WINDS_WRF = []
    for p in times:
        forecast_path = 'data/FORECAST/WRF/U10V10/wrfCeazaOp_U10V10_d02_'+\
                        p.strftime("%Y-%m-%d")+'.nc'
        ascat_path = os.popen('ls data/ASCAT/'+p.strftime('%Y%m%d')+'00*').read()
        ascat_path = ascat_path.replace("\n","")
        try:
            data = xr.open_dataset(ascat_path, engine='netcdf4').squeeze()
            data = data.rename({'longitude':'lon',
                                'latitude':'lat'})
            data = data.sortby('lat').sortby('lon')
            data = data.sel(lat=slice(lat1,lat2),lon=slice(lon1,lon2))
            data = data[['eastward_wind','northward_wind']]
            WINDS_ASCAT.append(data.rename({'eastward_wind':'U10',
                                            'northward_wind':'V10'}))
        except Exception as e:
            print('         File "'+ascat_path+'" doesnt exist or is corrupted.')
        try:
            data = load_wrf(forecast_path).squeeze()
            data = data.resample({'leadtime':'d'}).mean()
            data.coords['leadtime'] = np.arange(len(data.leadtime))
            data = data.sel(lat=slice(lat1,lat2),lon=slice(lon1,lon2))
            WINDS_WRF.append(data[['U10','V10']])
        except Exception as e:
            print('         File "'+forecast_path+'" doesnt exist or is corrupted.')
    WINDS_ASCAT = xr.concat(WINDS_ASCAT,dim='time').sortby('time')
    WINDS_WRF = xr.concat(WINDS_WRF,dim='time').sortby('time')
    return WINDS_ASCAT,WINDS_WRF

def make_wind_leadtime_plot(var, cmap, cbar_label, output_path,
              start_from0=False,
              level_step=0.25,
              date_interval="",
              **kwargs):
    fig,ax,cax = make_maps(MAPS_GRID,figsize=MAPS_FIGSIZE,
                        xticks=[-72.5,-71],
                        yticks=[-28,-29,-30,-31,-32,-33],
                        loclats=[x[0] for x in MAPS_LOCS.values()],
                        loclons=[x[1] for x in MAPS_LOCS.values()],
                        locnames=MAPS_LOCS.keys(),
                        extent=[-73,-70.5,-33,-28],
                        **kwargs)
    lon,lat = var.lon,var.lat
    lon2d,lat2d = np.meshgrid(lon,lat)
    lim = max(abs(var.quantile(0.05)),abs(var.quantile(0.95)))
    lim = np.ceil((lim).round(1))
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
        axis.set_ylim(-33,-28)
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


def wind_validation(N=30):
     # ----------------------------- global variables ----------------------------- #
    lon1,lon2,lat1,lat2 = [-73,-70.67,-33,-28] #Spatial extent lon1,lon2,lat1,lat2

    # ----------------------- Define times for the analysis ---------------------- #
    time = target_date("data/FORECAST/WRF/U10V10/*.nc","data/ASCAT/*.nc")
    target_times = [time-pd.Timedelta(days=n) for n in range(N)]
    date_interval = target_times[-1].strftime("%F"),target_times[0].strftime("%F")
    date_interval = " ; ".join(date_interval)
    print('Cargando data...')
    # --------------------------------- Load data -------------------------------- #
    WASCAT,WWRF = load_data(target_times, bbox=[lon1,lon2,lat1,lat2])
    WASCAT = WASCAT.reindex({'time':WWRF.time},method='nearest')
    WASCAT['MASK'] = ~np.isnan(WASCAT['U10'][0])
    
    # ---------------------------------------------------------------------------- #
    #                                  PROCESS DATA                                #
    # ---------------------------------------------------------------------------- #
    # -------------------------------- Match Grids ------------------------------- #
    print('Regrillando...')
    husk = xr.Dataset(coords={'lat':np.arange(lat1,lat2+0.1,0.1),
                            'lon':np.arange(lon1,lon2+0.1,0.1)})
    lat,lon = husk.lat.values,husk.lon.values
    lon2d,lat2d = np.meshgrid(lon,lat)
    WASCAT = regrid(WASCAT,husk)
    WASCAT = WASCAT.where(WASCAT!=0)
    WASCAT['MASK'] = ~np.isnan(WASCAT['MASK'])
    WWRF = regrid(WWRF,husk)
    WWRF = WWRF.where(WWRF!=0)
    # ----------------- Compute bias and model evaluation metrics ---------------- #
    WWRF['WS'] = np.sqrt(WWRF.U10**2+WWRF.V10**2)
    WASCAT['WS'] = np.sqrt(WASCAT.U10**2+WASCAT.V10**2)
    print('Calculando metricas de validacion...')
    METRICS = compute_metrics(WWRF['WS'],WASCAT['WS'])
    # ---------------------------------------------------------------------------- #
    #                                     PLOTS                                    #
    # ---------------------------------------------------------------------------- #
    print('Creando graficas...')
    plt.rc('font',size=12)
    # ------------------------------ make MBIAS maps ----------------------------- #
    label='Sesgo promedio '+r'($\overline{\Delta})$'+'\n'+\
        '$\Delta = U_{pronostico}-U_{satelite}$'+'\n'+'(m/s)'
    out  ='plots/VIENTO_MBIAS_DIAPRONOSTICO_CURRENT.png'
    make_wind_leadtime_plot(var=fill_borders(METRICS.MBIAS),
                       cmap='RdBu_r',
                       cbar_label=label,
                       output_path=out,
                       start_from0=False,
                       date_interval=date_interval)
    # ------------------------------ make RMSE maps ------------------------------ #
    label='Raiz del error cuadratico medio '+r'($\sqrt{\overline{\Delta^2}})$'+\
        '\n'+'$\Delta = U_{pronostico}-U_{satelite}$'+'\n(m/s)'
    out  ='plots/VIENTO_RMSE_DIAPRONOSTICO_CURRENT.png'
    make_wind_leadtime_plot(var=fill_borders(METRICS.RMSE),
                       cmap='Purples',
                       cbar_label=label,
                       output_path=out,
                       level_step=0.25,
                       start_from0=True,
                       date_interval=date_interval)
    print('Fin')
if __name__=="__main__":
   wind_validation(N=30)
   sys.exit()

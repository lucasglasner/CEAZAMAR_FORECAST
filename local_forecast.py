'''
 # @ Author: lucas
 # @ Create Time: 2022-07-25 21:32:48
 # @ Modified by: lucas
 # @ Modified time: 2022-07-25 21:33:04
 # @ Description: Script para generar pronosticos para una coordenada.
 Uso: python3 pronostico_local.py nombre,lon,lat,outputpath
'''

# ---------------------------------------------------------------------------- #
#                                    IMPORTS                                   #
# ---------------------------------------------------------------------------- #
import os
import sys
import locale
locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns


from load import forecast_path, load_forecast_ini
from check_forecast_status import checkcreated_data
from graphical import create_timegrid, plot_logo
from graphical import plot_row_arrows, plot_row_textcolor
from create_localforecast import create_localforecast
from params import *

# ---------------------------------------------------------------------------- #
#                                GLOBAL VARIABLES                              #
# ---------------------------------------------------------------------------- #
def local_forecast(idate,name,lon,lat,outdir='plots/PRONOSTICO_SITIOS/'):
    logo=plt.imread('static/Logo_Ceaza_color.png')
    if os.path.isfile('tmp/'+name.replace("_","")+'_FORECAST_CURRENT.csv'):
        data = pd.read_csv('tmp/'+name.replace("_","")+'_FORECAST_CURRENT.csv',
                           index_col=0)
        data.index = pd.to_datetime(data.index)  
    else:
        locations=pd.DataFrame([lon,lat],columns=[name],index=['lon','lat'])
        data = create_localforecast(idate,locations.T, save=False)[0]
        data.index = pd.to_datetime(data.index)
        
    inits = []
    for ftype in ['atm','ocean','wave']:
        path = forecast_path(idate,ftype)
        inits.append(load_forecast_ini(path,ftype))  
# ---------------------------------------------------------------------------- #
#                                         PLOT                                 #
# ---------------------------------------------------------------------------- #
    plt.rc('font',size=12)
    fig,ax,grid = create_timegrid(data.index,9, figsize=(130,5))
    plot_row_textcolor({'data':data[windspeed_name],
                        'row':0,
                        'fmt':'{:.1f}',
                        'fontsize':12,
                        'color_kwargs':{'cmap':'viridis',
                                        'norm':mcolors.Normalize(-5,11)}
                        },
                        grid=grid, ax=ax)
    plot_row_textcolor({'data':data['BEAUFORT'],
                        'row':1,
                        'fmt':'{:.0f}',
                        'fontsize':12,
                        'color_kwargs':{'cmap':'PuRd',
                                        'norm':mcolors.Normalize(3,12)}},
                         grid=grid,ax=ax)
    plot_row_arrows({'data':data['WDIR'],
                     'row':2},
                    grid=grid,ax=ax)
    plot_row_textcolor({'data':data['WDIR_STR'],
                        'row':3,
                        'fontsize':14
                        },
                        colors=False,grid=grid, ax=ax)
    cmap = mcolors.ListedColormap(plt.cm.nipy_spectral(np.linspace(0.1,0.95,
                                                                   1000)))
    plot_row_textcolor({'data':data[waveheight_name],
                        'row':4,
                        'fmt':'{:.1f}',
                        'fontsize':12,
                        'color_kwargs':{'cmap':cmap,
                                        'norm':mcolors.Normalize(0,4.5)}
                       },
                        grid=grid, ax=ax)
    plot_row_textcolor({'data':data[waveperiod_name],
                        'row':5,
                        'fmt':'{:.0f}',
                        'fontsize':12,
                        'color_kwargs':{'cmap':'YlGnBu',
                                        'norm':mcolors.Normalize(4,24)}
                       },
                        grid=grid, ax=ax)
    plot_row_arrows({'data':data[wavedir_name],
                     'row':6},
                    grid=grid,ax=ax)
    plot_row_textcolor({'data':data['VMDR_STR'],
                        'row':7,
                        'fontsize':14
                        },
                        colors=False,grid=grid, ax=ax)
    sst_daily = data[sst_name].resample('d').mean().reindex(data.index).interpolate()
    plot_row_textcolor({'data':sst_daily,
                        'row':8,
                        'color_kwargs':{'cmap':'RdBu_r',
                                        'norm':mcolors.Normalize(sst_daily.min()*0.925,
                                                                 sst_daily.max()*1.075)}
                        },
                       text=False,grid=grid,ax=ax)
    plot_row_textcolor({'data':data[sst_name],
                        'row':8,
                        'fmt':'{:0.1f}',
                        'fontsize':12
                        },
                       colors=False,grid=grid,ax=ax)
    
    
    # ------------------------------- common stuff --------------------------- #
    ax.set_yticklabels(['Velocidad del\nviento (m/s)',
                        'Escala de Beaufort',
                        '\n\nDirección\ndel viento',
                        '',
                        'Altura\nde ola (m)',
                        'Periodo (s)',
                        '',
                        'Dirección\nde oleaje\n\n',
                        'Temperatura superficial\ndel mar (°C)'][::-1]);
    ax.tick_params(axis='y', length=0, pad=15)
    ax.text(0,1.25,'PRONÓSTICO '+name.replace("_"," "),
            fontsize=18,
            transform=ax.transAxes)
    for d in np.unique(data.index.date)[1:]:
        d = pd.to_datetime(d)-pd.Timedelta(minutes=30)
        ax.axvline(d, color='k', lw=2)
    ax.text(0,-0.15,
            'Inicio pronóstico de viento: WRF-Ceaza '+inits[0]+'\n'+
            'Inicio pronóstico de olas: MFWAM-MeteoFrance '+inits[1]+'\n'+
            'Inicio pronóstico de TSM: NEMO-MeteoFrance '+inits[2],
            fontsize=10, transform=ax.transAxes)
    plot_logo(logo, (-0.0075,0.925), fig, 0.25)

    plt.savefig(outdir+name.replace("_","")+'_FORECAST_CURRENT.png',
                dpi=100, bbox_inches='tight')
    plt.close()
    return 

# ---------------------------------------------------------------------------- #
if __name__=='__main__':
    name,lon,lat,outdir = 'blabla',-72,-33,'./'
    #name,lon,lat,outdir = sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),sys.argv[4]
    print('Making forecast for: '+name)
    local_forecast(FORECAST_DATE,name,lon,lat,outdir)
    sys.exit()

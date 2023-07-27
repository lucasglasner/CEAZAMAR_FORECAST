'''
 # @ Author: lucas
 # @ Create Time: 2022-07-22 15:01:14
 # @ Modified by: lucas
 # @ Modified time: 2022-07-22 15:21:47
 # @ Description:
 '''

# ---------------------------------------------------------------------------- #
# ---------------------------------- Imports --------------------------------- #
# ---------------------------------------------------------------------------- #

import os
import datetime
from glob import iglob,glob
import xarray as xr
import numpy as np
import pandas as pd

from numerics import regrid
from params import *

# ---------------------------------------------------------------------------- #
# ---------------------------- Load data functions --------------------------- #
# ---------------------------------------------------------------------------- #




# ------------------------------ FORECAST TOOLS ------------------------------ #
def last_forecast_path(which):
    """
    Return last aviable forecast of each type

    Args:
        which (str): kind of forecast (atm, ocean ,wave)

    Returns:
        str: path to netcdf file
    """
    if which not in ['atm','ocean','wave']:
        raise ValueError('Which parameter must indicate only some\
                          of these ["ocean","wave", "atm"]')  
    path = os.popen("ls "+eval(which+'_forecast_dir')+"/*.nc | sort | tail -n 1").read()
    path = path.replace('\n','')

    return path

def first_forecast_date(which):
    """
    Return the first aviable forecast of each type

    Args:
        which (str): kind of forecast (atm, ocean ,wave)

    Returns:
        str: path to netcdf file
    """
    if which not in ['atm','ocean','wave']:
        raise ValueError('Which parameter must indicate only some\
                          of these ["ocean","wave", "atm"]')  
    path = os.popen("ls "+eval(which+'_forecast_dir')+"/*.nc | sort | head -n 1").read()
    path = path.replace('\n','')
    data = load_forecast_data(path,which)
    time = pd.to_datetime(data.time.item())
    return time

def target_date(forecast_directory, validationdata_directory):
    """
    Find out which is the last aviable date between
    forecast and validation data
    Returns:
        pandas Timestamp: last aviable data
    """
    last_forecast = iglob(forecast_directory)
    last_forecast = max(list(map(os.path.getctime,last_forecast)))
    last_forecast = datetime.datetime.fromtimestamp(last_forecast)

    last_validation = iglob(validationdata_directory)
    last_validation = max(list(map(os.path.getctime,last_validation)))
    last_validation = datetime.datetime.fromtimestamp(last_validation)

    return min(last_forecast,last_validation).date()


def forecast_path(date, which):
    """
    Return forecast path for a type and date. If asked for today
    or for the future returns last aviable forecast.
    If forecast exists but is corrupted, return last valid forecast.

    Args:
        which (str): kind of forecast (atm, ocean ,wave)
        date  (str): %Y-%m-%d

    Returns:
        str: path to netcdf file
    """
    #Some checks
    if pd.to_datetime(date) < first_forecast_date(which):
        fforecast = first_forecast_date(which).strftime('%F')
        raise ValueError('Forecast are only aviable for dates after '+fforecast)
    if which not in ['atm','ocean','wave']:
        raise ValueError('Which parameter must indicate only some\
                          of these ["ocean","wave", "atm"]') 
    if pd.to_datetime(date).date() == datetime.datetime.now().date():
        path = last_forecast_path(which)
    else:  
        path = os.popen("ls "+eval(which+'_forecast_dir')+"/*.nc | grep "+date).read()
        path = path.replace('\n','')
        if path.replace(which+'_forecast_dir','') == '':
            print('          '+which.upper()+' forecast for '+date+
                  ' doesnt exist, trying with yesterday...')
            ndate = pd.to_datetime(date)-pd.Timedelta(days=1)
            ndate = ndate.strftime("%F")
            return forecast_path(ndate,which)
        path = path.replace('\n','') 
    return path
        

def load_wrf(path, **kwargs):
    """ 
    load a wrf model output and adjust for the package to work
    other arguments are passed to xarray.open_dataset() function
    Args:
        path (str): path to netcdf file

    Returns:
        XDataSet: xarray loaded dataset
    """
    data = xr.open_dataset(path, engine='netcdf4', **kwargs)
    p = data.attrs['SIMULATION_START_DATE']
    data = data.sortby('XTIME')
    data = data.rename({'south_north':'y',
                        'west_east':'x',
                        'XTIME':'leadtime',
                        'XLONG':'lon',
                        'XLAT':'lat'})
    data.coords['time'] = pd.to_datetime(p, format="%Y-%m-%d_%H:%M:%S")
    
    # Regrid to rectangular grid
    lonmin,lonmax = data.lon.min().item(), data.lon.max().item()
    latmin,latmax = data.lat.min().item(), data.lat.max().item()
    dlon,dlat = data.lon.diff('x').min(),data.lat.diff('y').min()
    dlon,dlat = abs(dlon.item()),abs(dlat.item())
    hres      = min(dlon,dlat)
    husk = xr.Dataset(coords={'lat':(['y'], np.arange(latmin,latmax+hres,hres)),
                                'lon':(['x'], np.arange(lonmin,lonmax+hres,hres))})
    data = regrid(data,husk).rename({'x':'lon','y':'lat'})
    return data

def load_mercator(path, **kwargs):
    """ 
    load a mercator model output and adjust for the package to work
    other arguments are passed to xarray.open_dataset() function
    Args:
        path (str): path to netcdf file

    Returns:
        XDataSet: xarray loaded dataset
    """
    data = xr.open_dataset(path, engine='netcdf4', **kwargs)
    data = data.squeeze()
    data = data.rename({'latitude':'lat',
                    'longitude':'lon',
                    'time':'leadtime'})
    p = path.split("/")[-1].split(".")[0]
    data.coords['time'] = pd.to_datetime(p,format="%Y-%m-%d")

    return data
    
def load_forecast_data(path, which,**kwargs):
    """
    Load netcdf forecast data

    Args:
        path (str): path to netcdf file
        which (str): kind of forecast (ocean, atm, wave) 

    Raises:
        ValueError: If wrong kind of forecast is selected

    Returns:
        XDataSet: xarray with the loaded forecast data
    """
    if which=='ocean':
        return load_mercator(path, **kwargs)
    elif which=='wave':
        return load_mercator(path, **kwargs)
    elif which=='atm':
        return load_wrf(path, **kwargs)
    else:
        raise ValueError('Which parameter must indicate only some\
            of these ["ocean","wave", "atm"]')
    
def init_wrf(path):
    """
    Requieres netcdf library installed on path.
    From the metadata grabs the wrf initialization date.
    
    Args:
        path (str): path to a wrf output netcdf

    Returns:
        str: forecast initialization date
    """
    command = "ncdump -i -v XTIME "+path+" | grep XTIME"
    init = os.popen(command+" | tail -n 1 | awk '{ print $3 }'").read()
    init = init.replace(",","").replace("\"","")
    init = pd.to_datetime(init).strftime('%F %HUTC')
    return init
    
def init_mercator(path, which):
    """
    Requieres netcdf library installed on path.
    From the metadata grabs the wrf initialization date.
    
    Args:
        path (str): path to a mercator output netcdf

    Returns:
        str: forecast initialization date
    """
    if which=='ocean':
        command = "ncdump -i -v time "+path+" | grep time"
        init = os.popen(command+" | tail -n 1 | awk '{ print $3 }'").read()
        init = init.replace(",","").replace("\"","")
        init = pd.to_datetime(init).strftime('%F %HUTC')
    elif which=='wave':
        command = "ncdump -i -v time "+path+" | grep time"
        init = os.popen(command+" | tail -n 1 | awk '{ print $3 }'").read()
        init = init.replace(",","").replace("\"","")
        init = pd.to_datetime(init).strftime('%F %HUTC')
    else:
        raise ValueError('Which parameter must indicate only some\
            of these ["ocean","wave"]')   
    return init

def load_forecast_ini(path, which):
    """
    Load netcdf forecast data

    Args:
        path (str): path to netcdf file
        which (str): kind of forecast (ocean, atm, wave) 

    Raises:
        ValueError: If wrong kind of forecast is selected

    Returns:
        str: initialization date of the forecast type requested
    """
    if which=='ocean':
        return init_mercator(path,'ocean')
    elif which=='wave':
        return init_mercator(path, 'wave')
    elif which=='atm':
        return init_wrf(path)
    else:
        raise ValueError('Which parameter must indicate only some\
            of these ["ocean","wave", "atm"]')


# ------------------- Diagnostic and validation data tools ------------------- #


def load_altimeters(idate, centerhour=datetime.datetime.now(), hwidth=4):
    """
    Function for loading as a table the wave/wind altimeter data from 
    copernicus database.

    Args:
        idate (str): Target date to recover data
        centerhour (datetime, optional): _description_. Defaults to datetime.datetime.now().
        hwidth (int, optional): _description_. Defaults to 4.

    Returns:
        _type_: _description_
    """
    centerhour = datetime.datetime.now()
    print('Loading altimeter data...')
    pddate           = pd.to_datetime(idate)
    altimeters_paths = sorted(glob(wave_altimeter_dir+'/*'))
    altimeters_data  = []
    names            = []
    for a in altimeters_paths:
        try:
            p = a+'/'+str(pddate.year)+'/'+ str('%02d' % pddate.month)+'/*'+idate.replace("-","")+'*'
            data = xr.open_mfdataset(p).load().drop_duplicates('time').sortby('time').to_dataframe()
            data['longitude'] = (data['longitude']+180)%360-180
            times = slice(pddate-pd.Timedelta(hours=hwidth)+pd.Timedelta(hours=centerhour.hour),
                          pddate+pd.Timedelta(hours=hwidth)+pd.Timedelta(hours=centerhour.hour))
            data = data.loc[times]
            # data = data.loc[idate]
            altimeters_data.append(data)
            print('          '+a.split("/")[-1],': Done')
            names.append(a.split("/")[-1].split("_")[-2].split("-")[0])
            del data
        except Exception as e:
            print('          '+a.split("/")[-1],':', e)

    altimeters_data = pd.concat(altimeters_data, keys=names)
    altimeters_data = altimeters_data[['latitude','longitude','VAVH','WIND_SPEED']]
    altimeters_data.columns = ['lat','lon',waveheight_name, windspeed_name]
    return altimeters_data.drop_duplicates()
         

def load_ascat(idate, **kwargs):
    """
    Function for loading ASCAT L4 data as xarray

    Args:
        idate (_type_): _description_

    Returns:
        _type_: _description_
    """
    p = pd.to_datetime(idate)
    ascat_path = glob('data/ASCAT/'+p.strftime('%Y%m%d')+'00*')


    if ascat_path!=[]:
        ascat_path = ascat_path[0]
        data = xr.open_dataset(ascat_path, **kwargs).squeeze()
        data = data.rename({'longitude':'lon',
                            'latitude':'lat'})
        data = data.sortby('lat').sortby('lon')
        data = data[['eastward_wind','northward_wind']]
        data = data.rename({'eastward_wind':uwnd_name,'northward_wind':vwnd_name})
        data[windspeed_name] = np.hypot(data[uwnd_name],data[vwnd_name])
        return data
    else:
        print('         ASCAT data for '+idate+' doesnt exists!')
        return
    

def load_ccmp(idate, **kwargs):
    """
    Function for loading CCMP Wind data as xarray

    Args:
        idate (_type_): _description_

    Returns:
        _type_: _description_
    """
    ccmp_path = 'data/CCMPWINDS/'
    file_name = 'CCMP_RT_Wind_Analysis_'+idate.replace('-','')+'_V02.1_L3.0_RSS.nc'
    ccmp_path = ccmp_path+file_name
    print('          '+ccmp_path)
    data = xr.open_dataset(ccmp_path, **kwargs).squeeze()
    data = data.rename({'latitude':'lat', 'longitude':'lon',
                        'uwnd':uwnd_name,'vwnd':vwnd_name})
    data['lon'] = (data['lon']+180)%360-180
    data = data.sortby('lon').sortby('lat')
    data[windspeed_name] = np.hypot(data[uwnd_name], data[vwnd_name])
    data = data.sel(lat=slice(diagnostics_mapsextent[2]-1,diagnostics_mapsextent[3]+1),
                    lon=slice(diagnostics_mapsextent[0]-1,diagnostics_mapsextent[1]+1))
    return data

def load_ostia(idate, **kwargs):
    """
    Function for loading OSTIA SST L4 satellite data as xarray

    Args:
        idate (_type_): _description_

    Returns:
        _type_: _description_
    """
    p = pd.to_datetime(idate)
    ostia_path = 'data/OSTIA/'+p.strftime('%Y%m%d')+\
        '-UKMO-L4HRfnd-GLOB-v01-fv02-OSTIA.nc'
    if os.path.isfile(ostia_path):
        data = xr.open_dataset(ostia_path, **kwargs).analysed_sst-273.15
        data = data.resample({'time':'d'}).mean().squeeze()
        data = data.sel(lat=slice(diagnostics_mapsextent[2]-1,diagnostics_mapsextent[3]+1),
                    lon=slice(diagnostics_mapsextent[0]-1,diagnostics_mapsextent[1]+1))
        return data
    else:
        print('         OSTIA data for '+idate.strftime('%F')+' doesnt exists!')
        return

def load_tpxo(idate, path=ocean_tidemodel_file, n_constituents=10, **kwargs):
    """
    This functions load the TPXO ocean tides dataset and computes the 
    amplitude and phase of each tidal constituent.

    Args: 
        idate (str): forecast date
        path (str): ocean tide model file (netcdf)
        n_constituents (int): number of tidal constituents (1..10)
        **kwargs are passed to xarray.open_dataset()
    Returns:
        _type_: _description_
    """
#   print('Loading tide model data: '+ocean_tidemodel_file)
    if os.path.isfile(ocean_tidemodel_file):
        tides = xr.open_dataset(path, **kwargs)
        tides = tides.isel(periods=slice(0,n_constituents))
    else:
        # print('Tide model: '+ocean_tidemodel_file+'doesnt exists!')
        return
    # print('Tidal constituents: '+tides.components)
    try:
        tides = tides.rename({'lat_r':'lat','lon_r':'lon'})
        tides.coords['lon'] = (tides.coords['lon'] + 180) % 360 - 180
    except Exception as e:
        print(e)
        pass
    name=np.array(tides.components.split(' ')).squeeze()[:n_constituents]
    tides = tides.assign_coords({'name':('periods',name)})
    tides = tides.swap_dims({'periods':'name'})
    # print('Computing amplitude and phase for each constituent...')
    tides['tssh_complex']   = tides.ssh_r+tides.ssh_i*np.sqrt(-1, dtype=complex)
    tides['tssh_amplitude'] = np.abs(tides['tssh_complex'])

    tides['tssh_phase']     = np.mod(np.rad2deg(xr.apply_ufunc(np.angle,tides['tssh_complex'])),360)
    tides['t_time']         = pd.to_datetime(idate)
    
    # if nodal_correct:
    #     # print('Performing nodal corrections for '+idate+'...')
    #     pf,pu,t0,phase_mkB  = egbert_correct(modified_julian_day(pd.to_datetime(idate).date()),
    #                                          0,0,0)
    #     pf = pf.loc[name]
    #     pu = pu.loc[name]
        
    #     tides['tssh_amplitude'] = tides['tssh_amplitude']*pf.to_xarray().rename({'index':'name'})
    #     tides['tssh_phase']     = np.mod(-tides['tssh_phase']-pu.to_xarray().rename({'index':'name'}),360)
        
    # print('Done')
    return tides
    
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
import pandas as pd

from params import *
# ---------------------------------------------------------------------------- #
# ---------------------------- Load data functions --------------------------- #
# ---------------------------------------------------------------------------- #

def target_date(forecast_directory,validationdata_directory):
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

def forecast_path(date,which):
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
    data = data.assign_coords({'west_east':data.XLONG.values[0,:],
                               'south_north':data.XLAT.values[:,0]})
    data = data.rename({'south_north':'lat',
                        'west_east':'lon',
                        'XTIME':'leadtime'})
    data.coords['time'] = pd.to_datetime(p,
                                         format="%Y-%m-%d_%H:%M:%S")
    data = data.sortby('lat').sortby('lon')
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
    command = "grep -oP '(?<=START_DATE).*(?=;)'"
    init = os.popen("ncdump -h "+path+" | "+command).read()
    init = init.replace('_','T')
    init = init.split("\n")
    init = init[0][4:-2]+","+init[1][4:-2]
    init = [pd.to_datetime(t) for t in init.split(",")]
    init = min(init).strftime('%F %HUTC')
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
        command = "grep -oP '(?<=\").*(?=T00:30)'"
        init = os.popen("ncdump -ci "+path+" | grep time | tail -n 1 | "+
                        command).read()
        init = (pd.to_datetime(init)).strftime('%F %HUTC')
    elif which=='wave':
        command = "grep -oP '(?<=,\ \").*(?=T03)'"
        init = os.popen("ncdump -ci "+path+" | grep time | tail -n 1 | "+
                        command).read()
        init = (pd.to_datetime(init)).strftime('%F %HUTC')
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

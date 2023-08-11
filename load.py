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

from params import *
from numerics import *


# ------------------------------ PATH FUNCTIONS ------------------------------ #
def raise_incorrect_type(which):
    """
    Raise value error if incorrect forecast type

    Args:
        which (str): kind of forecast (atm, ocean ,wave)
    """
    if which not in ['atm','ocean','wave']:
        raise ValueError('Which parameter must indicate only some\
                          of these ["ocean","wave", "atm"]') 
    return

def first_forecast_path(which):
    """
    Return the first aviable forecast of each type

    Args:
        which (str): kind of forecast (atm, ocean ,wave)

    Returns:
        str: path to netcdf file
    """
    path = glob(eval(f'{which}_globalparams')['forecast_dir']+'/*.nc')
    path = sorted(path)[0]
    return path

def first_forecast_date(which):
    """
    Return the date of the first aviable forecast of each type

    Args:
        which (str): kind of forecast (atm, ocean ,wave)

    Returns:
        str: first forecast date
    """
    path = first_forecast_path(which)
    fdir     = eval(f'{which}_globalparams')['forecast_dir']
    fsuffix  = eval(f'{which}_globalparams')['forecast_suffix']
    date = path.replace(fdir,'')
    date = date.replace(fsuffix,'')
    date = date.replace('/','')
    date = date.replace('.nc','')
    date = pd.to_datetime(date).strftime('%F')
    return date
    

def last_forecast_path(which):
    """
    Return last aviable forecast of each type
    Args:
        which (str): kind of forecast (atm, ocean ,wave)

    Returns:
        str: path to netcdf file
    """
    path = glob(eval(f'{which}_globalparams')['forecast_dir']+'/*.nc')
    path = sorted(path)[-1]

    return path


def forecast_path(date, which):
    """
    Return forecast path for a type and specific date.
    
    Args:
        which (str): type of forecast (atm, ocean ,wave)
        date  (str): %Y-%m-%d

    Returns:
        str: path to netcdf file
    """
    # Some checks
    raise_incorrect_type(which)
    
    date      = pd.to_datetime(date)
    firstdate = pd.to_datetime(first_forecast_date(which)) 
    # If date goes before any aviable forecast raise error
    if date<firstdate:
        raise RuntimeError(f'Forecast are only aviable for dates after {firstdate}')
    # If date is from today or the future return last valid forecast
    if pd.to_datetime(date).date() >= datetime.datetime.now().date():
        path = last_forecast_path(which)
    else:
        fdir     = eval(f'{which}_globalparams')['forecast_dir']
        fsuffix  = eval(f'{which}_globalparams')['forecast_suffix']
        fdformat = eval(f'{which}_globalparams')['forecast_dateformat']
        path     = '{}/{}'.format(fdir,fsuffix)
        path     = path+'{}.nc'.format(date.strftime(fdformat))
    
    # Check if constructed path exist else raise error
    if os.path.isfile(path):
        # All good
        pass
    else:
        raise RuntimeError(f'{path} doesnt exists!')
    
    return path

# ------------------------------ LOAD FUNCTIONS ------------------------------ #

def load_wrf(path, **kwargs):
    """ 
    Load a wrf model output and adjust coordinates
    for the package to work.
    Args:
        path (str): path to netcdf file
        **kwargs passed to xarray.open_dataset

    Returns:
        data (xDataset): loaded xarray
    """
    data  = xr.open_dataset(path, **kwargs)
    cdict = {value:key for key, value in atm_variables.items()}
    data  = data.rename(cdict)[atm_variables.keys()]
    
    inittime = data.attrs['SIMULATION_START_DATE'].replace('_',' ')
    data.coords['inittime'] = pd.to_datetime(inittime) 
    return data

def load_mercator_ocean(path, **kwargs):
    """ 
    load a mercator model output and adjust
    for the package to work.
    Args:
        path (str): path to netcdf file
        **kwargs passed to xarray.open_dataset

    Returns:
        data (xDataset): loaded xarray
    """
    data = xr.open_dataset(path, engine='netcdf4', **kwargs)
    data = data.squeeze()
    cdict = {value:key for key, value in ocean_variables.items()}
    data  = data.rename(cdict)[ocean_variables.keys()]
    p = path.split("/")[-1].split(".")[0]
    data.coords['inittime'] = pd.to_datetime(p,format="%Y-%m-%d")
    return data

def load_mercator_waves(path, **kwargs):
    """ 
    load a mercator model output and adjust
    for the package to work.
    Args:
        path (str): path to netcdf file
        **kwargs passed to xarray.open_dataset

    Returns:
        data (xDataset): loaded xarray
    """
    data = xr.open_dataset(path, engine='netcdf4', **kwargs)
    data = data.squeeze()
    cdict = {value:key for key, value in wave_variables.items()}
    data  = data.rename(cdict)[wave_variables.keys()]
    p = path.split("/")[-1].split(".")[0]
    data.coords['inittime'] = pd.to_datetime(p,format="%Y-%m-%d")
    return data


def load_tpxo(date, path=ocean_tidemodel, n_constituents=10, **kwargs):
    """
    This functions load the TPXO ocean tides dataset and computes the 
    amplitude and phase of each tidal constituent taking account the
    nodal corrections for the desired datetime.

    Args: 
        date (str): forecast date
        path (str): ocean tide model file (netcdf)
        n_constituents (int): number of tidal constituents (1..10)
        **kwargs are passed to xarray.open_dataset()
    Returns:
        _type_: _description_
    """
    tides = xr.open_dataset(path, **kwargs)
    tides = tides.isel(periods=slice(0,n_constituents))

    tides = tides.rename({'lat_r':'lat','lon_r':'lon'})
    tides.coords['lon'] = (tides.coords['lon'] + 180) % 360 - 180

    constituents=np.array(tides.components.split(' ')).squeeze()[:n_constituents]
    tides = tides.assign_coords({'constituents':('periods',constituents)})
    tides = tides.swap_dims({'periods':'constituents'})
    
    # Computing amplitude and phase for each constituent...
    tides['tssh_complex']   = tides.ssh_r+tides.ssh_i*np.sqrt(-1, dtype=complex)
    tides['tssh_amplitude'] = np.abs(tides['tssh_complex'])
    tides['tssh_phase']     = np.mod(np.rad2deg(xr.apply_ufunc(np.angle,tides['tssh_complex'])),360)
    tides['t_time']         = pd.to_datetime(date)

    # Perform nodal corrections    
    pf,pu,t0,phase_mkB  = egbert_correct(modified_julian_day(
                                         pd.to_datetime(date).date()),
                                         0,0,0)
    pf = pf.loc[tides.constituents.values]
    pu = pu.loc[tides.constituents.values]
    

    tides['tssh_amplitude'] = tides['tssh_amplitude']*pf.to_xarray().rename(
        {'index':'constituents'})
    tides['tssh_phase']     = np.mod(-tides['tssh_phase']-pu.to_xarray().rename(
        {'index':'constituents'}),360)
    
    return tides

def load_forecast_data(date, which,**kwargs):
    """
    Load netcdf forecast data

    Args:
        date  (str): %Y-%m-%d
        which (str): kind of forecast (ocean, atm, wave) 

    Raises:
        RunTimeError: If wrong kind of forecast is selected

    Returns:
        XDataSet: xarray with the loaded forecast data
    """
    path = forecast_path(date, which)
    if which=='ocean':
        return load_mercator_ocean(path, **kwargs)
    elif which=='wave':
        return load_mercator_waves(path, **kwargs)
    elif which=='atm':
        return load_wrf(path, **kwargs)
    else:
        raise_incorrect_type(which)
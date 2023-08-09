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

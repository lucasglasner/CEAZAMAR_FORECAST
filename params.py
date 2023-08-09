'''
 # @ Author: lucas
 # @ Create Time: 2022-08-03 16:40:24
 # @ Modified by: lucas
 # @ Modified time: 2022-08-03 16:40:38
 # @ Description: Main parameters definitions
 '''

import datetime
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt


# ------------------------------- GENERAL STUFF ------------------------------ #
FORECAST_DATE        = datetime.datetime.now().strftime('%F')
EXECUTION_DIRECTORY  = '/home/lucas/CEAZAMAR_FORECAST'
NDAYS_REGIONAL = 10
NHOURS_LOCAL   = 24*9-12
N_JOBS = 10

# -------------------- LEADTIME MAPS GENERAL CONFIGURATION ------------------- #
landpolygon_path       = 'data/regiones.gpkg'
atm_mapsextent         = [-75,-70.8,-34,-28]
ocean_mapsextent       = [-75,-70.8,-34,-28]
wave_mapsextent        = [-75,-70.8,-34,-28]

# ----------------------------- ATMOSPHERIC MODEL ---------------------------- #
atm_globalparams = {
    'forecast_model':'WRF-Ceaza',
    'forecast_dir':'/home/lucas/storage/FORECAST/WRF/WRFMARd02',
    'forecast_suffix':'wrfCeazaOp_d02_',
    'forecast_dateformat':'%FT00Z',
    'horizontal_resolution':'4km',
    }

atm_variables = {
    'uwnd':'U10',
    'vwnd':'V10',
    'lsm':'LANDMASK',
    'precip':'RAIN',
    'rh2':'RH2',
    't2m':'T2',
    'lowclouds':'LOWCLOUDS',
    'midclouds':'MIDCLOUDS',
    'highclouds':'HIGHCLOUDS',    
}

# -------------------------------- OCEAN MODEL ------------------------------- #
ocean_globalparams = {
    'forecast_model':'MERCATOR-NEMO',
    'forecast_dir':'/home/lucas/storage/FORECAST/MERCATOR/PHYSICS',
    'forecast_suffix':'',
    'forecast_dateformat':'%F',
    'horizontal_resolution':'9km',
}


# -------------------------------- WAVE MODEL -------------------------------- #
wave_globalparams = {
    'forecast_model':'MERCATOR-MFWAM',
    'forecast_dir':'/home/lucas/storage/FORECAST/MERCATOR/WAVES',
    'forecast_suffix':'',
    'forecast_dateformat':'%F',
    'horizontal_resolution':'9km',
}





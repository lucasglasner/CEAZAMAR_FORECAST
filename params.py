'''
 # @ Author: lucas
 # @ Create Time: 2022-08-03 16:40:24
 # @ Modified by: lucas
 # @ Modified time: 2022-08-03 16:40:38
 # @ Description: Main parameters definitions
 '''
import datetime

# ---------------------------------------------------------------------------- #
#                                 GENERAL STUFF                                #
# ---------------------------------------------------------------------------- #
FORECAST_DATE        = datetime.datetime.now().strftime('%F')
EXECUTION_DIRECTORY  = '/home/lucas/CEAZAMAR_FORECAST'
NDAYS_REGIONAL = 10
NHOURS_LOCAL   = 216
N_JOBS = 10

#LEADTIME MAPS GENERAL CONFIGURATION
atm_mapsextent   = [-74,-70.5,-34,-28]
ocean_mapsextent = [-73,-70.5,-33,-27]
wave_mapsextent  = [-74,-70.5,-34,-27]

MAPS_GRID    = (2,5)
MAPS_FIGSIZE = (14,8)
MAPS_LOCS    = {'Los Vilos':(-31.904,-71.499),
                'Huentelauquen':(-31.621,-71.568),
                'Tongoy':(-30.255,-71.486),
                'La Serena':(-29.878,-71.273),
                'Chañaral de\nAceituno':(-29.064,-71.514)}

# ---------------------------------------------------------------------------- #
#                                  ATMOSPHERE                                  #
# ---------------------------------------------------------------------------- #
atm_model_name = 'WRF-Ceaza'
# ----------------------------------- paths ---------------------------------- #
atm_forecast_dir   = 'data/FORECAST/WRF/U10V10'           
atm_validation_dir = 'data/ASCAT'                       
# --------------------------- atmospheric variables -------------------------- #
uwnd_name   = 'U10'
vwnd_name   = 'V10'
lsm_name    = 'LANDMASK'

# ---------------------------------------------------------------------------- #
#                                     WAVES                                    #
# ---------------------------------------------------------------------------- #
wave_model_name = 'MFWAM-Meteofrance'
# ----------------------------------- paths ---------------------------------- #
wave_forecast_dir = 'data/FORECAST/MERCATOR/WAVES'
# ------------------------------ wave variables ------------------------------ #
waveheight_name  = 'VHM0'
wavedir_name     = 'VMDR'
waveperiod_name  = 'VTPK'

# ---------------------------------------------------------------------------- #
#                                     OCEAN                                    #
# ---------------------------------------------------------------------------- #
ocean_model_name = 'NEMO-Meteofrance'
# ----------------------------------- paths ---------------------------------- #
ocean_forecast_dir    = 'data/FORECAST/MERCATOR/PHYSICS'
ocean_climatology_dir = 'data/CLIMATOLOGIES.nc'
ocean_validation_dir  = 'data/OSTIA'
# ------------------------------ variable names ------------------------------ #
sst_name = 'thetao'
uo_name  = 'uo'
vo_name  = 'vo'
ssh_name = 'zos'








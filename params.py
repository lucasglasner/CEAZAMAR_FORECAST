'''
 # @ Author: Your name
 # @ Create Time: 2022-08-16 15:44:30
 # @ Modified by: Your name
 # @ Modified time: 2022-09-13 11:33:50
 # @ Description:
 '''

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
NHOURS_LOCAL   = 24*9
N_JOBS = 10

#LEADTIME MAPS GENERAL CONFIGURATION
COASTLINE_MASK_PATH    = '~/storage/VECTORIAL/ChileCOASTMASK.shp'
atm_mapsextent   = [-74,-70.5,-34,-28]
ocean_mapsextent = [-73,-70.5,-33,-27]
wave_mapsextent  = [-74,-70.5,-34,-27]
diagnostics_mapsextent = [-78,-70.5,-34,-26]

MAPS_GRID    = (2,5)
MAPS_FIGSIZE = (14,8)

MAPS_LOCS    = {'Valparaíso':(-33.046,-71.613),
                'Los Vilos':(-31.904,-71.499),
                'Huentelauquen':(-31.621,-71.568),
                'Talcaruca':(-30.476,-71.697),
                'La Serena':(-29.878,-71.286),
                'Chañaral de\nAceituno':(-29.064,-71.514),
                }
                #'Huasco':(-28.458, -71.212),
                #'Caldera':(-27.060,-70.810)}

# -----------------------------------------------------wave----------------------- #
#                                  ATMOSPHERE                                  #
# ---------------------------------------------------------------------------- #
atm_model_name = 'WRF-Ceaza'
# ----------------------------------- paths ---------------------------------- #
atm_forecast_dir   = 'data/FORECAST/WRF/U10V10'           
atm_validation_dir = 'data/ASCAT'                       
# --------------------------- atmospheric variables -------------------------- #
uwnd_name      = 'U10'
vwnd_name      = 'V10'
lsm_name       = 'LANDMASK'
windspeed_name = 'WS'

# ---------------------------------------------------------------------------- #
#                                     WAVES                                    #
# ---------------------------------------------------------------------------- #
wave_model_name = 'MFWAM-Meteofrance'
# ----------------------------------- paths ---------------------------------- #
wave_forecast_dir  = 'data/FORECAST/MERCATOR/WAVES'
wave_hindcast_dir  = 'data/FORECAST/MERCATOR/WAVES/HINDCAST'
wave_altimeter_dir = str('data/WAVES_SATELLITE_NRT/nrt.cmems-du.eu/Core/'+
                     'WAVE_GLO_WAV_L3_SWH_NRT_OBSERVATIONS_014_001')
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
ocean_hindcast_dir    = 'data/FORECAST/MERCATOR/PHYSICS/HINDCAST'
ocean_climatology_dir = 'data/CLIMATOLOGIES.nc'
ocean_validation_dir  = 'data/OSTIA'
# ------------------------------ variable names ------------------------------ #
sst_name = 'thetao'
uo_name  = 'uo'
vo_name  = 'vo'
ssh_name = 'zos'








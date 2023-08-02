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

# ---------------------------------------------------------------------------- #
#                                 GENERAL STUFF                                #
# ---------------------------------------------------------------------------- #
FORECAST_DATE        = datetime.datetime.now().strftime('%F')
EXECUTION_DIRECTORY  = '/home/lucas/projects/CEAZAMAR_KITCHEN/CEAZAMAR_FORECAST'
NDAYS_REGIONAL = 10
NHOURS_LOCAL   = 24*9-12
N_JOBS = 10

#LEADTIME MAPS GENERAL CONFIGURATION
landpolygon_path       = 'data/regiones.gpkg'
atm_mapsextent         = [-75,-70.8,-34,-28]
ocean_mapsextent       = [-75,-70.8,-34,-28]
wave_mapsextent        = [-75,-70.8,-34,-28]
diagnostics_mapsextent = [-75,-70.8,-34,-28]

MAPS_GRID    = (2,5)
MAPS_FIGSIZE = (15,8)

MAPS_LOCS    = {'Valparaíso':(-33.046,-71.613),
                'Los Vilos':(-31.904,-71.499),
                'Huentelauquen':(-31.621,-71.568),
                'Talcaruca':(-30.476,-71.697),
                'La Serena':(-29.878,-71.286),
                'Chañaral de\nAceituno':(-29.064,-71.514)}

# ---------------------------------------------------------------------------- #
#                                  ATMOSPHERE                                  #
# ---------------------------------------------------------------------------- #
atm_model_name      = 'WRF-Ceaza'
atm_validation_name = 'ASCAT'
# ----------------------------------- paths ---------------------------------- #
atm_forecast_dir    = 'data/FORECAST/WRF/U10V10'           
atm_validation_dir  = 'data/ASCAT'                       
# --------------------------- atmospheric variables -------------------------- #
uwnd_name           = 'U10'
vwnd_name           = 'V10'
lsm_name            = 'LANDMASK'
windspeed_name      = 'WS'
winddir_name        = 'WDIR'

# ---------------------------------------------------------------------------- #
#                                     WAVES                                    #
# ---------------------------------------------------------------------------- #
wave_model_name = 'MFWAM-Meteofrance'
# ----------------------------------- paths ---------------------------------- #
wave_forecast_dir  = 'data/FORECAST/MERCATOR/WAVES'
wave_hindcast_dir  = 'data/FORECAST/MERCATOR/WAVES/HINDCAST'
wave_altimeter_dir = str('data/WAVES_SATELLITE_NRT/nrt.cmems-du.eu/Core/'+
                     'WAVE_GLO_PHY_SWH_L3_NRT_014_001')
# ------------------------------ wave variables ------------------------------ #
waveheight_name   = 'VHM0'
swell1height_name = 'VHM0_SW1'
swell2height_name = 'VHM0_SW2'

waveperiod_name   = 'VTPK'
swell1period_name = 'VTM01_SW1'
swell2period_name = 'VTM01_SW2'

wavedir_name      = 'VPED'
swell1dir_name    = 'VMDR_SW1'
swell2dir_name    = 'VMDR_SW2'
# ---------------------------------------------------------------------------- #
#                                     OCEAN                                    #
# ---------------------------------------------------------------------------- #
ocean_model_name       = 'NEMO-Meteofrance'
ocean_validation_name  = 'OSTIA'
# ----------------------------------- paths ---------------------------------- #
ocean_tidemodel_file   = 'data/TPXO7.nc'
ocean_forecast_dir     = 'data/FORECAST/MERCATOR/PHYSICS'
ocean_hindcast_dir     = 'data/FORECAST/MERCATOR/PHYSICS/HINDCAST'
ocean_climatology_file = 'data/CLIMATOLOGIES.nc'
ocean_validation_dir   = 'data/OSTIA'
# ------------------------------ variable names ------------------------------ #
sst_name  = 'thetao'
uo_name   = 'uo'
vo_name   = 'vo'
ssh_name  = 'zos'


# ----------------------------- CUSTOM COLORMAPS ----------------------------- #
hexcolors = ["#4cb164","#5cb35b","#6cb452","#7cb649","#8cb840","#9cb937",
             "#adbb2d","#bdbc24","#cdbe1b","#ddc012","#edc109","#fdc300",
             "#fab302","#f7a204","#f49206","#f18208","#ee720a","#ea610c",
             "#e7510e","#e44110","#e13112","#de2014","#db1016"]
colors    = [mcolors.to_rgb(c) for c in hexcolors]
plt.cm.register_cmap(name='traffic_ceaza',
                     cmap=mcolors.ListedColormap(colors))
del hexcolors, colors

hexcolors = ["#1c8dbe","#3197c4","#45a2ca","#5aacd0","#6fb6d6","#83c1dc",
             "#98cbe1","#acd6e7","#c1e0ed","#d6eaf3","#eaf5f9","#ffffff",
             "#fce9ea","#f8d4d5","#f5bebf","#f2a8aa","#ef9295","#eb7d80",
             "#e8676b","#e55156","#e23b40","#de262b","#db1016"]
colors    = [mcolors.to_rgb(c) for c in hexcolors]
plt.cm.register_cmap(name='redblue_ceaza',
                     cmap=mcolors.ListedColormap(colors))
del hexcolors, colors




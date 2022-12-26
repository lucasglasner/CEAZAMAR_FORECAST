# !/usr/bin/env/python3


'''
 # @ Author: lucas
 # @ Create Time: 2022-08-01 16:09:28
 # @ Modified by: lucas
 # @ Modified time: 2022-08-01 16:09:34
 # @ Description:
 Script principal para correr el pronostico ceazamar
 '''

# ---------------------------------------------------------------------------- #
#                                    IMPORTS                                   #
# ---------------------------------------------------------------------------- #
import os
import sys
import locale
import warnings
import datetime
import pandas as pd
from itertools import repeat
from multiprocessing import Pool

from sst_diagnostics import sst_diagnostics
from wave_diagnostics import wave_diagnostics
from wind_diagnostics import wind_diagnostics

from sst_forecast import sst_forecast
from wave_forecast import wave_forecast
from wind_forecast import wind_forecast
from currents_forecast import currents_forecast
from create_localforecast import create_localforecast
from local_forecast import local_forecast

from sst_validation import sst_validation
from wind_validation import wind_validation

from post_request import transfer_personalweb, transfer_ceazamar

from check_forecast_status import check_forecastfiles, check_regionalforecast
from check_forecast_status import checkcreated_data, check_localforecast


from params import *

# ---------------------------------------------------------------------------- #
#                               GLOBAL VARIABLES                               #
# ---------------------------------------------------------------------------- #
diagnostics=True
if diagnostics:
    make_wind_diagnostics = True
    make_wave_diagnostics = True
    make_sst_diagnostics  = True
validation = True
if validation:
    make_wind_validation = True
    make_wave_validation = False
    make_sst_validation  = True
forecast = True
if forecast:
    make_sst_forecast      = True
    make_wave_forecast     = True
    make_currents_forecast = True
    make_wind_forecast     = True
    make_local_forecast    = True
post_webserver = True
if post_webserver:
    post_ceazamar    = True
    post_personalweb = True
check_todayforecast  = True



os.chdir(EXECUTION_DIRECTORY)
warnings.filterwarnings('ignore')
locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
N=30 #Number of days for validation

def space(char='%',num=120):
    print(char*num)
    return

def now(fmt='%F  %H:%M:%S'):
    return datetime.datetime.now().strftime(fmt)

# ---------------------------------------------------------------------------- #
if __name__=='__main__':
    start = datetime.datetime.now()
    if forecast:
        #start
        space()
        print('LAUNCHING CEAZAMAR REGIONAL AND LOCAL FORECAST VISUALIZATION SYSTEM')
        print('Date: '+now())
        print('Execution directory: '+os.getcwd())
        space()
        if make_sst_forecast:
            #regional sst forecast
            print('\n')
            print('LAUNCHING REGIONAL SST FORECAST: '+now())
            try:
                sst_forecast(FORECAST_DATE, fix_bias=False)
            except Exception as e:
                print(e)
            print('\n')
            space(char='-')
        if make_wave_forecast:
            #regional waves forecast
            print('\n')
            print('LAUNCHING REGIONAL WAVE FORECAST: '+now())
            try:
                wave_forecast(FORECAST_DATE)
            except Exception as e:
                print(e)
            print('\n')
            space(char='-')
        if make_wind_forecast:
            #regional wind forecast
            print('\n')
            print('LAUNCHING REGIONAL WIND FORECAST: '+now())
            try:
                wind_forecast(FORECAST_DATE)
            except Exception as e:
                print(e)
            print('\n')
            space(char='-')
        if make_currents_forecast:
            #regional currents forecast
            print('\n')
            print('LAUNCHING REGIONAL SURFACE CURRENTS FORECAST: '+now())
            try:
                currents_forecast(FORECAST_DATE)
            except Exception as e:
                print(e)
            print('\n')
            space(char='-')
        if make_local_forecast:
            #local point forecast
            print('\n')
            print('LAUNCHING COASTAL ZONES FORECAST: '+now())
            try:
                locations=pd.read_csv('data/COASTAL_POINTS.csv', index_col=0)
                # locations = locations.iloc[:10,:]
                
                print('\nPicking time series forecast as a table for each location...')
                create_localforecast(FORECAST_DATE, locations=locations, n_jobs=N_JOBS)
                outdir = []
                print('Making forecast plots ("oceangrams")...')
                for p,name,lat,lon in zip(locations.CEAZAMAR, locations.index,
                                        locations.lon, locations.lat):
                    text=pd.DataFrame([name.ljust(30,' '),
                        "{:.4f}".format(lon).ljust(20,' '),
                        "{:.4f}".format(lat).ljust(20,' ')]).T.to_string(
                            index=False,header=False)
                    print('Making forecast for: '+text)
                    if p:
                        outdir.append('plots/FORECAST_SITES/CEAZAMAR/')
                    else:
                        outdir.append('plots/FORECAST_SITES/')
                Pool(processes=N_JOBS).starmap(local_forecast,
                                            zip(repeat(FORECAST_DATE, len(locations)),
                                                locations.index,
                                                locations.lon,
                                                locations.lat,
                                                outdir))
            except Exception as e:
                print(e)
            # time.sleep(len(locations)*2)
            print('\n')
            print('Done')
            space(char='-')
            
    if diagnostics:
        #start
        space()
        print('LAUNCHING CEAZAMAR REGIONAL DIAGNOSTICS')
        print('Date: '+now())
        print('Execution directory: '+os.getcwd())
        space()
        if make_sst_diagnostics:
            print('\n')
            print('STARTING TSM DIAGNOSTICS FOR YESTERDAY: '+now())
            try:
                sst_diagnostics((pd.to_datetime(FORECAST_DATE)-pd.Timedelta(days=1)).strftime('%F'))
            except Exception as e:
                print(e)
            print('\n')
            space(char='-')
        if make_wind_diagnostics:
            print('\n')
            print('STARTING WIND DIAGNOSTICS FOR THE DAY AFTER YESTERDAY: '+now())
            try:
                wind_diagnostics((pd.to_datetime(FORECAST_DATE)-pd.Timedelta(days=2)).strftime('%F'))
            except Exception as e:
                print(e)
            print('\n')
            space(char='-')
        if make_wave_diagnostics:
            print('\n')
            print('STARTING WAVE DIAGNOSTICS FOR YESTERDAY: '+now())
            try:
                wave_diagnostics((pd.to_datetime(FORECAST_DATE)-pd.Timedelta(days=1)).strftime('%F'))
            except Exception as e:
                print(e)
            print('\n')
            space(char='-')
            
        
    if validation:
        #start
        space()
        print('LAUNCHING FORECAST DATA VALIDATION AND BIAS COMPUTING.')
        print('Date: '+now())
        print('Execution directory: '+os.getcwd())
        space()
        if make_wind_validation:
            #compute regional wind bias for last N days
            print('\n')
            print('STARTING VALIDATION OF THE LAST '+str(N)+' DAYS OF WIND: '+now())
            try:
                wind_validation(N=N)
            except Exception as e:
                print(e)
            print('\n')
            space(char='-')
        if make_sst_validation:
            #compute regional sst bias for last N days
            print('\n')
            print('STARTING VALIDATION OF THE LAST '+str(N)+' DAYS OF SST: '+now())
            try:
                sst_validation(N=N, bias_fix=False)
            except Exception as e:
                print(e)
            print('\n')
            space(char='-')
        if make_wave_validation:
            #compute regional wave bias
            print('\n')
            print('WAVES VALIDATION NOT YET IMPLEMENTED')
            print('\n')
            space(char='-')     
    if post_webserver:
        #start
        space()
        print('LAUNCHING POST REQUEST AND DATA TRANSFER TO WEB SERVERS.')
        print('Date: '+now())
        print('Execution directory: '+os.getcwd())
        space()
        if post_ceazamar:
            print('\nSending forecast data to CEAZAMAR web server...')
            try:
                transfer_ceazamar()
            except Exception as e:
                print(e)
            print('Done\n')
        if post_personalweb:
            print('Sending forecast to personal web server...')
            try:
                transfer_personalweb()
            except Exception as e:
                print(e)
            print('Done\n')
    if check_todayforecast:
        space()
        print('LAUNCHING FORECAST STATUS VALIDATION SCRIPT')
        print('Date: '+now())
        print('Execution directory: '+os.getcwd())
        space()
        print('CHECKING FORECAST FILES...')
        cond1 = check_forecastfiles()
        print('\n')
        print('CHECKING REGIONAL FORECAST FIGURES...')
        cond2 = check_regionalforecast()
        print('\n')
        print('CHECKING LOCAL FORECAST FILES...')
        cond3 = check_localforecast()
        print("\n")
        if cond1:
            print('FORECAST FILES: OK')
        else:
            print('FORECAST FILES: ERROR')
        if cond2:
            print('REGIONAL FORECAST: OK')
        else:
            print('REGIONAL FORECAST: ERROR')
        if cond3:
            print('LOCAL FORECAST: OK')
        else:
            print('LOCAL FORECAST: ERROR')
        status = all([cond1,cond2,cond3])
        if status:
            print('GLOBAL STATUS: OK')
        else:
            print('GLOBAL STATUS: ERROR')
    space()
    end = datetime.datetime.now()
    print("LISTO !!!")
    print('Execution time: '+str((end-start)))
    print('End time: '+end.strftime('%Y-%m-%d %H:%M:%S'))
    sys.exit()

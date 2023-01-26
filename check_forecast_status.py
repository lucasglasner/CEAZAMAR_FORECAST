'''
 # @ Author: Your name
 # @ Create Time: 2022-10-24 14:34:07
 # @ Modified by: Your name
 # @ Modified time: 2022-10-25 16:19:54
 # @ Description:
 '''

'''
 # @ Author: Your name
 # @ Create Time: 2022-10-24 14:34:07
 # @ Modified by: Your name
 # @ Modified time: 2022-10-25 16:19:35
 # @ Description:
 '''

'''
 # @ Author: lucas
 # @ Create Time: 2022-10-24 14:34:07
 # @ Modified by: lucas
 # @ Modified time: 2022-10-24 14:34:50
 # @ Description:
 
 Script for checking if the ceazamar forecast of today is OK for publication on the website.
 
 '''

from load import load_forecast_ini, forecast_path
from params import *
import pandas as pd
import numpy as np
import datetime
import os

# ---------------------------------------------------------------------------- #
def checkcreated_data(path, date=FORECAST_DATE):
    """
    Given a path, checks if the file was created on the given date
    (default = today)
    
    Args:
        path (str): path to file
        date (str): date
    Returns:
        bool: 
    """
    if os.path.exists(path):
        ctime = os.path.getctime(path)
        ctime = datetime.datetime.fromtimestamp(ctime)
        ttime = pd.to_datetime(date).date()
        cond = ctime.date() == ttime
    else:
        cond=False
    return cond
# ---------------------------------------------------------------------------- #
def check_forecastfiles(date=FORECAST_DATE):
    """
    Args:
        date (str, optional): Date for checking aviable forecast netcdf files.
        Defaults to FORECAST_DATE (params.py).

    Returns:
        status (bool): Downloaded files status
    """
    status=[]
    for ftype in ['ocean','wave','atm']:
        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+
              ' :  Checking '+ftype.upper()+' forecast file...')
        target_path = forecast_path(date, ftype)
        print('                       Path: /home/lucas/CEAZAMAR_FORECAST/'+
            target_path)
        
        ctime = datetime.datetime.fromtimestamp(os.path.getctime(target_path))
        print('                       Creation time: '+
            ctime.strftime('%Y-%m-%d %H:%M:%S'))
        itime = load_forecast_ini(target_path,ftype)
        print('                       Forecast initialization time: '+
            itime)
        tomorrow  = (pd.to_datetime(date)+pd.Timedelta(days=1)).strftime('%F')
        yesterday = (pd.to_datetime(date)-pd.Timedelta(days=1)).strftime('%F')
        fstatus  = checkcreated_data(target_path,date=date)
        fstatus1 = checkcreated_data(target_path,date=yesterday)
        fstatus2 = checkcreated_data(target_path,date=tomorrow)
        fstatus = fstatus or fstatus1 or fstatus2
        if fstatus:
            print('                       Forecast status: OK')
        else:
            print('                       Forecast status: ERROR - '+
                  'Forecast file is not from '+yesterday+' nor '+date+
                  ' nor '+tomorrow+'!')
        status.append(fstatus)
        print('\n')
    status = all(status)
    return status

# ---------------------------------------------------------------------------- #
def check_regionalforecast(date=FORECAST_DATE):
    """
    Args:
        date (str, optional): Date for checking aviable forecast netcdf files.
        Defaults to FORECAST_DATE (params.py).
    Returns:
        status (bool): Regional forecast maps (plots/*.png) status
    """
    files = ['SST','SEALEVEL_ANOMALY','SURFACECURRENTS',
             'WAVEHEIGHT','PERIOD','WINDSPEED']
    status=[]
    for f in files:
        f = 'plots/'+f+'_FORECASTMAP_CURRENT.png'
        if os.path.isfile(f):
            ctime   = datetime.datetime.fromtimestamp(os.path.getctime(f))
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+
                  ' :  Path: '+f)
            print('                       Creation time: '+
                ctime.strftime('%Y-%m-%d %H:%M:%S'))
            fstatus = checkcreated_data(f,date=date)
            if fstatus:
                print('                       Figure status: OK')
            else:
                print('                       Figure status: ERROR - Figure '+
                      f.replace('plots/','')+' is not from today !')
            status.append(fstatus)
            print("\n")
        else:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+
                  ' :  ERROR: "'+f+'" doesnt exists!!')
            status.append(False)
            print("\n")
    
    status=all(status)
    return status
# ---------------------------------------------------------------------------- #
def checkcreated_table(name):
    """
    Given the name of a place, checks if the table for today
    is already created
    
    Args:
        name (str): name of a place in COASTAL_POINTS.csv

    Returns:
        cond (bool): 
    """
    path='tmp/'+name.replace("_","")+'_CURRENT.csv'
    if os.path.exists(path):
        ctime = os.path.getctime(path)
        ctime = datetime.datetime.fromtimestamp(ctime)
        cond = ctime.date() == datetime.datetime.now().date()
    else:
        cond=False
    return cond
# ---------------------------------------------------------------------------- #
def check_localforecast(date=FORECAST_DATE):
    """
    Args:
        date (str, optional): Date for checking aviable forecast netcdf files.
        Defaults to FORECAST_DATE (params.py).

    Returns:
        status (bool): Created files and figures (oceangrams) status
    """
    locations = pd.read_csv('data/COASTAL_POINTS.csv', index_col=0)
    locations = list(locations[locations['CEAZAMAR']].index)
    status=[]
    for site in locations:
        p         = 'tmp/'+site.replace('_','')+'_FORECAST_CURRENT.csv'
        if os.path.isfile(p):
            ddate = pd.to_datetime(pd.read_csv(p, index_col=0).index[0])
            ddate = ddate.strftime('%F')
            pass
        else:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' :  '+
                  site+' - File "'+p+'" doesnt exists!')
            status.append(False)
            continue
        pf        = 'plots/FORECAST_SITES/CEAZAMAR/'+site.replace('_','')
        pf        = pf+'_FORECAST_CURRENT.png'
        if os.path.isfile(pf):
            pass
        else:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' :  '+
                  site+' - File "'+pf+'" doesnt exists!')
            status.append(False)
            continue
        data      = pd.read_csv(p, index_col=0)[['WS','WDIR','VHM0','thetao']]
        fstatus1  = ddate == date
        fstatus2  = np.isnan(data).sum().sum()==0
        fstatus3  = checkcreated_data(pf, date=date)
        fstatus   = all([fstatus1, fstatus2, fstatus3])
        if fstatus1:
            if fstatus2:
                if fstatus3:
                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' :  '+
                        site+' - File and figure status: OK')
                else:
                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' :  '+
                          site+' - File and figure status: ERROR - '+
                          'Forecast file (meteogram) is not from '+date+' !')
                    
            else:
                print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' :  '+
                  site+' - File and figure status: ERROR - '+
                  'Forecast file for '+date+' has NaNs !')
        else:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' :  '+
                  site+' - File and figure status: ERROR - '+
                  'Forecast file is not from '+date+' !')
        status.append(fstatus)
        
    status = all(status)
    return status


if __name__=='__main__':
    print('CHECKING FORECAST FILES...')
    cond1 = check_forecastfiles()
    print("\n")
    print('CHECKING REGIONAL FORECAST FIGURES...')
    cond2 = check_regionalforecast()
    print('CHECKING LOCAL FORECAST FILES...')
    cond3 = check_localforecast()
    print('\n')
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

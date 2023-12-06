'''
 # @ Author:lucas
 # @ Create Time: 2022-07-29 14:36:43
 # @ Modified by: lucas
 # @ Modified time: 2022-07-29 14:40:25
 # @ Description: Compute (if needed) and post forecast in the webservice
 (my own or ceazamar)
 '''
from params import *
from glob import glob
import pandas as pd
import requests
import os

regionalforecastdir=EXECUTION_DIRECTORY+'/plots/'
localforecastdir=EXECUTION_DIRECTORY+'/plots/FORECAST_SITES/'
weburl="https://lhgv.pythonanywhere.com/upload_forecast"
# ---------------------------------------------------------------------------- #
def transfer_ceazamar(remotehost='lucas@ip1.ceazamet.cl',
                      remotepath_regional='/home/lucas/PRONOSTICOS/REGIONAL/',
                      remotepath_local_tables='/home/lucas/PRONOSTICOS/LOCAL/DATA/',
                      remotepath_local_figures='/home/lucas/PRONOSTICOS/LOCAL/'):
    os.system('scp -P 10722 '+regionalforecastdir+
            f'*.png {remotehost}:{remotepath_regional}')
    locations=pd.read_csv('data/COASTAL_POINTS.csv', index_col=0)
    names = locations[locations['REGION']=='COQUIMBO']
    names = names[names['CEAZAMAR']].Name
    for name in names:
        name = name.replace('_','')
        os.system('scp -P 10722 '+EXECUTION_DIRECTORY+f'/tmp/{name}*.csv '+
                f'{remotehost}:{remotepath_local_tables}')
        os.system('scp -P 10722 '+localforecastdir+
                f'CEAZAMAR/{name}*.png {remotehost}:{remotepath_local_figures}')
        os.system('scp -P 10722 '+localforecastdir+
                f'CEAZAMAR/{name}*.pdf {remotehost}:{remotepath_local_figures}')
    return

def transfer_personalweb():
    paths = glob(localforecastdir+'*FORECAST*.png')
    paths = paths + glob(localforecastdir+'CEAZAMAR/*FORECAST*.png')
    paths = paths + glob(regionalforecastdir+'*.png')
    files = {'img'+str(i):open(p, 'rb') for i,p in enumerate(paths)}
    resp = requests.post(weburl, files=files)
    print(resp.text)
    return resp.text

if __name__=='__main__':
    transfer_ceazamar()
    transfer_personalweb()
    


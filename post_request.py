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
def transfer_ceazamar():
    os.system('scp -P 10722 '+regionalforecastdir+
            '*.png lucas@ip1.ceazamet.cl:/home/lucas/PRONOSTICOS/REGIONAL/')
    locations=pd.read_csv('data/COASTAL_POINTS.csv', index_col=0)
    names = locations[locations['REGION']=='COQUIMBO']
    names = names[names['CEAZAMAR']].Name
    for name in names:
        name = name.replace('_','')
        os.system('scp -P 10722 '+EXECUTION_DIRECTORY+f'/tmp/{name}*.csv '+
                'lucas@ip1.ceazamet.cl:/home/lucas/PRONOSTICOS/LOCAL/DATA/')
        os.system('scp -P 10722 '+localforecastdir+
                f'CEAZAMAR/{name}*.png lucas@ip1.ceazamet.cl:/home/lucas/PRONOSTICOS/LOCAL/')
        os.system('scp -P 10722 '+localforecastdir+
                f'CEAZAMAR/{name}*.pdf lucas@ip1.ceazamet.cl:/home/lucas/PRONOSTICOS/LOCAL/')
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
    


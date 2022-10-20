'''
 # @ Author:lucas
 # @ Create Time: 2022-07-29 14:36:43
 # @ Modified by: lucas
 # @ Modified time: 2022-07-29 14:40:25
 # @ Description: Compute (if needed) and post forecast in the webservice
 (my own or ceazamar)
 '''
from load import checkcreated_data
from params import *
from glob import glob
import requests
import pandas as pd
import os

regionalforecastdir=EXECUTION_DIRECTORY+'/plots/'
localforecastdir=EXECUTION_DIRECTORY+'/plots/FORECAST_SITES/'
weburl="https://lhgv.pythonanywhere.com/upload_forecast"
# ---------------------------------------------------------------------------- #
def transfer_ceazamar():
    print('          Sending forecast to CEAZAMAR web server...')
    os.system('scp -P 10722 '+EXECUTION_DIRECTORY+'/tmp/*.csv '+
              'lucas@ip1.ceazamet.cl:/home/lucas/PRONOSTICOS/LOCAL/DATA/')
    os.system('scp -P 10722 '+regionalforecastdir+
            '*.png lucas@ip1.ceazamet.cl:/home/lucas/PRONOSTICOS/REGIONAL/')
    os.system('scp -P 10722 '+localforecastdir+
            'CEAZAMAR/*.png lucas@ip1.ceazamet.cl:/home/lucas/PRONOSTICOS/LOCAL/')
    print('          Done')
    return

def postserver(imgpath):
    print('          '+imgpath)
    img = {'img':open(imgpath,'rb')}
    resp = requests.post(weburl,files=img)
    return resp.text

def transfer_personalweb():
    print('          Sending forecast to personal web server...')
    paths = glob(localforecastdir+'*FORECAST*.png')
    paths = paths + glob(localforecastdir+'CEAZAMAR/*FORECAST*.png')
    for p in paths:
        postserver(p)
    for p in glob(regionalforecastdir+'*FORECAST*.png'):
        postserver(p)
    print('          Done')
    return

if __name__=='__main__':
    transfer_ceazamar()
    transfer_personalweb()
    


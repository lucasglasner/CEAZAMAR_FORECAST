'''
 # @ Author: Your name
 # @ Create Time: 2023-09-25 10:31:45
 # @ Modified by: Your name
 # @ Modified time: 2023-09-25 10:32:00
 # @ Description:
 This script takes the "oceangram" plot and creates a pdf where each page is 
 each day forecast
 '''



import matplotlib.pyplot as plt
import numpy as np
import sys
import os


from params import *
from glob import glob
from pypdf import PdfMerger

def local_forecast_print(oceangram_png):
    print(oceangram_png.split('/')[-1].split('.')[0])
    img    = plt.imread(oceangram_png)
    header = img[:,:260,:] 
    slices = [slice(260,1441), slice(1441,2622), slice(2620,3800),
            slice(3799,4980), slice(4979,6159), slice(6159,7340),
            slice(7338,8521), slice(8518,9700), slice(9698,10346)]
    days   = [np.concatenate([header,img[:,s,:]], axis=1) for s in slices]
    days   = [np.transpose(d[::-1,:,:], (1,0,2)) for d in days]
    for i in range(len(days)):
        plt.imsave(f'tmp/oceangram{i}.pdf',days[i])
        
    pdfs = sorted(glob('tmp/oceangram*.pdf'))
    merger = PdfMerger()
    for pdf in pdfs:
        merger.append(pdf)
    merger.write(oceangram_png.replace('.png','.pdf'))
    merger.close()
    os.system('rm -f tmp/oceangram*.pdf')
    return
        
if __name__=='__main__':
    print('Transforming "oceangrams" to printable pdfs')
    local_forecast_print('plots/FORECAST_SITES/CEAZAMAR/APOLILLADO_FORECAST_CURRENT.png')
    sys.exit()

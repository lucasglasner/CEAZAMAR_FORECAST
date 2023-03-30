'''
 # @ Author: Your lucas
 # @ Create Time: 2022-07-22 19:35:24
 # @ Modified by: lucas
 # @ Modified time: 2022-07-22 19:35:46
 # @ Description:
 '''


# ---------------------------------------------------------------------------- #
# ---------------------------------- Imports --------------------------------- #
# ---------------------------------------------------------------------------- #

import xesmf as xe
import xarray as xr
import numpy as np
import pandas as pd
import scipy.signal as signal

# ---------------------------------------------------------------------------- #
# ---------------------------- Numerical data functions ---------------------- #
# ---------------------------------------------------------------------------- #

def coriolis_parameter(lat, units='deg'):
    """
    This function computes the classical coriolis parameter
    or planetary vorticity from an array of latitudes.

    Args:
        lat (array): latitude
        units (str, optional): units of latitude array.
        Defaults to 'deg'.

    Raises:
        ValueError: If units is not deg or rad

    Returns:
        array: coriolis parameter
    """
    if units == 'deg':
        lat = np.deg2rad(lat)
    elif units == 'rad':
        pass
    else:
        raise ValueError('units should be "deg" or "rad" not'+str(units))
    omega = 1/(24*3600) #Earth axis angular speed
    f     = 2*omega*np.sin(lat)
    return f
    

def julian_day(date):
    """
    From a python datetime compute the julian day

    Args:
        date (datetime or timestamp): date

    Returns:
        float: julian day
    """
    return date.toordinal()+1721424.5

def modified_julian_day(date):
    """
    From a python datetime compute the modified julian day

    Args:
        date (datetime or timestamp): date

    Returns:
        float: modified julian day
    """
    mjd = julian_day(date)-2400000.5
    return mjd


def rhopoints_depths(h,zeta,s_rho,Cs_r,hc,vtransform=2):
    """ Compute depth of roms sigma coordinates.

    Args:
        h (_type_): _description_
        zeta (_type_): _description_
        s_rho (_type_): _description_
        Cs_r (_type_): _description_
        hc (_type_): _description_
        vtransform (int, optional): _description_. Defaults to 2.

    Returns:
        _type_: _description_
    """
    if vtransform==1:
        Z_rho = hc*(s_rho-Cs_r)+Cs_r*h
        z_rho = Z_rho+zeta*(1+Z_rho/h)
        return z_rho
    else:
        Z_rho = (hc*s_rho+Cs_r*h)/(hc+h)
        z_rho = zeta+(zeta+h)*Z_rho
        return z_rho
    

def haversine(p1,p2):
    """
    Given two points with lat,lon coordinates, compute the distance 
    between those points on the surface of the sphere with the haversine formula
    Args:
        p1 (tuple): first point lat,lon
        p2 (tuple): last point lat,lon

    Returns:
        float: distance
    """
    lat1,lon1 = p1
    lat2,lon2 = p2
    
    lon1,lon2,lat1,lat2 = map(np.deg2rad, [lon1,lon2,lat1,lat2])
    
    dlon = lon2-lon1
    dlat = lat2-lat1
    
    a = np.sin(dlat/2)**2+np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    c = 2*np.arcsin(np.sqrt(a))
    r = 6371
    return c*r
    


def fill_borders(data):
    """
    Fill all nans with forward and backward filling.

    Args:
        data (xarray): 

    Returns:
        xarray: 
    """
    #fill bays with pixels from the top
    data = data.bfill('lat', limit=4)
    data = data.ffill('lon').bfill('lon')
    data = data.ffill('lat').bfill('lat')
    return data

def regrid(data,husk,method='bilinear'):
    """
    Regrid dataset to a new latlon grid.

    Args:
        data (xarray): Data to regrid
        husk (xarray): Data with the new coordinates.
        method (str, optional):
         "bilinear","conservative","nearests2d"
         Defaults to 'bilinear'.

    Returns:
        (xarray): Regridded data using xESMF routines.
    """
    regridder = xe.Regridder(data,husk,method)
    return regridder(data)

def compute_metrics(model,reference, dim='time'):
    """
    Compute model metrics (MBIAS, RMSE, pearsonr) against reference.

    Args:
        model xarray: _description_
        reference xarray: _description_
        dim (str, optional): dimension to reduce along. Defaults to 'time'.

    Returns:
        xarray: Dataset with stored metrics
    """
    BIAS  = model-reference
    MBIAS = BIAS.mean(dim)
    RMSE  = (BIAS**2).mean(dim)**0.5
    CORR  = xr.corr(model,reference,dim)
    METRICS = xr.merge([MBIAS.to_dataset(name='MBIAS'),
                        RMSE.to_dataset(name='RMSE'),
                        CORR.to_dataset(name='CORR')])
    return METRICS


def bias_correct_SST(data,method='linregress'):
    """
    Bias correct SST with delta method or linregress
    Require the files with the coefficient or correction data.

    Args:
        data (xarray): 
         Mercator forecast sea surface temperature
        method (str, optional): 
         linregress or delta. Defaults to 'linregress'.

    Returns:
        xarray: bias corrected mercator sst as xarray object
    """
    if method == 'delta':
        p = '~/storage/FORECAST/MERCATOR/'
        mbias = xr.open_dataset(p+'MBIAS_MERCATORANALYSIS-OSTIA_MONTHLY.nc').mbias
        mbias = mbias.rename({'longitude':'lon','latitude':'lat'})
        mbias = mbias.reindex({'lon':data.lon,'lat':data.lat},
                            method='nearest')
        data = data.groupby('time.dayofyear')-mbias
    if method == 'linregress':
        p = '~/storage/FORECAST/MERCATOR/'
        lr = xr.open_dataset(p+'LINEAR_REGRESSION_COEFFICIENTS.nc')
        lr = lr.reindex({'lon':data.lon,'lat':data.lat},
                            method='nearest')
        data = data*lr.SLOPE+lr.INTERCEPT
    return data


def deg2compass(angle):
    """
    Transform an angle in degrees to the
    windrose string.
    The angle increases clockwise with 0° pointing North.

    Args:
        angle (float): Angle in degrees

    Returns:
        str: vector direction string
    """
    if angle<0:
        angle = angle+360
    if np.isnan(angle):
        return np.nan
    val = int((angle/45)+0.5)
    arr = np.array(['N','NE','E','SE','S','SW','W','NW'])
    return arr[(val%8)]

def coastwinddir(u,v,land_sea_mask):
    """
    Compute wind angle against coastline

    Args:
        u (xarray): zonal wind
        v (xarray): meridional wind
        land_sea_mask (xarray): Land sea mask

    Returns:
        angle: raster with the angle of the wind respect to coastline
    """
    LSM = land_sea_mask
    LSM = (LSM.where(LSM==1).ffill('lon')==1).astype(float)
    LSM_GRADIENT=LSM.differentiate('lon'),LSM.differentiate('lat')
    LSM_GRADIENT_MODULE=(LSM_GRADIENT[0]**2+LSM_GRADIENT[1]**2)**0.5    
    ws = (u**2+v**2)**0.5
    angle = LSM_GRADIENT[0]*u+LSM_GRADIENT[1]*v
    angle = angle/(LSM_GRADIENT_MODULE*ws)*180/np.pi
    angle = angle.where(~LSM.astype(bool))
    return angle

def beaufort_scale(wind):
    """
    Given the wind (knots) return the beaufort number
    
    Args:
        wind (float): wind in knots

    Returns:
        int: beaufort number
    """
    scale=np.array([0,1,4,7,11,17,22,28,34,41,48,56,64,np.inf])
    for n in range(len(scale)-1):
        if scale[n]<=wind and scale[n+1]>wind:
            return int(n)
    

def seasonal_decompose(ts, period, nharmonics=3, bandwidth=2):
    """
    Parameters
    ----------
    ts : Time series data in a pandas series format, with timestamps
         in the index.
    period : period of the season
    nharmonics : Number of harmonics to remove, default is 3.

    Returns
    -------
    season : Seasonal component of the time series.
    anomaly : The time series anomaly without the seasonal cycle.
    """
    if len(ts)%2==0:
        n = len(ts)
    else:
        n = len(ts)+1
    ft = np.fft.fft(ts)
    ft[0] = 0  # Remove mean#
    for i in range(nharmonics):  # Filter cycle#
        pos = n//(period//(i+1))
        ft[pos-bandwidth:pos+bandwidth] = 0
        ft[n-pos-bandwidth:n-pos+bandwidth] = 0
        # ft[pos]=0
        # ft[n-pos]=0
    anomaly = np.fft.ifft(ft).real
    # anomaly = pd.Series(anomaly, index=ts.index)
    season = ts-anomaly
    return season

def filter_timeseries(ts, order, cutoff, btype='lowpass', fs=1, **kwargs):
    """Given an array, this function apply a butterworth (high/low pass) 
    filter of the given order and cutoff frequency.
    For example:
    If 'ts' is a timeseries of daily samples, filter_timeseries(ts,3,1/20)
    will return the series without the 20 days or less variability using an
    order 3 butterworth filter. 
    In the same way, filter_timeseries(ts,3,1/20, btype='highpass') will
    return the series with only the 20 days or less variability.

    Args:
        ts (array_like): timeseries or 1D array to filter
        order (int): _description_
        cutoff (array_like): Single float for lowpass or highpass filters, 
        arraylike for bandpass filters.
        btype (str, optional): The type of filter. Defaults to 'lowpass'.
        fs (int): Sampling frequency. Defaults to 1.s
        **kwargs are passed to scipy.signal.butter

    Returns:
        output (array): Filtered array
    """
    mask = np.isnan(ts)
    nans = np.ones(len(ts))*np.nan
    if mask.sum()==len(ts):
        return nans
    else:
        b, a = signal.butter(order,cutoff, btype=btype, fs=fs, **kwargs)
        filt=signal.filtfilt(b, a, ts[~mask])
        output=np.ones(len(ts))*np.nan
        output[np.where(~mask)] = filt
        return output
    
def filter_xarray(data, dim, order, cutoff, btype='lowpass', parallel=True, fs=1):
    """Given a 3d DataArray, with time and spatial coordinates, this function apply
    the 1D function filter_timeseries along the time dimension, filter the complete
    xarray data.

    Args:
        data (XDataArray): data
        dim (str): name of the time dimension
        order (int): butterworth filter order
        cutoff (array_like): if float, the cutoff frequency, if array must be the
                            [min,max] frequencys for the bandpass filter.
        btype (str, optional): {lowpass,highpass,bandpass}. Defaults to 'lowpass'.
        parallel (bool, optional): If parallelize with dask. Defaults to True.
        fs (int, optional): Sampling frequency. Defaults to 1.

    Returns:
        XDataArray: filtered data
    """
    if parallel:
        dask='parallelized'
    else:
        dask='forbidden'
    filt = xr.apply_ufunc(filter_timeseries, data, order, cutoff, btype, fs,
                          input_core_dims=[[dim],[],[],[],[]],
                          output_core_dims=[[dim]],
                          exclude_dims=set((dim,)),
                          keep_attrs=True,
                          vectorize=True, dask=dask)
    filt[dim] = data[dim]
    return filt

def compute_anomalies(forecast, climatology, timename='leadtime'):
    """Compute anomaly from climatology

    Args:
        forecast (XDataArray): forecast data
        climatology (XDataArray): climatology data

    Returns:
        XDataArray: anomaly
    """
    climatology = climatology.reindex({'lat':forecast.lat,'lon':forecast.lon})
    anomaly = forecast.groupby(timename+'.dayofyear')-climatology
    return anomaly

def utc_to_local(series, gap=4):
    """
    Transform pandas series with datetime index from UTC time to local

    Args:
        series (pd.Series): pandas timeseries with utc data 

    Returns:
        pd.Series: data in local time
    """
    series.index = series.index-pd.Timedelta(hours=gap)
    return series

def grabpoint(data,lat,lon,method='nearest'):
    """
    Given a coordinate in lat,lon an a netcdf file in data (as
    an xarray object), this function grabs the timeseries
    in the specified coordinate.

    Args:
        data (xarray): _description_
        lat (float): _description_
        lon (float): _description_
        method (str, optional): Interpolation method. Defaults to 'nearest'.

    Returns:
        pd.Dataframe: timeseries of the pixel as a dataframe
    """
    point = fill_borders(data).interp(lat=lat,lon=lon, method=method)
    point = point.to_dataframe()
    return point


    
def egbert_correct(mjd, hour, minutes, seconds):
    """
    #  Correct phases and amplitudes for real time runs
    #  Use parts of pos-processing code from Egbert's & Erofeeva's (OSU) 
    #  TPXO model. Their routines have been adapted from code by Richard Ray 
    #  (@?) and David Cartwright.
    #  Adapted to python from crocotoolsv1.2 egbert_correct.m function
    """
    #---------------------------------------------------------------------
    tstart=mjd+hour/24+minutes/(60*24)+seconds/(60*60*24)
    # Determine nodal corrections pu & pf :
    # these expressions are valid for period 1990-2010 (Cartwright 1990).
    # reset time origin for astronomical arguments to 4th of May 1860:
    timetemp=tstart-51544.4993;
    # ---------------------------------------------------------------------------- #
    # mean longitude of lunar perigee
    P =  83.3535 +  0.11140353 * timetemp
    P = np.mod(P,360.0)
    # P[P<0.0] = P[P<0.0] + 360.0
    P=P*np.pi/180;
    # ---------------------------------------------------------------------------- #
    # mean longitude of ascending lunar node
    N = 125.0445 -  0.05295377 * timetemp
    N = np.mod(N,360.0)
    # N[N<0.0] = N[N<0.0] + 360.0
    N=N*np.pi/180
    # ---------------------------------------------------------------------------- #
    # nodal corrections: pf = amplitude scaling factor [], 
    #                    pu = phase correction [deg]
    sinn  = np.sin(N);
    cosn  = np.cos(N);
    sin2n = np.sin(2*N);
    cos2n = np.cos(2*N);
    sin3n = np.sin(3*N);
    tmp1  = 1.36*np.cos(P)+0.267*np.cos((P-N))
    tmp2  = 0.64*np.sin(P)+0.135*np.sin((P-N));
    temp1 = 1-0.25*np.cos(2*P)-0.11*np.cos((2*P-N))-0.04*cosn
    temp2 = 0.25*np.sin(2*P)+0.11*np.sin((2*P-N))+0.04*sinn
    pftmp = np.hypot((1-0.03731*cosn+0.00052*cos2n),(0.03731*sinn-0.00052*sin2n))
    
    pf    = np.empty(10)
    pf[0] = pftmp                                                              # M2
    pf[1] = 1.0                                                                # S2
    pf[2] = pftmp                                                              # N2
    pf[3] = np.hypot((1+0.2852*cosn+0.0324*cos2n),(0.3108*sinn+0.0324*sin2n))  # K2
    pf[4] = np.hypot((1+0.1158*cosn-0.0029*cos2n),(0.1554*sinn-0.0029*sin2n))  # K1
    pf[5] = np.hypot((1+0.189*cosn-0.0058*cos2n),(0.189*sinn -0.0058*sin2n))   # O1
    pf[6] = 1.0                                                                # P1
    pf[7] = np.hypot((1+0.188*cosn),(0.188*sinn))                              # Q1
    pf[8] = 1.043 + 0.414*cosn                                                 # Mf
    pf[9] = 1.0 - 0.130*cosn                                                   # Mm

    putmp = np.arctan((-0.03731*sinn+0.00052*sin2n)/
                   (1-0.03731*cosn+0.00052*cos2n))*180/np.pi                   # 2N2

    pu    = np.empty(10)
    pu[0] = putmp                                                              # M2
    pu[1] = 0.0;                                                               # S2
    pu[2] = putmp;                                                             # N2
    pu[3] = np.arctan(-(0.3108*sinn+0.0324*sin2n)/
                    (1+0.2852*cosn+0.0324*cos2n))*180/np.pi;                   # K2
    pu[4] = np.arctan((-0.1554*sinn+0.0029*sin2n)/
                    (1+0.1158*cosn-0.0029*cos2n))*180/np.pi                    # K1
    pu[5] = 10.8*sinn - 1.3*sin2n + 0.2*sin3n;                                 # O1
    pu[6] = 0.0;                                                               # P1
    pu[7] = np.arctan(.189*sinn/(1.+.189*cosn))*180/np.pi;                     # Q1
    pu[8] = -23.7*sinn + 2.7*sin2n - 0.4*sin3n;                                # Mf
    pu[9] = 0.0;                                                               # Mm
    
    
    
    # to determine phase shifts below time should be in hours
    # relatively Jan 1 1992 (=48622mjd) 
        
    t0=48622.0*24.0;

    # Astronomical arguments, obtained with Richard Ray's
    # "arguments" and "astrol", for Jan 1, 1992, 00:00 Greenwich time

    phase_mkB=[1.731557546,   # M2
               0.000000000,   # S2
               6.050721243,   # N2
               3.487600001,   # K2
               0.173003674,   # K1
               1.558553872,   # O1
               6.110181633,   # P1
               5.877717569,   # Q1
               1.756042456,   # Mf
               1.964021610]   # Mm
    
    index = ['M2','S2','N2','K2','K1','O1','P1','Q1','Mf','Mm']
    pf    = pd.Series(pf, index=index)
    pu    = pd.Series(pu, index=index)
    phase_mkB = pd.Series(np.array(phase_mkB)*180/np.pi, index=index)

    return pf,pu,t0,phase_mkB
'''
 # @ Author: lucas
 # @ Create Time: 2022-07-22 14:20:23
 # @ Modified by: lucas
 # @ Modified time: 2022-07-22 15:19:50
 # @ Description:
 '''

# ---------------------------------------------------------------------------- #
# ---------------------------------- Imports --------------------------------- #
# ---------------------------------------------------------------------------- #
import numpy as np
import pandas as pd


import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
from matplotlib import axes as maxes
from matplotlib import axis as maxis
import matplotlib.ticker as mticker
import matplotlib.cbook as cbook
from matplotlib.projections import register_projection
import cartopy.crs as ccrs
import cartopy.feature as cf
import geopandas as gpd
from shapely.geometry import Polygon

from numerics import fill_borders
from params import *

# ---------------------------------------------------------------------------- #
# ---------------------------------- classes --------------------------------- #
# ---------------------------------------------------------------------------- #

class SubMinorXAxis(maxis.XAxis):
    def __init__(self,*args,**kwargs):
        self.subminor = maxis.Ticker()
        self.subminorTicks = []
        self._subminor_tick_kw = dict()

        super(SubMinorXAxis,self).__init__(*args,**kwargs)


    def reset_ticks(self):
        cbook.popall(self.subminorTicks)
        ##self.subminorTicks.extend([self._get_tick(major=False)])
        self.subminorTicks.extend([maxis.XTick(self.axes, 0, '', major=False, **self._subminor_tick_kw)])
        self._lastNumSubminorTicks = 1
        super(SubMinorXAxis,self).reset_ticks()


    def set_subminor_locator(self, locator):
        """
        Set the locator of the subminor ticker

        ACCEPTS: a :class:`~matplotlib.ticker.Locator` instance
        """
        self.isDefault_minloc = False
        self.subminor.locator = locator
        locator.set_axis(self)
        self.stale = True


    def set_subminor_formatter(self, formatter):
        """
        Set the formatter of the subminor ticker

        ACCEPTS: A :class:`~matplotlib.ticker.Formatter` instance
        """
        self.isDefault_minfmt = False
        self.subminor.formatter = formatter
        formatter.set_axis(self)
        self.stale = True


    def get_subminor_ticks(self, numticks=None):
        'get the subminor tick instances; grow as necessary'
        if numticks is None:
            numticks = len(self.get_subminor_locator()())

        if len(self.subminorTicks) < numticks:
            # update the new tick label properties from the old
            for i in range(numticks - len(self.subminorTicks)):
                ##tick = self._get_tick(major=False)
                tick = maxis.XTick(self.axes, 0, '', major=False, **self._subminor_tick_kw)
                self.subminorTicks.append(tick)

        if self._lastNumSubminorTicks < numticks:
            protoTick = self.subminorTicks[0]
            for i in range(self._lastNumSubminorTicks, len(self.subminorTicks)):
                tick = self.subminorTicks[i]
                tick.gridOn = False
                self._copy_tick_props(protoTick, tick)

        self._lastNumSubminorTicks = numticks
        ticks = self.subminorTicks[:numticks]

        return ticks

    def set_tick_params(self, which='major', reset=False, **kwargs):
        if which == 'subminor':
            kwtrans = self._translate_tick_kw(kwargs, to_init_kw=True)
            if reset:
                self.reset_ticks()
                self._subminor_tick_kw.clear()
            self._subminor_tick_kw.update(kwtrans)

            for tick in self.subminorTicks:
                tick._apply_params(**self._subminor_tick_kw)
        else:
            super(SubMinorXAxis, self).set_tick_params(which=which, reset=reset, **kwargs)

    def cla(self):
        'clear the current axis'
        self.set_subminor_locator(mticker.NullLocator())
        self.set_subminor_formatter(mticker.NullFormatter())

        super(SubMinorXAxis,self).cla()


    def iter_ticks(self):
        """
        Iterate through all of the major and minor ticks.
        ...and through the subminors
        """
        majorLocs = self.major.locator()
        majorTicks = self.get_major_ticks(len(majorLocs))
        self.major.formatter.set_locs(majorLocs)
        majorLabels = [self.major.formatter(val, i)
                       for i, val in enumerate(majorLocs)]

        minorLocs = self.minor.locator()
        minorTicks = self.get_minor_ticks(len(minorLocs))
        self.minor.formatter.set_locs(minorLocs)
        minorLabels = [self.minor.formatter(val, i)
                       for i, val in enumerate(minorLocs)]

        subminorLocs = self.subminor.locator()
        subminorTicks = self.get_subminor_ticks(len(subminorLocs))
        self.subminor.formatter.set_locs(subminorLocs)
        subminorLabels = [self.subminor.formatter(val, i)
                       for i, val in enumerate(subminorLocs)]

        major_minor = [
            (majorTicks, majorLocs, majorLabels),
            (minorTicks, minorLocs, minorLabels),
            (subminorTicks, subminorLocs, subminorLabels),
        ]

        for group in major_minor:
            for tick in zip(*group):
                yield tick


class SubMinorAxes(maxes.Axes):
    name = 'subminor'

    def _init_axis(self):
        self.xaxis = SubMinorXAxis(self)
        self.spines['top'].register_axis(self.xaxis)
        self.spines['bottom'].register_axis(self.xaxis)
        self.yaxis = maxis.YAxis(self)
        self.spines['left'].register_axis(self.yaxis)
        self.spines['right'].register_axis(self.yaxis)

register_projection(SubMinorAxes)

# ---------------------------------------------------------------------------- #
# ---------------------------- Plotting functions ---------------------------- #
# ---------------------------------------------------------------------------- #

def make_maps(shape,figsize,
              xticks=[],
              yticks=[],
              colorbar='one',
              loclats=[x[0] for x in MAPS_LOCS.values()],
              loclons=[x[1] for x in MAPS_LOCS.values()],
              locnames=MAPS_LOCS.keys(),
              extent=[-85,-69,-45,-15],
              proj=ccrs.PlateCarree(),
              **kwargs):
    rows,cols = shape
    #Create figure
    fig,ax = plt.subplots(rows,cols,sharex=True,sharey=True,
                          subplot_kw={'projection':proj},
                          figsize=figsize, **kwargs)
    LAND    = gpd.read_file(landpolygon_path)
    polygon = Polygon(zip([extent[0], extent[1], extent[1], extent[0], extent[0]],
                          [extent[2], extent[2], extent[3], extent[3], extent[2]]))
    polygon = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[polygon])
    LAND    = gpd.clip(LAND,polygon)
    #Check axis grid dimension
    if np.size(ax)==1:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
        LAND.plot(ax=ax, color='silver', lw=0, zorder=3)
        LAND.boundary.plot(ax=ax, color='k', lw=0.25, zorder=3)
        ax.scatter(loclons,loclats, color='gold', edgecolor='k',
                    zorder=3,s=20)
        for i, txt in enumerate(locnames):
            ax.annotate(txt, (loclons[i]+0.075,loclats[i]-0.05),
                        fontsize=8,
                        zorder=3)
        #Create colorbar(s) axis
        if colorbar == 'one':
            box = ax.get_position()
            cax = fig.add_axes([box.xmax*1.05,box.ymin,0.01,box.ymax-box.ymin])
        else:
            cax = None
        #Place tick labels
        ax.set_yticks(yticks)
        ax.set_yticklabels(list(map(lambda x: str(-x)+'$\degree S$',yticks)))
    
        ax.set_xticks(xticks)
        ax.set_xticklabels(list(map(lambda x: str(-x)+'$\degree W$',xticks)))
    else:
        if len(ax.shape) == 1:
            ax = np.array([ax])
        #Loop over axes
        for axis in ax.ravel():
            #Force spatial extent and draw features (coastlines, land, etc)
            
            LAND.plot(ax=axis, color='silver', lw=0, zorder=3)
            LAND.boundary.plot(ax=axis, color='k', lw=0.75, zorder=3)
            
            axis.set_extent(extent, crs=ccrs.PlateCarree())

            axis.scatter(loclons,loclats, color='gold', edgecolor='k',
                        zorder=3,s=20)
        
        #For the first plot name the plotted points   
        for i, txt in enumerate(locnames):
            ax.ravel()[0].annotate(txt, (loclons[i]+0.05,loclats[i]+0.05),
                                fontsize=9,
                                zorder=3)
        #Create colorbar(s) axis
        if colorbar == 'one':
            box1 = ax[0,-1].get_position()
            box2 = ax[-1,-1].get_position()
            cax = fig.add_axes([box2.xmax*1.05,box2.ymin,0.01,box1.ymax-box2.ymin])
        else:
            cax = None
        #Place tick labels
        for i in range(rows):
            ax[i,0].set_yticks(yticks)
            ax[i,0].set_yticklabels(list(map(lambda x: str(-x)+'$\degree S$',yticks)))
        for j in range(cols):
            ax[-1,j].set_xticks(xticks)
            ax[-1,j].set_xticklabels(list(map(lambda x: str(-x)+'$\degree W$',xticks)))
    return fig,ax,cax

def make_forecast_plot(var, cmap, cbar_label, vmin, vmax, figsize=MAPS_FIGSIZE,
                       level_step=0.25,fill=True,
                       **kwargs):
    fig,ax,cax = make_maps((2,5),figsize=figsize,
                            **kwargs)
    if fill:
        var = fill_borders(var)
    lon,lat = var.lon,var.lat
    lon2d,lat2d = np.meshgrid(lon,lat)
    for i,axis in enumerate(ax.ravel()):
        mapa = axis.contourf(lon2d,lat2d,var[i].values,
                            levels=np.arange(vmin,vmax+level_step,level_step),
                            norm=mcolors.Normalize(vmin,vmax),
                            cmap=cmap,
                            extend='both',
                            transform=ccrs.PlateCarree(),
                            zorder=0)
    cbar=fig.colorbar(mapa,cax=cax)
    cbar.set_label(label=cbar_label,
                   fontsize=18)
    cbar.ax.tick_params(labelsize=18)
    return fig,ax,cax,cbar


def create_timegrid(timestamp,nvars, figsize=(120,3)):
    fig = plt.figure(num=0,figsize=figsize)
    ax  = fig.add_subplot(111)
    
    x,y = timestamp,np.arange(0,nvars,1)
    grid = np.meshgrid(x,y)
    ax.xaxis.tick_top()
    fmt = lambda x,pos: mdates.DateFormatter(
        '%B\n%a\n%d\n%Hhr')(x,pos).capitalize()
    ax.xaxis.set_major_formatter(fmt)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))

    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%a\n%d\n%Hhr'))
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
    
    ax.invert_yaxis()
    ax.set_xlim(timestamp[0]-pd.Timedelta(minutes=30),
                timestamp[-1]+pd.Timedelta(minutes=30))
    ax.set_ylim(y.max()+0.5,y.min()-0.5)
    ax.set_yticks(y[::-1])
    ax.set_yticklabels([])
    
    # ax.grid(which='major',color='k')

    return fig,ax,grid

def build_row_matrix(timeseries,row,grid):
    X,Y    = grid
    mask   = np.zeros(X.shape, dtype=bool)
    mask[row,:] = True
    matrix = pd.DataFrame(np.empty(mask.shape))
    matrix.iloc[row,:] = timeseries
    matrix = matrix.where(mask)
    return matrix,mask

def plot_row_textcolor(data, grid, ax, text=True, colors=True):
    
    #Some safeties
    dtype=type(data['data'][0])
    row = data['row']
    if row>grid[0].shape[0]:
        raise ValueError('Row number must be less than the grix x dimension.')

    #build row matrix with data
    X,Y    = grid
    matrix,mask = build_row_matrix(data['data'],row,grid)
    
    #Modify plot
    if colors:
        if 'color_kwargs' in data.keys():
            kwargs=data['color_kwargs']
            ax.pcolormesh(X,Y,matrix,rasterized=True,edgecolor='w',
                            **kwargs)
        else:
            ax.pcolormesh(X,Y,matrix,rasterized=True,edgecolor='w')
    if text:
        for y in range(matrix.shape[1]):
            if 'fmt' in data.keys():
                ax.text((y+0.5)/matrix.shape[1],1-(row+0.5)/matrix.shape[0],
                        data['fmt'].format(matrix.iloc[row,y]),
                        fontsize=data['fontsize'],transform=ax.transAxes,
                        ha='center',va='center')
            else:
                ax.text((y+0.5)/matrix.shape[1],1-(row+0.5)/matrix.shape[0],
                        matrix.iloc[row,y],
                        fontsize=data['fontsize'],transform=ax.transAxes,
                        ha='center',va='center')                

    return 
        
def plot_row_arrows(data, grid, ax):
    #Some safeties
    dtype=type(data['data'][0])
    row = data['row']
    if row>grid[0].shape[0]:
        raise ValueError('Row number must be less than the grix x dimension.')
    #build row matrix with data
    X,Y    = grid
    angle = (90-data['data'])%360
    u,v = -np.cos(angle*np.pi/180),-np.sin(angle*np.pi/180)
    U,V = build_row_matrix(u,row,grid)[0],build_row_matrix(v,row,grid)[0]
    #Calculate arrow starting point (when rotating from midpoint)
    # off = u.map(lambda x: pd.Timedelta(hours=x))
    # off = np.tile(off.values,X.shape[0]).reshape(X.shape)
    
    X_tail = X
    Y_tail = Y
    ax.quiver(X_tail,Y_tail,U,V, scale=450, width=0.0002)
    
    return
    
def plot_logo(logo, position, fig, size):
    axis = fig.add_axes([position[0],position[1],size,size])
    axis.axis('off')
    axis.imshow(logo)
    return axis


def scale_bar(ax, length=None, location=(0.5, 0.05), linewidth=3):
    """
    ax is the axes to draw the scalebar on.
    length is the length of the scalebar in km.
    location is center of the scalebar in axis coordinates.
    (ie. 0.5 is the middle of the plot)
    linewidth is the thickness of the scalebar.
    """
    #Get the limits of the axis in lat long
    llx0, llx1, lly0, lly1 = ax.get_extent(ccrs.PlateCarree())
    #Make tmc horizontally centred on the middle of the map,
    #vertically at scale bar location
    sbllx = (llx1 + llx0) / 2
    sblly = lly0 + (lly1 - lly0) * location[1]
    tmc = ccrs.TransverseMercator(sbllx, sblly)
    #Get the extent of the plotted area in coordinates in metres
    x0, x1, y0, y1 = ax.get_extent(tmc)
    #Turn the specified scalebar location into coordinates in metres
    sbx = x0 + (x1 - x0) * location[0]
    sby = y0 + (y1 - y0) * location[1]

    #Calculate a scale bar length if none has been given
    #(Theres probably a more pythonic way of rounding the number but this works)
    if not length:
        length = (x1 - x0) / 5000 #in km
        ndim = int(np.floor(np.log10(length))) #number of digits in number
        length = round(length, -ndim) #round to 1sf
        #Returns numbers starting with the list
        def scale_number(x):
            if str(x)[0] in ['1', '2', '5']: return int(x)
            else: return scale_number(x - 10 ** ndim)
        length = scale_number(length)

    #Generate the x coordinate for the ends of the scalebar
    bar_xs = [sbx - length * 500, sbx + length * 500]
    #Plot the scalebar
    ax.plot(bar_xs, [sby, sby], transform=tmc, color='k', linewidth=linewidth)
    #Plot the scalebar label
    ax.text(sbx, sby, str(length) + ' km', transform=tmc,
            horizontalalignment='center', verticalalignment='bottom')
def scale_bar(ax, length=None, location=(0.5, 0.05), linewidth=3):
    """
    ax is the axes to draw the scalebar on.
    length is the length of the scalebar in km.
    location is center of the scalebar in axis coordinates.
    (ie. 0.5 is the middle of the plot)
    linewidth is the thickness of the scalebar.
    """
    #Get the limits of the axis in lat long
    llx0, llx1, lly0, lly1 = ax.get_extent(ccrs.PlateCarree())
    #Make tmc horizontally centred on the middle of the map,
    #vertically at scale bar location
    sbllx = (llx1 + llx0) / 2
    sblly = lly0 + (lly1 - lly0) * location[1]
    tmc = ccrs.TransverseMercator(sbllx, sblly)
    #Get the extent of the plotted area in coordinates in metres
    x0, x1, y0, y1 = ax.get_extent(tmc)
    #Turn the specified scalebar location into coordinates in metres
    sbx = x0 + (x1 - x0) * location[0]
    sby = y0 + (y1 - y0) * location[1]

    #Calculate a scale bar length if none has been given
    #(Theres probably a more pythonic way of rounding the number but this works)
    if not length:
        length = (x1 - x0) / 5000 #in km
        ndim = int(np.floor(np.log10(length))) #number of digits in number
        length = round(length, -ndim) #round to 1sf
        #Returns numbers starting with the list
        def scale_number(x):
            if str(x)[0] in ['1', '2', '5']: return int(x)
            else: return scale_number(x - 10 ** ndim)
        length = scale_number(length)

    #Generate the x coordinate for the ends of the scalebar
    bar_xs = [sbx - length * 500, sbx + length * 500]
    #Plot the scalebar
    ax.plot(bar_xs, [sby, sby], transform=tmc, color='k', linewidth=linewidth)
    #Plot the scalebar label
    ax.text(sbx, sby, str(length) + ' km', transform=tmc,
            horizontalalignment='center', verticalalignment='bottom')

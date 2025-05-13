import numpy as np
import os.path
import collections

import datetime
import fnmatch

import cartopy.crs as ccrs
import shapely.geometry as sgeom
from netCDF4 import num2date, date2num

# Set path for sample model data
SAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'sample_data')

# Set path for tracking output (this is the central repository)
TRACK_DIR = '/project/seasonal/hadjn/TRACK/TCTRACK_DATA_vn1.40/results/'
FEREDAY_DIR = '/project/seasonal/hadjn/fereday_vorticity/'


""" Store model storm observations as a named tuple (this enables access to data by its 
name instead of position index) """
Observation = collections.namedtuple('Observation', ['date', 'lat', 'lon', 'vort', 'vmax', 
                                                     'mslp', 'extras'])

class Observation(Observation):
    """  Represents a single observation of a model tropical storm. """
    
    def six_hourly_timestep(self):
        """ Returns True if a storm record is taken at 00, 06, 12 or 18Z only """
        return self.date.hour in (0,6,12,18) and self.date.minute == 0 and self.date.second == 0
    
    def add_to_axes(self, ax):
        """ Instructions on how to plot a model tropical storm observation """
        ax.plot(self.lon, self.lat)
        

class Storm(object):
    def __init__(self, snbr, obs, extras=None):
        """ Stores information about the model storm (such as its storm number) and corresponding 
        observations. Any additional information for a storm should be stored in extras as a dictionary. """
        self.snbr = snbr
        self.obs = obs
        
        # Create an empty dictionary if extras is undefined
        if extras is None:
            extras = {}
        self.extras = extras 

    @property
    def vmax(self):
        """ The maximum wind speed attained by the storm during its lifetime """
        return max(ob.vmax for ob in self.obs)
    
    @property
    def mslp_min(self):
        """ The minimum central pressure reached by the storm during its lifetime (set to 
        -999 if no records are available) """
        mslps = [ob.mslp for ob in self.obs if ob.mslp != 1e12]  
        mslps = list(filter(lambda ob: ob != -999.0,mslps))
        if not mslps:
            mslps = [-999]
        return min(mslps)
    
    @property
    def vort_max(self):
        """ The maximum 850 hPa relative vorticity attained by the storm during its lifetime """
        return max(ob.vort for ob in self.obs)
    
    def __len__(self):
        """ The total number of observations for the storm """
        return len(self.obs)
    
    def nrecords(self):
        """ The total number of records/observations for the storm """
        return len(self)
    
    def number_in_season(self):
        """ Returns storm number of the storm (the number of the storm for that year and ensemble
        member number) """
        return self.snbr    
    
    def lifetime(self,calendar='360_day'):
        """ The total length of time that the storm was active. This uses all observation
        points, no maximum wind speed threshold has been set """
        date1=min(ob.date for ob in self.obs)
        date2=max(ob.date for ob in self.obs)
        date1=date2num(date1,units='hours since 1970-01-01 00:00:00',calendar=calendar)
        date2=date2num(date2,units='hours since 1970-01-01 00:00:00',calendar=calendar)
        return date2-date1 
        
    def time_to_max(self,calendar='360_day'): 
        '''The length of time between the genesis and the maximum'''
        date1=self.genesis_date()
        date2=self.max_date()
        date1=date2num(date1,units='hours since 1970-01-01 00:00:00',calendar=calendar)
        date2=date2num(date2,units='hours since 1970-01-01 00:00:00',calendar=calendar)
        return date2-date1

    def step_of_min_mslp(self,calendar='360_day'):
        date1=self.genesis_date()
        date2=self.time_of_min_mslp()
        from netcdftime import utime
        cdftime = utime('hours since 0001-01-01 00:00:00')
        date1=cdftime.date2num(date1)#,units='hours since 1970-01-01 00:00:00',calendar=calendar)
        date2=cdftime.date2num(date2)#,units='hours since 1970-01-01 00:00:00',calendar=calendar)
        return int((date2-date1)/6)

    def step_of_max_vort(self,calendar='360_day'):
        date1=self.genesis_date()
        date2=self.time_of_max_vort()
        date1=date2num(date1,units='hours since 1970-01-01 00:00:00',calendar=calendar)
        date2=date2num(date2,units='hours since 1970-01-01 00:00:00',calendar=calendar)
        return (date2-date1)/6

    def time_of_min_mslp(self): 
        return self.obs_at_min_mslp().date

    def time_of_max_vort(self):
        return self.obs_at_max_vort().date 

    def max_date(self):
        """ The date of when the storm attains its maximum vorticity  """
        return self.obs_at_vmax().date 
        
    def genesis_date(self):
        """ The first observation date that a storm becomes active """
        #return min(ob.date for ob in self.obs)
        return self.obs_at_genesis().date
    
    def lysis_date(self):
        """ The final date that a storm was active """
        #return max(ob.date for ob in self.obs)
        return self.obs_at_lysis().date
    
    def ace_index(self):
        """ The accumulated cyclone energy index for the storm. Calculated as the square of the
        storms maximum wind speed every 6 hours (0, 6, 12, 18Z) throughout its lifetime. Observations
        of the storm taken in between these records are not currently used. Returns value rounded to
        2 decimal places. Wind speed units: knots """
        ace_index = 0
        for ob in self.obs:
            if ob.six_hourly_timestep():
                ace_index += np.square(ob.extras['vmax_kts'])/10000.
        return round(ace_index, 2)
    
    def obs_at_vmax(self):
        """Return the maximum observed vmax Observation instance. If there is more than one obs 
        at vmax then it returns the first instance """
        return max(self.obs, key=lambda ob: ob.vmax)
    
    def obs_at_min_mslp(self):
        """Return the maximum observed vmax Observation instance. If there is more than one obs 
        at vmax then it returns the first instance """
        return min(self.obs, key=lambda ob: ob.mslp)

    def obs_at_max_vort(self):
        """Return the maximum observed vmax Observation instance. If there is more than one obs 
        at vmax then it returns the first instance """
        return max(self.obs, key=lambda ob: ob.vort)

    def obs_at_genesis(self):
        """Returns the Observation instance for the first date that a storm becomes active """       
        for ob in self.obs:
            return ob
        else:
            raise ValueError('model storm was never born :-(')

    def obs_at_lysis(self):
        """Returns the Observation instance for the last date that a storm was active """    
        return [ob for ob in self.obs][-1]
    

def _boundary_segment(boundary, project=True):
    REGION_BOUNDARY = { 'west_midlat_na': ([-80, -68, -52, -62], [30, 43, 46, 60]),
                 'south_midlat_na': ([-80, -12], [30, 30]),
                       }
    rbox = sgeom.LineString(zip(*REGION_BOUNDARY.get(boundary)))
    if project: 
        rbox = ccrs.PlateCarree().project_geometry(rbox, ccrs.PlateCarree())
    return rbox

def _basin_polygon(basin, project=True):
    #: Lat/lon locations of tracking regions for each ocean basin
    TRACKING_REGION = {'na': ([-75, -20, -20, -80, -80, -100, -100, -75, -75], [0, 0, 60, 60, 40, 40, 20, 6, 0]),
                    'midlat_na': ([-80, -58, -52, -62, -49, -12, -12, -80], [30, 43, 46, 60, 60, 63, 30, 30]),
                    'midlat_np': ([136, 157, 165, -162, -136, -118, 136], [30, 50, 60, 60, 55, 30, 30]),
                    'gulf_stream': ([-90,-90,-50,-50,-90],[30, 48, 48, 30, 30]),
                    'gulf_stream_N': ([-90,-90,-50,-50,-90],[44, 54, 54, 44, 44]),
                       #'ep': ([-140, -75, -75, -100, -100, -120, -120, -140, -140], [0, 0, 6, 20, 40, 40, 60, 60, 0]),
                       'ep': ([-140, -75, -75, -100, -100, -140, -140], [0, 0, 6, 20, 30, 30, 0]),
                       #'wp': ([-260, -180, -180, -260, -260], [0, 0, 25, 25, 0]),
                       #'wp': ([-260, -180, -180, -260, -260], [0, 0, 60, 60, 0]),
                       'wp': ([100, 180, 180, 100, 100], [0, 0, 60, 60, 0]),    # corrected
                       #'ni': ([-320, -260, -260, -320, -320], [0, 0, 30, 30, 0]),
                       'ni': ([40, 100, 100, 40, 40], [0, 0, 30, 30, 0]),    # corrected
                       #'si': ([-330, -270, -270, -330, -330], [-40, -40, 0, 0, -40]),
                       'si': ([30, 90, 90, 30, 30], [-40, -40, 0, 0, -40]),    # corrected
                       #'au': ([-270, -200, -200, -270, -270], [-40, -40, 0, 0, -40]),
                       'au': ([90, 160, 160, 90, 90], [-40, -40, 0, 0, -40]),    # corrected
                       #'sp': ([-200, -120, -120, -200, -200], [-40, -40, 0, 0, -40]),
                       'sp': ([160, 240, 240, 160, 160], [-40, -40, 0, 0, -40]),    # corrected
                       'sa': ([-90, 0, 0, -90, -90], [-40, -40, 0, 0, -40]),
                       #'mdr': ([-80, -20, -20, -80, -80], [10, 10, 20, 20, 10])
                       'mdr': ([-60, -20, -20, -60, -60], [10, 10, 20, 20, 10])
                       }
    
    rbox = sgeom.Polygon(zip(*TRACKING_REGION.get(basin)))
    if project: 
        rbox = ccrs.PlateCarree().project_geometry(rbox, ccrs.PlateCarree())
    return rbox
    
def _obs_in_basin(storm, basin):
    """ Returns True if a storm track intersects a defined ocean basin """
    rbox = _basin_polygon(basin)
    list=[]
    for ob in storm.obs:
        lons, lats = zip(*[(ob.lon, ob.lat)])
        track = sgeom.Point(zip(lons, lats))     
        projected_track = ccrs.PlateCarree().project_geometry(track, ccrs.Geodetic())
        if rbox.intersection(projected_track):
            list.append(True)
        else:
            list.append(False)
    return list 
    
def _storm_motion(storm):
     fac=np.pi/180.
     speeds=_storm_speed(storm) 
     azimuth=_storm_azimuth(storm) 
     motion=[(v*np.cos(az*fac),v*np.sin(az*fac)) for (v,az) in zip(speeds,azimuth)]
     return motion

def _storm_speed(storm):
     nr=storm.nrecords()
     speeds = [] 
     positions = [(ob.lon, ob.lat) for ob in storm.obs]
     for i in range(0,nr-1):
         speeds.append(lon_lat_to_distance(positions[i],positions[i+1]))
         speeds=[np.abs(v)/(6.*3600.) for v in speeds]
         speeds.append(np.float('NaN'))
     return speeds

def _storm_azimuth(storm):
     nr=storm.nrecords()
     azimuth = []
     positions = [(ob.lon, ob.lat) for ob in storm.obs]
     for i in range(0,nr-1):
         azimuth.append(lon_lat_to_azimuth(positions[i],positions[i+1]))
         azimuth.append(np.float('NaN'))
     return azimuth

def _storm_cross_boundary(storm, boundary):
    """ Returns True if a storm intersects a region boundary """
    rbox = _boundary_segment(boundary)
    lons, lats = zip(*[(ob.lon, ob.lat) for ob in storm.obs])
    track = sgeom.LineString(zip(lons, lats))
    projected_track = ccrs.PlateCarree().project_geometry(track, ccrs.Geodetic())
    if rbox.intersects(projected_track):
        return True
    return False

def _storm_in_basin(storm, basin):
    """ Returns True if a storm track intersects a defined ocean basin """
    rbox = _basin_polygon(basin)   
    lons, lats = zip(*[(ob.lon, ob.lat) for ob in storm.obs]) 
    track = sgeom.LineString(zip(lons, lats))       
    projected_track = ccrs.PlateCarree().project_geometry(track, ccrs.Geodetic())
    if rbox.intersects(projected_track):
        return True
    return False

    
def _storm_vmax_in_basin(storm, basin):
    """ Returns True if the maximum intensity of the storm occurred
    in desired ocean basin. """
    rbox = _basin_polygon(basin)  
    xy = ccrs.PlateCarree().transform_point(storm.obs_at_vmax().lon, storm.obs_at_vmax().lat, ccrs.Geodetic())
    point = sgeom.Point(xy[0], xy[1])
    if point.within(rbox):
        return True
    return False

def _storm_genesis_in_basin(storm, basin):
    """ Returns True if the maximum intensity of the storm occurred
    in desired ocean basin. """
    rbox = _basin_polygon(basin)  
    xy = ccrs.PlateCarree().transform_point(storm.obs_at_genesis().lon, storm.obs_at_genesis().lat, ccrs.Geodetic())
    point = sgeom.Point(xy[0], xy[1])
    if point.within(rbox):
        return True
    return False
    
def _storms_in_basin_year_member_forecast(storms, basin, years, members, fcst_dates):
    """ 
    A generator which yields storms that occur within a desired ocean basin 
    with a particular start date, ensemble member number and forecast date 
    
    """
    for storm in storms:
        if (storm.genesis_date().year in years) and \
            (storm.extras['member'] in members) and \
            (storm.extras['fcst_start_date'] in fcst_dates) and \
            _storm_in_basin(storm, basin):
            yield storm  

def _storms_in_year_member_forecast(storms, years, members, fcst_dates):
    for storm in storms:
        if (storm.genesis_date().year in years) and \
            (storm.extras['member'] in members) and \
            (storm.extras['fcst_start_date'] in fcst_dates):
            yield storm
             
             
def _get_time_range(year, months):
    """ 
    Creates a start and end date (a datetime.date timestamp) for a 
    given year and a list of months. If the list of months overlaps into 
    the following year (for example [11,12,1,2,3,4]) then the end date 
    adds 1 to the original year 
    
    """
    start_date = datetime.datetime(year, months[0], 1)
    end_year = year
    end_month = months[-1]+1
    if months[-1]+1 < months[0] or months[-1]+1 == 13 or len(months) >= 12:
        end_year = year+1
    if months[-1]+1 == 13:
        end_month = 1
    end_date = datetime.datetime(end_year, end_month, 1)
    return start_date, end_date
                
        
def _storms_in_time_range(storms, year, months):
    """Returns a generator of storms that formed during the desired time period """
    start_date, end_date = _get_time_range(year, months)
    for storm in storms:        
        if (storm.genesis_date() >= start_date) and (storm.genesis_date() < end_date):
            yield storm
            
            
def _storms_in_basin_year_month_member_forecast(storms, basin, year, months, members, fcst_dates):
    """ 
    A generator which yields storms that occurred within a desired ocean basin 
    with a particular start date, start month, ensemble member number and forecast date 
    
    """
    for storm in _storms_in_time_range(storms, year, months):
        if (storm.extras['member'] in members) and \
           (storm.extras['fcst_start_date'] in fcst_dates) and \
            _storm_in_basin(storm, basin):
            yield storm
            
          
#def _tracking_file_exists(start_date, year, member, hemisphere):
#    """ 
#    Searches for a filename with a given forecast start date, year
#    and ensemble member number. Returns True if file is found.
#    
#    """
#    for root, dirs, files in os.walk(TRACK_DIR):
#        for file in files:
#            fname = os.path.join(root, file)
#            if os.path.isfile(fname):
#                if fnmatch.fnmatch(fname, 
#                                   '%sff_trs.vor_fullgrid_wind_mslp_L5.new.%s_%s_%s.%s.date' % 
#                                   (TRACK_DIR, str(year), start_date, member, hemisphere)
#                                   ):
#                    return True
             
def _tracking_file_exists(fcst_date, year, member, hemisphere, 
                          model='glosea5', file_type='tropical'):
    """ 
    Searches for a filename with a given forecast start date, year
    and ensemble member number. Returns True if file is found.
    
    """
    tracking_dir = TRACK_DIR + model
    
    for root, dirs, files in os.walk(tracking_dir):
        for file in files:
            fname = os.path.join(root, file)
            if os.path.isfile(fname):
                if fnmatch.fnmatch(fname, 
                    '%s/ff_trs.vor_fullgrid_wind_mslp_L5.new.%s.%s_%s_%s.%s.date' % 
                    (tracking_dir, file_type, str(year), fcst_date, 
                     member, hemisphere)):
                    return True

def ensemble_count(years, fcst_dates, members, hemisphere, file_type='tropical'):
    """ Returns number of individual tracking files available for a given 
    set of forecast dates, ensemble members and years """
    count  = 0
    for year in years:
        for fcst_date in fcst_dates:
            for member in members:
                if _tracking_file_exists(fcst_date, year, member, 
                                         hemisphere, file_type=file_type):
                    count += 1
    return count

'''
Function below do not work in python 3:

def lon_lat_to_distance(lon1,lat1,lon2,lat2):
    fac=np.pi/180.
    R = 6371.e3
    phi1 = lat1*fac
    phi2 = lat2*fac
    delta_phi = (lat2-lat1)*fac
    delta_lambda = (lon2-lon1)*fac
    a = np.sin(delta_phi/2.) * np.sin(delta_phi/2.) + np.cos(phi1) * np.cos(phi1) * np.sin(delta_lambda/2.) * np.sin(delta_lambda/2.) 
    c = 2. * np.arctan2(np.sqrt(a), np.sqrt(1-a));
    d = R * c;
    return d 

def lon_lat_to_azimuth(lon1,lat1,lon2,lat2):
    fac=np.pi/180.
    delta_lambda = (lon2-lon1)*fac
    phi1 = lat1*fac
    phi2 = lat2*fac
    x = np.sin(delta_lambda) * np.cos(phi2)
    y = np.cos(phi1) * np.sin(phi2) - (np.sin(phi1) * np.cos(phi2) * np.cos(delta_lambda))
    initial_bearing = np.arctan2(x, y)
    initial_bearing = np.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing
'''

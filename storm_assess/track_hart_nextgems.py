""" 
Load function to read TRACK-format output from TempestExtremes.

Notes:
    - All files should contain the DATES of the storms, not the 
      original timesteps, as output by TRACK.

    - The fields read are:
        * vmax (10m)
        * mslp
        * fields output by TempestExtremes
        * Hart CPS parameters
"""

import os.path, datetime
import storm_assess


# Load TRACK file
def load(fh, unstructured_grid = False, calendar=None):
    """
    N.B.
    This function assumes that added fields are, in order:
        MSLP, 10m wind speed, geopotential height, sst and precipitation flux.
    """

    # allow users to pass a filename instead of a file handle.
    if isinstance(fh, str):
        with open(fh,'r') as fh:
            fh_lines = fh.readlines()
                
#    else:
        # for each line in the file handle
        for line in fh_lines:
            if line.startswith('TRACK_NUM'):
                split_line = line.split()
                if split_line[2] == 'ADD_FLD':
                    number_fields = int(split_line[3])
                else:
                    raise ValueError('Unexpected line in TRACK output file.')
                # assume mslp,vmax,mslp,z(x4),sst,tp,TL,TU,B
                if number_fields == 8:
                    ex_cols = 0

    # create list of storm start line indices
    startline_idx = []

    # for each line in the file handle            
    for line in fh_lines:
        if line.startswith('TRACK_ID'):
            startline_idx.append(fh_lines.index(line))

    # read storms
    for idx in startline_idx:
        line = fh_lines[idx]
        # create a new observations list
        storm_obs = []
        # new storm: store the storm number
        try:
            _, snbr, _, _ = line.split()
        except:
            _, snbr = line.split()
        snbr =  int(snbr.strip())

        # get the number of observation records stored in the next line
        next_line = fh_lines[idx+1]
        if next_line.startswith('POINT_NUM'):
            _, n_records = next_line.split()
            n_records = int(n_records)
        else:
            raise ValueError('Unexpected line in TRACK output file.')

        # create a new observations list
        storm_lines = [fh_lines[idx+2+i] for i in range(n_records)]

        """ Read in the storm's observations """     
        # For each observation record            
        for obs_line in storm_lines:#zip(range(n_records), fh_lines):
            
            # get each observation element
            split_line = obs_line.strip().split('&')

            # get observation date, T63 lat & lon, and vort
            # (in case higher resolution data are not available)
            date, lon, lat, vort = split_line[0].split()
            
            if len(date) == 10: # i.e., YYYYMMDDHH
                if calendar == 'netcdftime':
                    yr = int(date[0:4])
                    mn = int(date[4:6])
                    dy = int(date[6:8])
                    hr = int(date[8:10])
                    date = netcdftime.datetime(yr, mn, dy, hour=hr)
                else:
                    date = datetime.datetime.strptime(date.strip(), '%Y%m%d%H')
            else:
                date = int(date)

            # get full resolution 850 hPa maximum vorticity (s-1)
            vort = float(vort)
            #vort = float(storm_centre_record[3])
            #vort = float(split_line[::-1][nlevels_T63+2+ex_cols])
            #vort_idx = (nlevels_T63+2)*3
            #vort = float(split_line[vort_idx])

            # get storm location of maximum vorticity (full resolution field)
            #lat = float(split_line[::-1][8+ex_cols])
            #lon = float(split_line[::-1][9+ex_cols])
            #storm_centre_record = split_line[0].split(' ')
            lat = float(lat)
            lon = float(lon)

            # if higher resolution lat/lon data is not available then use lat 
            # lon from T42 resolution data
            #if lat == 1e12 or lon == 1e12 or lat == 1.0e25 or lon == 1.0e25:
            #    lat = float(tmp_lat)
            #    lon = float(tmp_lon)

            # get T63 vorticity
            #T63_1 = float(split_line[1*3])
            #T63_2 = float(split_line[2*3])
            #T63_3 = float(split_line[3*3])
            #T63_4 = float(split_line[4*3])
            #T63_5 = float(split_line[5*3])
            #T63_6 = float(split_line[6*3])
            #T63_7 = float(split_line[7*3])
            #T63_diff = (T63_1 - T63_5)

            # get full resolution mslp
            mslp = float(split_line[1])
            if mslp > 1.0e4:
                mslp /= 100
            mslp = float(round(mslp,2))
            
            # get full resolution 925 hPa maximum wind speed (m/s)
            vmax = float(split_line[3])

            # check for mslp-vmax mix-up
            #if mslp < 500. and vmax > 500.:
            #    mslp,vmax = vmax,mslp

            # store vmax in knots (1 m/s = 1.944 kts) to match observations
            vmax_kts = vmax * 1.944

            # Fields added by TempExt
            zg250max = float(split_line[3])
            zg250min = float(split_line[4])
            zg500max = float(split_line[5])
            zg500min = float(split_line[6])
            sst = float(split_line[7])
            tp = float(split_line[8])

            # store observations
            # get 10m wind speed
            #v10m = float(split_line[::-1][4])
            #v10m_lat = float(split_line[::-1][5])
            #v10m_lon = float(split_line[::-1][6])

            # Hart parameters
            TL = float(split_line[9])
            TU = float(split_line[10])
            B = float(split_line[11])

            # store observations
            storm_obs.append(storm_assess.Observation(date, lat, lon, vort, vmax, mslp,
                extras={'vmax_kts':vmax_kts,'TL':TL,'TU':TU,'B':B}))
                
        # Yield storm
        yield storm_assess.Storm(snbr, storm_obs, extras={})


if __name__ == '__main__':
    #fname = os.path.join(SAMPLE_TRACK_DATA)
    #print 'Loading TRACK data from file:' , fname    
    #storms = list(load(fname, ex_cols=3, calendar='netcdftime'))
    #print 'Number of model storms: ', len(storms)
    
    ## Print storm details:
    #for storm in storms: 
    #    #print storm.snbr, storm.genesis_date()
    #    for ob in storm.obs:
    #        print ob.date, ob.lon, ob.lat, ob.vmax, ob.extras['vmax_kts'], ob.mslp, ob.vort
    #print 'Number of model storms: ', len(storms) 
    pass

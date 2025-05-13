
""" 
Load function to read IBTrACS.

"""
import os.path
import datetime
#import netcdftime
import storm_assess


def load(fh, calendar=None):

    # allow users to pass a filename instead of a file handle.
    if isinstance(fh,str):
        with open(fh,'r') as fh:
            fh_lines = fh.readlines()
#            for data in load(fh, calendar=calendar):
#                yield data

    # create list of storm start line indices
    startline_idx = []

    # for each line in the file handle            
    for line in fh_lines:
        if line.startswith('TRACK_NUM'):
            split_line = line.split()
            if split_line[2] == 'ADD_FLD':
                number_fields = int(split_line[3])
            else:
                raise ValueError('Unexpected line in TRACK output file.')
            break

    for line in fh_lines:
        if line.startswith('TRACK_ID'):
            # This is a new storm. Store the storm number.
            startline_idx.append(fh_lines.index(line))
            try:
                _, snbr, _, _ = line.split()
            except:
                _, snbr = line.split()
            snbr =  int(snbr.strip())

    for idx in startline_idx:
        # Now get the number of observation records stored in the next line                
        next_line = fh_lines[idx+1]
        if next_line.startswith('POINT_NUM'):
            _, n_records = next_line.split()
            n_records = int(n_records)
        else:
            raise ValueError('Unexpected line in TRACK output file.')
                    
        # Create a new observations list
        storm_obs = []
        
        """ Read in the storm's observations """     
        # For each observation record            
        for _, obs_line in zip(range(n_records), fh_lines[idx+2:idx+n_records]):
            
            # Get each observation element
            split_line = obs_line.strip().split('&')

            date, tmp_lon, tmp_lat, mslp = split_line[0].split()

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

            #storm_centre_record = split_line[0].split(' ')
            #lat = float(storm_centre_record[2])
            #lon = float(storm_centre_record[1])
            lat = float(tmp_lat)
            lon = float(tmp_lon)

            # Get full resolution mslp
            mslp = float(mslp)
            #if mslp == 0.0:
            #    mslp = None
            
            # Get maximum wind speed (m/s)
            # Also store vmax in knots (1 m/s = 1.944 kts) to match observations
            vmax = float(split_line[1])
            vmax_kts = vmax * 1.944
            #if vmax == -5143.925556:
            #    vmax = None
            #    vmax_kts = None
            
            # Get full resolution 850 hPa maximum vorticity (s-1)
            vort = None # dummy value

            # Store observations
            storm_obs.append(storm_assess.Observation(date, lat, lon, vort, vmax, mslp,
                extras={'vmax_kts':vmax_kts}))#,'v10m':v10m}))

        # Yield storm
        yield storm_assess.Storm(snbr, storm_obs, extras={})


if __name__ == '__main__':

    pass


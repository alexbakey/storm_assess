""" 
Load function to read in Reading Universities TRACK output. 
Should work for individual ensemble member files and also the 
'combine' file. 

Note: All files need to contain the DATES of the storms, not the 
original timestep as output by TRACK.

Note: Any fields in addition to the full field vorticity, mslp
and 925 hPa max winds (e.g. 10m winds or precipitation) are not 
currently stored. If you want these values you need to read in 
the data file and include the variables in the 'extras' dictionary. 


"""
import os.path
import datetime

import storm_assess

# Set path for sample model data
#SAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'sample_data')

#SAMPLE_TRACK_DATA = os.path.join(SAMPLE_DATA_PATH, 
#                                 'combined_ff_trs.vor_10m_fullgrid_N512_xgxqe_L5.new_20002011.date')


def load(fh, calendar=None):
    """
    ADAPTED TO READ PLV/KH TRACKs

    """
    # allow users to pass a filename instead of a file handle.
    if isinstance(fh,str):
        with open(fh,'r') as fh:
            fh_lines = fh.readlines()
#    if isinstance(fh, basestring):
#        with open(fh, 'r') as fh:
#            for data in load(fh, calendar=calendar):
#                yield data
                
#    else:

        for line in fh_lines:
            if line.startswith('TRACK_NUM'):
                split_line = line.split()
                if split_line[2] == 'ADD_FLD':
                    number_fields = int(split_line[3])
                else:
                    raise ValueError('Unexpected line in TRACK output file.')
        if number_fields == 7:
            ex_cols = 0

        # for each line in the file handle            
        startline_idx = []
        for line in fh_lines:
            if line.startswith('TRACK_ID'):    # new storm
                startline_idx.append(fh_lines.index(line))

        for idx in startline_idx: 
            # This is a new storm. Store the storm number.
            line = fh_lines[idx]
            try:
                _, snbr, _, _ = line.split()
            except:
                _, snbr = line.split()
            snbr =  int(snbr.strip())
                
            # Now get the number of observation records stored in the next line                
            #next_line = fh.next()
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
            #for _, obs_line in zip(range(n_records), fh_lines):
            for i in range(idx+2,idx+2+n_records):
                # Get each observation element
                obs_line = fh_lines[i]
                split_line = obs_line.strip().split('&')

                # Get observation date and T42 lat lon location in case higher 
                # resolution data are not available
                date, tmp_lon, tmp_lat, vort = split_line[0].split()
                
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

                # Get full resolution mslp
                mslp = float(split_line[::-1][4+ex_cols])
                #if mslp > 1.0e4:
                #    mslp /= 100
                #mslp = float(round(mslp,1))
                
                # Get full resolution 10m maximum wind speed (m/s)
                vmax = float(split_line[::-1][1])

                # Also store vmax in knots (1 m/s = 1.944 kts) to match observations
                vmax_kts = vmax * 1.944
                
                # Get storm location of maximum vorticity (full resolution field)
                storm_centre_record = split_line[0].split(' ')
                lat = float(storm_centre_record[2])
                lon = float(storm_centre_record[1])
                vort = float(vort)

 
                # Store observations
                storm_obs.append(storm_assess.Observation(date, lat, lon, vort, vmax, mslp,
                                 extras={'vmax_kts':vmax_kts}))#,'v10m':v10m}))
                
            # Yield storm
            yield storm_assess.Storm(snbr, storm_obs, extras={})


if __name__ == '__main__':
#    fname = os.path.join(SAMPLE_TRACK_DATA)
#    print 'Loading TRACK data from file:' , fname    
#    storms = list(load(fname, ex_cols=3, calendar='netcdftime'))
#    print 'Number of model storms: ', len(storms)
    
    # Print storm details:
#    for storm in storms: 
#        #print storm.snbr, storm.genesis_date()
#        for ob in storm.obs:
#            print ob.date, ob.lon, ob.lat, ob.vmax, ob.extras['vmax_kts'], ob.mslp, ob.vort
#    print 'Number of model storms: ', len(storms) 
    pass

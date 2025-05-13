
""" 
Load function to read in TempestExtremes (Ullrich et al., 2017, 2021) MCS nodefile output

"""
import os.path
import datetime
#import netcdftime
import storm_assess


def load(fh, unstructured_grid = False, calendar=None):
    """
    N.B.
    This function assumes that added fields are, in order:
        centlon, centlat, area.
    """

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
        if line.startswith('start'):    # new storm
            startline_idx.append(fh_lines.index(line))
#            else:
#                raise ValueError('Unexpected line in TempestExtremes output file.')

    for idx in startline_idx:
        # create a new observations list
        storm_obs = []

        snbr = idx                     # snbr not output by TempestExtremes

        start_line = fh_lines[idx]
        header = start_line.split()
        n_obs = int(header[1])         # number of timesteps
        start_yr = int(header[2])
        start_mon = int(header[3])
        start_day = int(header[4])
        start_hr = int(header[5])

        # read in storm's observations
        if unstructured_grid:
            for i in range(idx+1,idx+1+n_obs):
                s_line = fh_lines[i]    # storm line
                s_obs = s_line.split()  # storm's observations

                node = int(s_obs[0])
                lon, lat = float(s_obs[1]),float(s_obs[2])
                vort = None             # dummy value
                mslp = None
                vmax = None
                area = float(s_obs[4])
                yr, mon, day, hr = int(s_obs[5]),int(s_obs[6]),int(s_obs[7]),int(s_obs[8])
                timestamp = datetime.datetime(yr,mon,day,hr)

                # store observations
                storm_obs.append(storm_assess.Observation(timestamp, lat, lon, vort, vmax, mslp,
                    extras = {
                        'area':area}))

            # yield storm
            yield storm_assess.Storm(snbr, storm_obs, extras={})

        elif not unstructured_grid:
            for i in range(idx+1,idx+1+n_obs):
                s_line = fh_lines[i]    # storm line
                s_obs = s_line.split()  # storm's observations

                x, y = int(s_obs[0]),int(s_obs[1])
                lon, lat = float(s_obs[2]),float(s_obs[3])
                vort = None             # dummy value
                mslp = None
                vmax = None
                area = float(s_obs[4])
                yr, mon, day, hr = int(s_obs[5]),int(s_obs[6]),int(s_obs[7]),int(s_obs[8])
                timestamp = datetime.datetime(yr,mon,day,hr)

                # store observations
                storm_obs.append(storm_assess.Observation(timestamp, lat, lon, vort, vmax, mslp,
                    extras = {
                        'area':area}))

            # yield storm
            yield storm_assess.Storm(snbr, storm_obs, extras={})


if __name__ == '__main__':

    pass


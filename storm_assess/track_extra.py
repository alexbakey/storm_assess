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
import netcdftime
import storm_assess
import collections
SAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'sample_data')
SAMPLE_TRACK_DATA = os.path.join(SAMPLE_DATA_PATH, 'combined_ff_trs.vor_10m_fullgrid_N512_xgxqe_L5.new_20002011.date')
Observation_extra = collections.namedtuple('Observation_extra', ['date', 'value'])

class Observation_extra(Observation_extra):
    """  Represents a single observation of a model tropical storm. """

    def six_hourly_timestep(self):
        """ Returns True if a storm record is taken at 00, 06, 12 or 18Z only """
        return self.date.hour in (0, 6, 12, 18) and self.date.minute == 0 and self.date.second == 0

    def add_to_axes(self, ax):
        """ Instructions on how to plot a model tropical storm observation """
        ax.plot(self.lon, self.lat)

class Storm_extra(object):

    def __init__(self, snbr, obs):
        """ Stores information about the model storm (such as its storm number) and corresponding
        observations. Any additional information for a storm should be stored in extras as a dictionary. """
        self.snbr = snbr
        self.obs = obs

    def __len__(self):
        """ The total number of observations for the storm """
        return len(self.obs)

    def nrecords(self):
        """ The total number of records/observations for the storm """
        return len(self)

    def obs_at_genesis(self):
        """Returns the Observation instance for the first date that a storm becomes active """
        for ob in self.obs:
            return ob
        else:
            raise ValueError('model storm was never born :-(')

    def genesis_date(self):
        """ The first observation date that a storm becomes active """
        return self.obs_at_genesis().date


def write(storms, file_name, calendar = None):
    tr_count = len(storms)
    nff = 4
    number_fields = 4
    file_object = open(file_name, 'w')
    file_object.write('0 \n')
    file_object.write('0 0 \n')
    for i, storm in enumerate(storms):
        date = storm.genesis_date().strftime('%Y%m%d%I')
        trid = storm.snbr
        num = storm.nrecords()
        file_object.write('TRACK_ID {trid} START_TIME {date:10}\n'.format(trid=trid, date=date))
        file_object.write('POINT_NUM  {num}\n'.format(num=num))
        for step, ob in enumerate(storm.obs):
            date = ob.date.strftime('%Y%m%d%I')
            value = ob.value
            file_object.write('{date:10} {value} &\n'.format(date=date, value=value))

    file_object.close()

def load(fh, ex_cols = 0, calendar = None):
    """
    Reads model tropical storm tracking output from Reading Universities TRACK
    algorithm. Note: lat, lon, vorticity, maximum wind speed and minimum central
    pressure values are taken from the full resolution field, not T42. The lat/
    lon values correspond to the location of maximum 850 hPa relative vorticity
    (unless data are unavailable, in which case the original T42 resolution lat/
    lon values are used).

    If you have additional fields/columns after the full field vorticity, max
    wind and mslp data, then you need to count the number of columms these
    take up and set this as the ex_cols value (this value does not include
    &'s or comma's, just data). For example, for a file containing additional
    10m wind information ex_cols=3 (lat, lon, 10m wind speed value).

    Note: if you are using model data which uses a 12 months x 30 daycalendar
    then you need to set calendar to 'netcdftime'. Default it to use gregorian
    calendar.


    """
    if isinstance(fh, basestring):
        with open(fh, 'r') as fh:
            for data in load(fh, ex_cols=ex_cols, calendar=calendar):
                yield data

    else:
        for line in fh:
            if line.startswith('TRACK_NUM'):
                split_line = line.split()
                if split_line[2] == 'ADD_FLD':
                    number_fields = int(split_line[3])
                else:
                    raise ValueError('Unexpected line in TRACK output file.')
                nlevels_t63 = number_fields - 4
                if number_fields == 7 or number_fields == 9:
                    ex_cols = 3
                else:
                    print 'using ex_cols value ', ex_cols
            if line.startswith('TRACK_ID'):
                _, snbr, _, _ = line.split()
                snbr = int(snbr.strip())
                next_line = fh.next()
                if next_line.startswith('POINT_NUM'):
                    _, n_records = next_line.split()
                    n_records = int(n_records)
                else:
                    raise ValueError('Unexpected line in TRACK output file.')
                storm_obs = []
                for _, obs_line in zip(range(n_records), fh):
                    split_line = obs_line.strip().split('&')
                    date, extra_data = split_line[0].split()
                    storm_obs.append((date, extra_data))

                yield (snbr, storm_obs)

if __name__ == '__main__':
    fname = os.path.join(SAMPLE_TRACK_DATA)
    print 'Loading TRACK data from file:', fname
    storms = list(load(fname, ex_cols=3, calendar='netcdftime'))
    print 'Number of model storms: ', len(storms)
    for storm in storms:
        for ob in storm.obs:
            print ob.date, ob.lon, ob.lat, ob.vmax, ob.extras['vmax_kts'], ob.mslp, ob.vort

    print 'Number of model storms: ', len(storms)


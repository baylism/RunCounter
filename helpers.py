from datetime import datetime, timedelta
import re
from difflib import get_close_matches


def duration(timedelta):
    """
    Convert datetime object to dictionary of days, hours, minutes, seconds.

    Args:
        timedelta: A datetime.timedelta object

    Returns:
        A dict of  {'day': (float),
                    'hour': (float),
                    'minute': (float),
                    'second': (float)}.
    Raises:
        AttributeError: If timedelta is not datetime.timedelta object.

    """
    duration = {}
##    if type(timedelta) == 'datetime.timedelta':
##        duration['day'] = timedelta.days
##        minutes_temp, duration['second'] = divmod(timedelta.seconds, 60)
##        duration['hour'], duration['minute'] = divmod(minutes_temp, 60)
##    else:
##        for key in ['day', 'hour', 'minute', 'second']:
##            duration[key] = 0
    duration['day'] = timedelta.days
    minutes_temp, duration['second'] = divmod(timedelta.seconds, 60)
    duration['hour'], duration['minute'] = divmod(minutes_temp, 60)

    return duration

def say_duration(duration):
    """
    Return string representation of duration.

    Args:
        duration: a dict of    {'day': (float),
                                'hour': (float),
                                'minute': (float),
                                'second': (float)}.

    Returns:
            A string like '1 day, 2 hours, 34 minutes and 56 seconds'.

    """
    result = []
    for d in ['day', 'hour', 'minute', 'second']:
        if duration[d] == 1:
            result.append("{0} {1}".format(duration[d], d))
        if duration[d] > 1:
            result.append("{0} {1}s".format(duration[d], d))
    if result:
        if len(result) > 1:
            s = ', '.join(result[:-1])
            s += ' and '
            s += result[-1]
            return s
        else:
            return result[0]
    else:
        return '0 minutes'

def say_timedelta(timedelta):
    return say_duration(duration(timedelta))

def convert_times(value):
    """
    Returns tuple of datetime.datetime objects before/after time in ISO1806.

    Args:
        value: A string in ISO1806 format representing a time period.
            Currently supports the following subset of ISO1806:
                day - '2017-06-26'
                week - '2017-W01'
                month - '2015-12'
                year - '2015'

    Returns:
        A tuple of datatime.datetime objects. Sample input/output:
            '2017-06-26' => (2017-06-26 00:00:00, 2017-06-27 00:00:00)
            '2017-W01' => (2017-01-02 00:00:00, 2017-01-09 00:00:00)
            '2015-12' => (2015-12-01 00:00:00, 2016-01-01 00:00:00)
            '2015' => (2015-01-01 00:00:00, 2016-01-01 00:00:00)

    Raises:
        ValueError: If value string does not match a supported ISO1806 pattern.
        
    """
    day_patern = re.compile('\d{4}-\d{2}-\d{2}')
    week_pattern = re.compile('\d{4}-W\d{2}')
    month_pattern = re.compile('\d{4}-\d{2}')
    year_pattern = re.compile('\d{4}')

    if re.match(day_patern, value):
        date = datetime.strptime(value, '%Y-%m-%d')
        end = date + timedelta(days=1)
        return date, end
    elif re.match(week_pattern, value):
        date = datetime.strptime(value + '-1', '%Y-W%W-%w')
        end = date + timedelta(days=7)
        return date, end
    elif re.match(month_pattern, value):
        date = datetime.strptime(value, '%Y-%m')
        if date.month == 12:
            end = date.replace(year=date.year + 1, month=1)
        else:
            end = date.replace(month=date.month + 1)
        return date, end
    elif re.match(year_pattern, value):
        date = datetime.strptime(value, '%Y')
        end = date.replace(year=date.year + 1)
        return date, end
    else:
        raise ValueError('Date not recognised')

def match_activity(activity):
    """
    Returns best match from list of valid Strava activities.

    Note: returns a 'good enough' match that may or may not be the activity
        spoken by the user. For very similar terms ('run', 'Ran' vs 'Run') the
        it always returns a correct match. For strings that are not similar to
        one of the possiblities it might not.

        To tune behaviour, modify cutoff passed to get_close_matches(). 
    
    Args:
        activity: A string. For a match to be found this should be similar
            to a valid activity name (see posibilities list below). Exclude
            worse match by moving cutoff closer to 1. 

    Raises:
        IndexError: If no close match (match with a score >= cutoff) found. 
        
    """
    possibilities = [
        'Ride',
        'Kitesurf',
        'Run',
        'NordicSki',
        'Swim',
        'RockClimbing',
        'Hike',
        'RollerSki',
        'Walk',
        'Rowing',
        'AlpineSki',
        'Snowboard',
        'BackcountrySki',
        'Snowshoe',
        'Canoeing',
        'StairStepper',
        'Crossfit',
        'StandUpPaddling',
        'EBikeRide',
        'Surfing',
        'Elliptical',
        'VirtualRide',
        'IceSkate',
        'WeightTraining',
        'InlineSkate',
        'Windsurf',
        'Kayaking',
        'Workout',
        'Yoga'
        ]

    #activity is capitalised so close matches 'run' vs 'Run' are very likely
    #to work. 
    return get_close_matches(activity.capitalize(),
                             possibilities, n=1, cutoff=0.5)[0]


    

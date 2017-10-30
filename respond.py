from stravalib.client import Client, unithelper
from datetime import datetime, timedelta, date, timezone
import re
from difflib import get_close_matches
from functools import reduce

# Exceptions

ACTIVITY_NOUNS_PL = {'Ride': 'rides', 'Kitesurf': 'kitesurfs', 'Run': 'runs', 'NordicSki': 'skis', 'Swim': 'swims',
                  'RockClimbing': 'climbs', 'Hike': 'hikes', 'RollerSki': 'rollerskis', 'Walk': 'walks', 'Rowing': 'rows',
                  'AlpineSki': 'skis', 'Snowboard': 'snowboards', 'BackcountrySki': 'skis', 'Snowshoe': 'showshoes',
                  'Canoeing': 'canoes', 'StairStepper': 'steppers', 'Crossfit': 'crossfits', 'StandUpPaddling': 'paddles',
                  'EBikeRide': 'e-bike rides', 'Surfing': 'surfs', 'Elliptical': 'ellipticals', 'VirtualRide': 'virtual rides',
                  'IceSkate': 'ice skates', 'WeightTraining': 'weight training sessions', 'InlineSkate': 'inline skates', 'Windsurf': 'windsurfs',
                  'Kayaking': 'kayaks', 'Workout': 'workouts', 'Yoga': 'yoga sessions'}


class SlotError(Exception):
    pass


class DialogNotFinishedError(Exception):
    pass

# ------------- class -------------


class Response:
    """
    Create, update and build a response for the Alexa Skill service

    Attributes:
        event: Alexa request in JSON format.

    """
    def __init__(self, event=None):
        if event:
            self.card_title = event['request']['intent']['name']
        else:
            self.card_title = None

        self.session_attributes = {}
        self.speech_type = 'PlainText'
        self.speech_output = None
        self.reprompt_text = None
        self.should_end_session = True
        self.directives = []
        self.card_type = 'Simple'

    def build_response(self):
        """
        Return response in JSON format

        Response adheres to the response format from JSON Interface Reference
        for Custom Skills v1.0, available at
        <https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/
        docs/alexa-skills-kit-interface-reference#response-body-syntax>

        """
        if self.speech_type == 'SSML':
            output_speech = {'type': self.speech_type, 'ssml': self.speech_output}
        if self.speech_type == 'PlainText':
            output_speech = {'type': self.speech_type, 'text': self.speech_output}

        return {
            'version': '1.0',
            'sessionAttributes': self.session_attributes,
            'response': {
                'outputSpeech': output_speech,
                'card': {
                    'type': self.card_type,
                    'title': self.card_title,
                    'content': self.speech_output
                    },
                'reprompt': {
                    'outputSpeech': {
                        'type': 'PlainText',
                        'text': self.reprompt_text
                        }
                    },
                'shouldEndSession': self.should_end_session
                }
            }

    def build_directive(self):
        """
        Return response in JSON format

        Response adheres to the response format from JSON Interface Reference
        for Custom Skills v1.0, available at
        <https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/
        docs/alexa-skills-kit-interface-reference#response-body-syntax>

        """
        return {
            'version': '1.0',
            'sessionAttributes': self.session_attributes,
            'response': {
                'card': {
                    'type': 'Simple',
                    'title': self.card_title,
                    'content': 'Returning dialog directive'
                    },

                'shouldEndSession': False,
                'directives': self.directives
                }
            }


class StravaResponse(Response):
    """
    Base class with methods for accessing and retrieving data from Strava API
    """
    def __init__(self, event):
        super(StravaResponse, self).__init__(event)
        self.event = event
        self.client = Client(access_token=event['session']['user']['accessToken'])
        self.activities = None
        self.stats = None
        self.friend_activities = None
        self.followers = None

    def retrieve_activities(self, before=datetime.now(), after=None, limit=None):
        self.activities = self.client.get_activities(before=before,
                                                     limit=limit,
                                                     after=after)

    def retrieve_stats(self):
        self.stats = self.client.get_athlete_stats()

    def retrieve_friend_activities(self, limit=10):
        self.friend_activities = self.client.get_friend_activities(limit)

    def retrieve_followers(self):
        self.followers = self.client.get_athlete_followers()

    def get_latest_activity(self, activity_type=None):
        if activity_type:
            return next(filter(lambda x: x.type == activity_type, self.activities))
        else:
            return next(self.activities)

    def get_week_activities(self, activity_type=None):
        today = datetime.now(timezone.utc)
        last_monday = today.replace(hour=0, minute=0) - timedelta(days=today.weekday())

        if activity_type:
            def date_and_type(activity):
                return activity.start_date > last_monday and activity.type == activity_type
            return filter(date_and_type, self.friend_activities)
        else:
            return filter(lambda x: x.start_date > last_monday, self.friend_activities)

    def get_stats(self, activity_type=None):
        if activity_type == 'Ride':
            return self.stats.all_ride_totals
        else:
            return self.stats.all_run_totals



    def calculate_distance(self, activities, activity_type=None, athlete_id=None):
        """
        Return total distance of activity_type activities.

        Args:
            activities: An iterator of Activity objects.
            activity_type: StravaLib activity.type. 'Run', 'Row' etc.
            athlete_id: Strava athlete id

        Returns:
            distance: float.
        """
        if activity_type:
            activities = filter(lambda x: x.type == activity_type, activities)

        if athlete_id:
            activities = filter(lambda x: x.athlete.id == athlete_id, activities)

        distance = 0
        for a in activities:
            distance += round(float(unithelper.miles(a.distance)), 2)
        return distance

    def calculate_time(self, activities, activity_type=None):
        """
        Return total time of activity_type activities.

        Args:
            activities: An iterator of Activity objects.
            activity_type: StravaLib activity.type. 'Run', 'Row' etc.

        Returns:
            time: datetime.timedelta object.
        """
        if activity_type:
            activities = filter(lambda x: x.type == activity_type, activities)
        activities = map(lambda x: x.elapsed_time, activities)
        return reduce(lambda x, y: x + y, activities, timedelta(0))

    def calculate_count(self, activities, activity_type=None):
        """
        Return total number of activity_type activities.

        Args:
            activities: An iterator of Activity objects.
            activity_type: StravaLib activity.type. 'Run', 'Row' etc.
        Returns:
            count: int.
        """
        if activity_type:
            activities = filter(lambda x: x.type == activity_type, activities)
        return sum(1 for activity in activities)

    def duration(self, timedelta):
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
        duration['day'] = timedelta.days
        minutes_temp, duration['second'] = divmod(timedelta.seconds, 60)
        duration['hour'], duration['minute'] = divmod(minutes_temp, 60)

        return duration

    def say_duration(self, duration):
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

    def say_timedelta(self, timedelta):
        return self.say_duration(self.duration(timedelta))

    def convert_distance(self, distance):
        return float(unithelper.miles(distance))

    def summarise_activities(self, activities):
        unique_activities = list(set([activity.type for activity in activities]))

        totals = []
        for t in unique_activities:
            distance = self.calculate_distance(activities, activity_type=t)
            time = self.calculate_time(activities, activity_type=t)
            count = self.calculate_count(activities, t)

            if count == 1:
                name = t
            else:
                name = ACTIVITY_NOUNS_PL[t]

            totals.append('{0} {1}, with a total distance of {2:.0f} miles and a total time of {3}'.format(
                count,
                name,
                self.convert_distance(distance),
                self.say_timedelta(time)
            ))

        return ' and '.join(totals)


class StravaSlotResponse(StravaResponse):
    def __init__(self, event):
        super(StravaSlotResponse, self).__init__(event)
        self.activity_type = None
        self.period_start = None
        self.period_end = None
        self.period_type = None

    def check_dialog(self):
        dialog_status = self.event['request']['dialogState']
        if dialog_status != 'COMPLETED':
            self.directives.append({"type": "Dialog.Delegate"})
            print('DIALOG STATUS: ', dialog_status)
            print('SENDING DIRECTIVE: ', self.directives)
            raise DialogNotFinishedError

    def validate_activity(self):
        """
        Validate the activity slot and set activity_type for the response.

        Raises:
            SlotError if there is a problem and the response needs to be returned.
        """
        # Get slot resolved by Alexa during dialog
        try:
            self.activity_type = self.event['request']['intent']['slots']['Activity']['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['id']

        # If slot doesn't resolve as expected, check for unresolved slot then make a best guess or fail
        except KeyError:
            try:
                activity_slot = self.event['request']['intent']['slots']['Activity']['value']
            except KeyError:
                self.speech_output = "Sorry, I didn't hear that activity."
                self.should_end_session = True
                raise SlotError

            try:
                self.activity_type = self.match_activity(activity_slot)
            except (IndexError, KeyError, AttributeError):
                self.speech_output = "Hmm, I didn't understand that activity. "
                self.should_end_session = True
                raise SlotError

    def match_activity(self, activity):
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
            'Activity',  # Not a valid activity, used here to denote 'all activities'
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

        # activity is capitalised so close matches 'run' vs 'Run' are very likely
        # to succeed.
        return get_close_matches(activity.capitalize(),
                                 possibilities, n=1, cutoff=0.5)[0]

    def validate_time(self):
        """
        Validate the date slot and set period_start and period_end for the response.

        Raises:
            SlotError if there is a problem and the response needs to be returned.

        """
        # Get time slot
        try:
            date_slot = self.event['request']['intent']['slots']['Date']['value']
        except KeyError:
            self.speech_output = "Please specify a time period like 'last week' or 'on 27th June 2017'."
            raise SlotError

        # Convert date string to datetime.datetime objects
        try:
            self.period_type, self.period_start, self.period_end = self.convert_times(date_slot)
        except ValueError:
            self.speech_output = "Sorry, I didn't understand that date."
            raise SlotError

        # Convert convert future months to same month in previous year
        now = datetime.now()
        # if self.period_type == 'month':
        if self.period_start > now:
            self.period_end = self.period_end.replace(year=self.period_end.year - 1)
            self.period_start = self.period_start.replace(year=self.period_start.year - 1)

        # Ensure other time periods do not end in future
        elif self.period_end > now:
            self.period_end = now

        # Raise an error if time period starts in future
        if self.period_start > now:
            self.speech_output = "I can't check future dates."
            raise SlotError

    def convert_times(self, value):
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
            return 'day', date, end

        elif re.match(week_pattern, value):
            date = datetime.strptime(value + '-1', '%Y-W%W-%w')
            end = date + timedelta(days=7)
            return 'week', date, end

        elif re.match(month_pattern, value):
            date = datetime.strptime(value, '%Y-%m')
            if date.month == 12:
                end = date.replace(year=date.year + 1, month=1)
            else:
                end = date.replace(month=date.month + 1)
            return 'month', date, end

        elif re.match(year_pattern, value):
            date = datetime.strptime(value, '%Y')
            end = date.replace(year=date.year + 1)
            return 'year', date, end

        else:
            raise ValueError('Date not recognised')

    def say_time_slot(self):
        date = self.period_start.strftime('%Y%m%d')
        if self.period_type == 'day':
            return '<say-as interpret-as="date">????{}</say-as>'.format(date[4:])
        elif self.period_type == 'week':
            return 'the week beginning <say-as interpret-as="date">????{}</say-as>'.format(date[4:])
        elif self.period_type == 'month':
            return'<say-as interpret-as="date">{}??</say-as>'.format(date[:6])
        elif self.period_type == 'year':
            return'<say-as interpret-as="date">{}????</say-as>'.format(date[:4])


# ------------- decorator -------------


def build_full_response(session_attributes, card_title, speech_output, reprompt_text, should_end_session):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response':{
            'outputSpeech': {
                'type': 'PlainText',
                'text': speech_output
                },
            'card': {
                'type': 'Simple',
                'title': "SessionSpeechlet - " + card_title,
                'content': "SessionSpeechlet - " + speech_output
                },
            'reprompt': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': reprompt_text
                    }
                },
            'shouldEndSession': should_end_session
            }
        }


def respond(card_title, reprompt_text=None, should_end_session=True):   
    def decorator(request_handler):    
        def decorated(intent, session):          
            speech_output, session_attributes = request_handler(intent, session)   
            return build_full_response(session_attributes,
                                  card_title,
                                  speech_output,
                                  reprompt_text,
                                  should_end_session)
        return decorated
    return decorator


# ------------- Alexa tutorial -------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

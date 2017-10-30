# TODO remove unnecessary reprompts. Possibly convert to helps.
# TODO

from stravalib.client import unithelper

from respond import Response, SlotError, StravaSlotResponse, DialogNotFinishedError
from helpers import duration, say_duration
from datetime import datetime, timedelta, date
import time

ACTIVITY_VERBS = {'Ride': 'rode', 'Kitesurf': 'kitesurfed', 'Run': 'ran', 'NordicSki': 'went', 'Swim': 'swam',
                  'RockClimbing': 'went', 'Hike': 'hiked', 'RollerSki': 'went', 'Walk': 'walked', 'Rowing': 'rowed',
                  'AlpineSki': 'skied', 'Snowboard': 'went', 'BackcountrySki': 'skied', 'Snowshoe': 'went',
                  'Canoeing': 'canoed', 'StairStepper': 'went', 'Crossfit': 'went', 'StandUpPaddling': 'paddled',
                  'EBikeRide': 'rode', 'Surfing': 'surfed', 'Elliptical': 'went', 'VirtualRide': 'rode',
                  'IceSkate': 'skated', 'WeightTraining': 'went', 'InlineSkate': 'skated', 'Windsurf': 'windsurfed',
                  'Kayaking': 'kayaked', 'Workout': 'went', 'Yoga': 'went'}

ACTIVITY_NOUNS_PL = {None: 'activities', 'Ride': 'rides', 'Kitesurf': 'kitesurfs', 'Run': 'runs', 'NordicSki': 'skis', 'Swim': 'swims',
                     'RockClimbing': 'climbs', 'Hike': 'hikes', 'RollerSki': 'rollerskis', 'Walk': 'walks', 'Rowing': 'rows',
                     'AlpineSki': 'skis', 'Snowboard': 'snowboards', 'BackcountrySki': 'skis', 'Snowshoe': 'showshoes',
                     'Canoeing': 'canoes', 'StairStepper': 'steppers', 'Crossfit': 'crossfits', 'StandUpPaddling': 'paddles',
                     'EBikeRide': 'e-bike rides', 'Surfing': 'surfs', 'Elliptical': 'ellipticals', 'VirtualRide': 'virtual rides',
                     'IceSkate': 'ice skates', 'WeightTraining': 'weight training sessions', 'InlineSkate': 'inline skates', 'Windsurf': 'windsurfs',
                     'Kayaking': 'kayaks', 'Workout': 'workouts', 'Yoga': 'yoga sessions'}


# Session handling


def welcome_linked():
    """
    Return welcome message for linked account.
    
    Returns:
        Response in JSON format.
        
    """
    response = Response()
    response.card_title = "Welcome to Running Info"
    response.speech_output = ("Welcome to Running Info. Thank you for linking your account. "
                              "To get information on your last run, say "
                              "Tell me about my last run")
    response.reprompt_text = "To hear about your last run, say Tell me about my last run"
    response.should_end_session = False

    return response.build_response()


def welcome_request_link():
    """
    Return welcome message requesting that use links their account.

    Returns:
        Response in JSON format.
        
    """
    response = Response()
    response.card_title = "Link Account"
    response.card_type = 'LinkAccount'
    response.speech_output = ("Welcome to Running Info. To use this skill, "
                              "please link your account in the Alexa app.")

    return response.build_response()


def request_link():
    """
    Return a message requesting that use links their account.

    Returns:
        Response in JSON format.

    """
    response = Response()
    response.card_title = "Link Account"
    response.card_type = 'LinkAccount'
    response.speech_output = ("Before I can answer that I need to connect to your Strava account. "
                              "Please look for the account linking card in your Alexa App.")

    return response.build_response()


def handle_session_end_request():
    """
    Return message informing user of session end.

    Returns:
        Response in JSON format.
        
    """
    response = Response()
    response.card_title = "Session Ended"
    response.speech_output = "Thank you for using Running Info " 

    return response.build_response()


# Summaries


def latest_activity(event, all_activities=False):
    """
    Return total distance of activities in period specified.

    Args:
        event: a request from the Alexa service
            Slots contain:
            -'['Date']['value']' (str) - time in ISO1806 format.
            -(Optional) '['Activity']['value']' (str) - the type of activity
                requested in a format in or close to a StravaLib activity.type.
            session contains:
            -session['user']['accessToken'] with Strava API access token
            from OAuth account linking.

        all_activities: Force report over all ativities in user's time period.
            Ignores empty or useless Intent['slots']['Activity']['value'] from Alexa.
            Defaults to False.

    Returns:
        Response in JSON format.

    """
    try:
        response = StravaSlotResponse(event)
    except KeyError:
        return request_link()

    # print(event)

    if all_activities:
        response.activity_type = None
    else:
        # Complete dialog
        try:
            response.check_dialog()
        except DialogNotFinishedError:
            print('returning response')
            return response.build_directive()

        # Validate activity slot
        try:
            response.validate_activity()
        except SlotError:
            response.activity_type = None

    response.retrieve_activities(limit=200)

    try:
        activity = response.get_latest_activity(response.activity_type)
    except StopIteration:
        response.speech_output = "I can't find any activities of that type."
        response.should_end_session = True
        return response.build_response()

    def say_activity_summary(activity):
        """
        Return activity summary text to be spoken by alexa.

        Args:
            activity: A stravalib Activity object with .elapsed_time.

        Returns:
            A string to be spoken by Alexa.

        """
        elapsed_time = activity.elapsed_time
        distance_float = float(unithelper.miles(activity.distance))
        mile_pace = elapsed_time / distance_float

        return ("Your last {0.type}, {0.name}, was {1:.2f} miles. "
                "It took {2} at an average pace of {3} per mile.").format(
            activity,
            distance_float,
            say_duration(duration(elapsed_time)),
            say_duration(duration(mile_pace)))

    response.speech_output = say_activity_summary(activity)
    response.card_title = "Latest {}".format(activity.type)
    return response.build_response()


def stats(event):
    """
    Return the user's all-time stats.

    Args:
        event: an alexa skill service request. Session portion of Alexa
            request contains session['user']['accessToken'] with Strava API access token
            from OAuth account linking.
        
    Returns:
        Response in JSON format.
        
    """
    try:
        response = StravaSlotResponse(event)
    except KeyError:
        return request_link()

    # Validate activity slot or default to 'Run'
    try:
        response.validate_activity()
    except SlotError:
        response.activity_type = 'Run'

    # Limit activity_type to ride and run
    if response.activity_type not in ('Ride', 'Run'):
        response.speech_output = 'Sorry, I only know all time stats' \
                                 ' for running and cycling'
        return response.build_response()

    response.retrieve_stats()

    def say_stats(activity_totals):
        """
        Return text to be spoken by Alexa.

        Args:
            activity_totals: stats object returned by get_athlete_stats()
                method in Stravalib.

        Returns:
            A string representation of the stats.
        """
        return ("Here are your all-time stats: "
               "Distance: {0:.0f} miles. "
               "Total time: {1}. "
               "Moving time: {2}. "
               "Elevation gain: {3:.0f} feet.").format(
                   response.convert_distance(activity_totals.distance),
                   response.say_timedelta(activity_totals.elapsed_time),
                   response.say_timedelta(activity_totals.moving_time),
                   float(unithelper.feet(activity_totals.elevation_gain)))

    response.speech_output = say_stats(response.get_stats(response.activity_type))
    response.card_title = "All Time Stats"
    return response.build_response()


def weekly_report(event):

    try:
        response = StravaSlotResponse(event)
    except KeyError:
        return request_link()

    response.card_title = 'Weekly summary'

    today = date.today()
    last_monday = today - timedelta(days=today.weekday())
    last_monday_datetime = datetime(last_monday.year, last_monday.month, last_monday.day)

    response.retrieve_activities(after=last_monday_datetime)

    if all(False for _ in response.activities):
        response.speech_output = 'You haven\'t done any activities yet this week.'
        return response.build_response()

    def summarise_activities(activities):
        unique_activities = list(set([activity.type for activity in activities]))

        totals = []
        for t in unique_activities:
            distance = response.calculate_distance(activities, activity_type=t)
            time = response.calculate_time(activities, activity_type=t)
            count = response.calculate_count(activities, t)

            if count == 1:
                name = t
            else:
                name = ACTIVITY_NOUNS_PL[t]

            totals.append('{0} {1}, with a total distance of {2:.0f} miles and a total time of {3}'.format(
                count,
                name,
                response.convert_distance(distance),
                response.say_timedelta(time)
            ))

        return ' and '.join(totals)

    def say_weekly_report(activities):
        return 'This week, you have done {}'.format(summarise_activities(activities))

    response.speech_output = say_weekly_report(response.activities)
    return response.build_response()


def weekly_friend_report(event, mutual=False):
    try:
        response = StravaSlotResponse(event)
    except KeyError:
        return request_link()

    # Validate activity slot or default to 'None' if no type specified or failed to resolve/match
    try:
        response.validate_activity()
    except SlotError:
        print('slot error')
        response.activity_type = None

    # Limit activity_type to ride and run
    if response.activity_type not in (None, 'Ride', 'Run'):
        response.speech_output = 'Sorry, I can only compare, runs, cycles or activities.'
        return response.build_response()

    def filter_mutual(activities):
        response.retrieve_followers()
        follower_ids = map(lambda x: x.id, response.followers)
        return filter(lambda x: x.athlete.id in follower_ids, activities)

    def leaderboard_distance(activities):
        leaderboard = {}
        client_id = response.client.get_athlete().id
        for activity in activities:
            friend_id = activity.athlete.id
            if friend_id != client_id:
                if friend_id not in leaderboard:
                    leaderboard[friend_id] = {}
                    leaderboard[friend_id]['distance'] = round(float(unithelper.miles(activity.distance)), 2)
                    leaderboard[friend_id]['name'] = activity.athlete.firstname
                else:
                    leaderboard[friend_id]['distance'] += round(float(unithelper.miles(activity.distance)), 2)

        return leaderboard

    def summarise_athletes(leaderboard):
        top_three = sorted(leaderboard, key=lambda x: leaderboard[x]['distance'], reverse=True)[:4]
        print(top_three)

        report = []
        for friend in top_three:
            report.append('{0}, at {1:.2f} miles'.format(leaderboard[friend]['name'], leaderboard[friend]['distance']))

        if len(report) > 1:
            s = ', '.join(report[:-1])
            s += ', and '
            s += report[-1]
            return s
        else:
            return report[0]

    def say_top_friend_report(activities):
        leaderboard = leaderboard_distance(activities)
        summary = summarise_athletes(leaderboard)
        activity_name = response.activity_type if response.activity_type else 'total'

        if mutual is True:
            return 'Your top followers by {} distance this week are: {}'.format(activity_name, summary)
        else:
            return 'Your top friends by {} distance this week are: {}'.format(activity_name, summary)

    response.retrieve_friend_activities(limit=300)
    week_activities = response.get_week_activities(response.activity_type)

    if mutual:
        week_activities = filter_mutual(week_activities)

    try:
        response.speech_output = say_top_friend_report(week_activities)
    except IndexError:
        if mutual is True:
            response.speech_output = 'Your followers haven\'t done any {} this week.'.format(ACTIVITY_NOUNS_PL[response.activity_type])
        else:
            response.speech_output = 'Your friends haven\'t done any {} this week.'.format(ACTIVITY_NOUNS_PL[response.activity_type])

    response.card_title = 'Top friends by distance'
    return response.build_response()


# Specific requests


def report_distance(event, all_activities=False):
    """
    Return total distance of activities in period specified.

    Args:
        event: a request from the Alexa service
            Slots contain:
            -'['Date']['value']' (str) - time in ISO1806 format.
            -(Optional) '['Activity']['value']' (str) - the type of activity
                requested in a format in or close to a StravaLib activity.type.          
            session contains:
            -session['user']['accessToken'] with Strava API access token
            from OAuth account linking.
            
        all_activities: Force report over all ativities in user's time period.
            Ignores empty or useless Intent['slots']['Activity']['value'] from Alexa.
            Defaults to False. 
                   
    Returns:
        Response in JSON format.
        
    """
    try:
        response = StravaSlotResponse(event)
    except KeyError:
        return request_link()

    # Ensure dialogue has finished
    try:
        response.check_dialog()
    except DialogNotFinishedError:
        print('returning response')
        return response.build_directive()

    # Validate time period
    try:
        response.validate_time()
    except SlotError:
        return response.build_response()

    # Validate activity
    if all_activities:
        response.activity_type = None
    else:
        try:
            response.validate_activity()
        except SlotError:
            return response.build_response()

    response.retrieve_activities(before=response.period_end,
                                 after=response.period_start)

    distance = response.calculate_distance(response.activities,
                                           activity_type=response.activity_type)

    def say_distance_report(distance, activity_type=None):
        """
        Return report text to be spoken by Alexa.

        Args:
            distance: total distance in miles (float)
            activity_type: Run, Row etc

        Returns:
            String representation of report. 
            
        """
        if activity_type:
            return "You {0} {1:.2f} miles".format(ACTIVITY_VERBS[activity_type],
                                                   distance)
        else:
            return "Your total distance is {.2f} miles".format(distance)

    response.speech_type = 'SSML'
    if response.period_type == 'day':
        response.speech_output = '<speak> {} on {} </speak>'.format(say_distance_report(distance, response.activity_type),
                                                                    response.say_time_slot())
    else:
        response.speech_output = '<speak> {} in {} </speak>'.format(say_distance_report(distance, response.activity_type),
                                                                    response.say_time_slot())
    response.card_title = "Distance Report"
    return response.build_response()


def report_time(event, all_activities=False):
    """
    Return total time, time or number of activities in period specified.

    Args:
        event: a request from the Alexa service
            Slots contain:
            -'['Date']['value']' (str) - time in ISO1806 format.
            -(Optional) '['Activity']['value']' (str) - the type of activity
                requested in a format in or close to a StravaLib activity.type.          
            session contains:
            -session['user']['accessToken'] with Strava API access token
            from OAuth account linking.
            
        all_activities: Force report over all ativities in user's time period.
            Ignores empty or useless Intent['slots']['Activity']['value'] from Alexa.
            Defaults to False. 
                   
    Returns:
        Response in JSON format.
        
    """
    try:
        response = StravaSlotResponse(event)
    except KeyError:
        return request_link()

    # Check dialogue
    try:
        response.check_dialog()
    except DialogNotFinishedError:
        print('returning response')
        return response.build_directive()

    # Validate time period
    try:
        response.validate_time()
    except SlotError:
        return response.build_response()

    # Validate activity
    if all_activities:
        response.activity_type = None
    else:
        try:
            response.validate_activity()
        except SlotError:
            return response.build_response()

    response.retrieve_activities(before=response.period_end,
                                 after=response.period_start)
    time = response.calculate_time(response.activities,
                                   activity_type=response.activity_type)
          
    def say_time_report(time, activity_type=None):
        """
        Return report text to be spoken by Alexa.

        Args:
            time: total time as datetime.timeperiod object
            activity_type: activity_type Run, Row etc

        Returns:
            String representation of report. 
            
        """
        if activity_type:
            return "You {0} for {1}.".format(ACTIVITY_VERBS[activity_type],
                                             say_duration(
                                                 duration(
                                                     time)))
        else:
            return "Your total time is {.2f} miles.".format(say_duration(duration(time)))

    response.speech_type = 'SSML'
    if response.period_type == 'day':
        response.speech_output = '<speak> {} on {} </speak>'.format(say_time_report(time, response.activity_type),
                                                                    response.say_time_slot())
    else:
        response.speech_output = '<speak> {} in {} </speak>'.format(say_time_report(time, response.activity_type),
                                                                    response.say_time_slot())
    response.card_title = "Time Report"
    return response.build_response()


def report_count(event, all_activities=False):
    """
    Return total time, time or number of activities in period specified.

    Args:
        event: a request from the Alexa service
            Slots contain:
            -'['Date']['value']' (str) - time in ISO1806 format.
            -(Optional) '['Activity']['value']' (str) - the type of activity
                requested in a format in or close to a StravaLib activity.type.          
            session contains:
            -session['user']['accessToken'] with Strava API access token
            from OAuth account linking.
            
        all_activities: Force report over all ativities in user's time period.
            Ignores empty or useless Intent['slots']['Activity']['value'] from Alexa.
            Defaults to False. 
                   
    Returns:
        Response in JSON format.
        
    """
    try:
        response = StravaSlotResponse(event)
    except KeyError:
        return request_link()

    # Check dialogue
    try:
        response.check_dialog()
    except DialogNotFinishedError:
        print('returning response')
        return response.build_directive()

    # Validate time period
    try:
        response.validate_time()
    except SlotError:
        return response.build_response()

    # Validate activity
    if all_activities:
        response.activity_type = None
    else:
        try:
            response.validate_activity()
        except SlotError:
            return response.build_response()

    response.retrieve_activities(before=response.period_end,
                                 after=response.period_start)
    count = response.calculate_count(response.activities,
                                     activity_type=response.activity_type)

    def say_count_report(count, activity_type=None):
        """
        Return report text to be spoken by Alexa.

        Args:
            count: number of time activity completed (int)
            activity_type: activity_type Run, Row etc

        Returns:
            String representation of report. 
            
        """
        if activity_type:
            if count == 1:
                return "You {0} once".format(ACTIVITY_VERBS[activity_type], count)
            elif count == 2:
                return "You {0} twice".format(ACTIVITY_VERBS[activity_type], count)
            else:
                return "You {0} {1} times".format(ACTIVITY_VERBS[activity_type], count)
        else:
            if count == 1:
                return "You completed {0} activity.".format(count)
            else:
                return "You completed {0} activities.".format(count)

    response.speech_type = 'SSML'
    if response.period_type == 'day':
        response.speech_output = '<speak> {} on {} </speak>'.format(
            say_count_report(count, response.activity_type),
            response.say_time_slot())
    else:
        response.speech_output = '<speak> {} in {} </speak>'.format(
            say_count_report(count, response.activity_type),
            response.say_time_slot())

    response.card_title = "Activity Count Report"
    return response.build_response()

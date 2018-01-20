import request


# --------------- Intent handler ------------------


def on_intent(event):
    """ Called when the user specifies an intent request for this skill """

    print("INTENT HANDLER RECEIVED received intent ID " + event['request']['requestId'] +
          "NAME = " + event['request']['intent']['name'] +
          ", sessionId= " + event['session']['sessionId'])

    intent_name = event['request']['intent']['name']
    print(event)

    # Dispatch to your skill's intent handlers
    if intent_name == "LatestAllActivitiesIntent":
        return request.latest_activity(event, all_activities=True)
    elif intent_name == 'LatestActivityIntent':
        return request.latest_activity(event)
    elif intent_name == "ActivityStatsIntent":
        return request.stats(event)
    elif intent_name == "DistanceReportIntent":
        return request.report_distance(event)
    elif intent_name == "TimeReportIntent":
        return request.report_time(event)
    elif intent_name == "CountReportIntent":
        return request.report_count(event)
    elif intent_name == "AllActivityCountIntent":
        return request.report_count(event, all_activities=True)
    elif intent_name == "WeeklyReportIntent":
        return request.weekly_report(event)
    elif intent_name == "FriendReportIntent":
        return request.weekly_friend_report(event)
    elif intent_name == "MutualFriendReportIntent":
        return request.weekly_friend_report(event, mutual=True)
    elif intent_name == "AMAZON.HelpIntent":
        return request.welcome_request_link()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return request.handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


# --------------- Session events ------------------

def on_session_started(event):
    """ Called when the session starts
    Print session info to logs
    """

    print("SESSION STARTED, requestId=" + event['request']['requestId']
          + ", sessionId=" + event['session']['sessionId'])


def on_launch(event):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + event['request']['requestId'] +
          ", sessionId=" + event['session']['sessionId'])

    if 'accessToken' in event['session']['user']:
        return request.welcome_linked()
    else:
        return request.welcome_request_link()


def on_session_ended(event):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("SESSION ENDED, requestId=" + event['request']['requestId'] +
          ", sessionId=" + event['session']['sessionId'])



# --------------- Main handler ------------------


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("LAMBDA HANDLER RECEIVED:  " + event['request']['type'] + " applicationID = " +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    if (event['session']['application']['applicationId'] !=
            ""):
        raise ValueError("Invalid Application ID")

    # Print session start to logs
    if event['session']['new']:
        on_session_started(event)

    # Handle request events
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event)
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event)
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event)

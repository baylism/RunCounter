# Run Counter

## Overview
An Alexa skill to access activity information through the Strava API. Developed and tested on AWS Lambda.

## Features
`response.py` defines classes for creating Alexa responses and for accessing the Strava API. Valid requests are passed by a handler in `lambda_function.py` to one of 10 request types defined in `request.py`.

These are:

#### latest activity, run or ride

‘Ask Run Counter for my latest run’

#### stats, running stats or cycling stats

‘Give my my stats’ ‘Ask Run Counter for my cycling stats’

#### how far/for how long/how many times the user did any Strava activity type in a day, week, month or year.

‘How far did I row in July?’ ‘For how long did I run last year?’ 
‘How many times have I cycled this month?’

#### the user's friend (people they follow) report, friend running report or friend cycling report

‘Ask Run Counter for my friend report’
‘Ask Run Counter for my friend running report’

#### the user's follower (people they follow, and who follow them) report, running report or cycling report

‘Ask Run Counter for my follower report’
‘Ask Run Counter for my follower running report’

See the intent schema for a more comprehensive list of possible queries.

## Implementation
The skill has been developed and tested using AWS Lambda.

OAuth authentication for the Strava API is handled by Alexa Skills Service. 

Note: A dialog directive is used to resolve slot values for certain requests. This isn't yet supported by the Alexa testing interface. 

## Dependencies
[stravalib](https://github.com/hozn/stravalib)


# coding: utf-8

# In[1]:

#!/usr/bin/python3

import time
import re
import requests

def message_matches(user_id, message_text):
    '''
    Check if the username and the word 'bot' appears in the text
    '''
    regex_expression = '.*@' + user_id + '.*bot.*'
    regex = re.compile(regex_expression)
    # Check if the message text matches the regex above
    match = regex.match(message_text)
    # returns true if the match is not None (ie the regex had a match)
    return match != None 


# In[2]:

def extract_name(message_text):
    '''
    Extract the name. The regex relies on the question having a specific form
    '''
    regex_expression = 'Show me articles on (.+)'
    regex= re.compile(regex_expression)
    matches = regex.finditer(message_text)

    for match in matches:
        return match.group(1)
    # if there were no matches, return None
    return None


# In[3]:

import MySQLdb as mdb
import sys

con = mdb.connect(host = 'localhost', 
                  user = 'root', 
                  passwd = 'dwdstudent2015', 
                  charset='utf8', use_unicode=True);

cur = con.cursor(mdb.cursors.DictCursor)
cur.execute("SELECT * FROM NYTimes2.Articles_Constant")
rows = cur.fetchall()



# In[8]:

def getData(topic):
    
    data = rows
    result = [ {"Title": row["title"], "Description": row["Description"],"Entity": row["entity"], "URL": row["url"], "Sentiment": row["sentiment_type"],
               "Shares": row["Shares"]} 
             for row in rows if topic.lower() in row["title"].lower() or topic.lower() in row["entity"].lower() or topic.lower() in row["Description"].lower()
             ]
    return result



# In[5]:

def create_message(username, topic):
    '''
    This function takes as input the username of the user that asked the question,
    and the station_name that we managed to extract from the question (potentially it can be None)
    We check the Citibike API and respond with the status of the Citibike stations.
    '''
    if topic != None:
        # We want to address the user with the username. Potentially, we can also check
        # if the user has added a first and last name, and use these instead of the username
        message = "Thank you @{u} for abusing me. Here is a list of relevant articles on {s}. You will be charged a $5 fee. Please check your bank account now.\n\n".format(u=username, s=topic)

        # Let's get the data from the Citibike API
        matching = getData(topic)
        # If we cannot find any matching station
        if len(matching) == 0:
            message += "I could not find anything on that topic.\n"

#       Add the information for each station
        for articles in matching:
            Title = articles['Title']
            Description = articles['Description']
            About = articles['Entity']
            Link = articles['URL']
            senti = articles['Sentiment']
            numShares = articles['Shares']
            message += "Title: {a}. \n Description: {f}.\n Entity: {b}.\n Link: {c}\n Article Sentiment: {d}\n Shares: {e}\n\n".format(a=Title, f=Description, b=About, c=Link, d=senti, e=numShares)
    else:
        message =  "Thank you @{u} for asking.".format(u=username)
        message += "Unfortunately no else cares about it.\n"
        message += "Ask me `Show me articles on ___.` and I will try to answer."
        
    return message


# In[6]:

import json

secrets_file = 'slack_secret.json'
f = open(secrets_file, 'r') 
content = f.read()
f.close()

auth_info = json.loads(content)
auth_token = auth_info["access_token"]
bot_user_id = auth_info["user_id"]

from slackclient import SlackClient
sc = SlackClient(auth_token)


# In[ ]:

# Connect to the Real Time Messaging API of Slack and process the events

if sc.rtm_connect():
    # We are going to be polling the Slack API for recent events continuously
    while True:
        # We are going to wait 1 second between monitoring attempts
        time.sleep(1)
        # If there are any new events, we will get a response. If there are no events, the response will be empty
        response = sc.rtm_read()
        for item in response:
            # Check that the event is a message. If not, ignore and proceed to the next event.
            if item.get("type") != 'message':
                continue
                
            # Check that the message comes from a user. If not, ignore and proceed to the next event.
            if item.get("user") == None:
                continue
            
            # Check that the message is asking the bot to do something. If not, ignore and proceed to the next event.
            message_text = item.get('text')
            if not message_matches(bot_user_id, message_text):
                continue
                
            # Get the username of the user who asked the question
            response = sc.api_call("users.info", user=item["user"])
            username = response['user'].get('name')
            
            # Extract the station name from the user's message
            topic = extract_name(message_text)

            # Prepare the message that we will send back to the user
            message = create_message(username, topic)

            # Post a response to the #bots channel
            sc.api_call("chat.postMessage", channel="#bots", text=message)


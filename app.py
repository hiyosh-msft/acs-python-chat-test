from flask import Flask, render_template, redirect, session, jsonify
from flask import request

from datetime import datetime, timedelta
import requests
import json
import csv

from azure.communication.chat import ChatClient, CommunicationTokenCredential, ChatMessageType, ChatParticipant, ChatMessageType
from azure.communication.identity import CommunicationIdentityClient, CommunicationUserIdentifier

app = Flask(__name__)

#ACS Endpoint
endpoint = ''
#Function App Endpoint for Token 
tokenendpoint = ''
#Function Key for Token Endpoint
functionkey = ''

#Landing Page
@app.route('/')
def index():
    return render_template('index.html')

#Set your Identity for the session.
#Token will be requested from a Function App that will return info as {"id": "8:acs:xxxx", "token": "<value>"}
@app.route('/set-identity', methods=['GET', 'POST'])
def setidentity():
    try:
        if request.method == 'GET':
            return render_template('set-identity.html')
        
        elif request.method == 'POST':

            if 'new_user' == request.form.get('user_type'):
                res = requests.get(tokenendpoint + functionkey)
                jsoned_res = res.json()

                #Keep a record of User Ids in CSV
                with open('./userids.csv','a') as fd:
                    fd.write(jsoned_res['id'] + ', \n')
        
            elif 'returning_user' == request.form.get('user_type'):
                userid = request.form.get('user_id')
                res = requests.get(tokenendpoint + functionkey + '&' + 'id=' + userid)
                jsoned_res = res.json()
        
            session['userid'] = jsoned_res['id']
            session['token'] = jsoned_res['token']

    except Exception as ex:
        print(ex)
        return 'Error encountered while retrieving token. Please try again.'
    
    return jsonify(jsoned_res)

#Create a new thread
@app.route('/create-thread', methods=['GET', 'POST'])
def createthread():
    if request.method == 'GET':
        return render_template('create-thread.html', userid=session['userid'], token=session['token'])
    
    elif request.method == 'POST':
        topic = request.form.get('topic')
        chat_client = ChatClient(endpoint, CommunicationTokenCredential(session['token']))
        chat_thread_result = chat_client.create_chat_thread(topic)

    return chat_thread_result.chat_thread.id

#Lists all messages in Chat Thread
@app.route('/list-chats', methods=['GET', 'POST'])
def listchats():
    if request.method == 'GET':
        return render_template('list-chats.html',  userid=session['userid'], token=session['token'])

    elif request.method == 'POST':
        thread_id = request.form.get('thread_id')
        chat_client = ChatClient(endpoint, CommunicationTokenCredential(session['token']))
        chat_thread_client = chat_client.get_chat_thread_client(thread_id)

    chat_messages = chat_thread_client.list_messages()

    return render_template('list-chats.html', thread_id=thread_id, chat_messages=chat_messages, userid=session['userid'], token=session['token'])

#Lists all chat threads
@app.route('/list-threads')
def listthreads():
    chat_client = ChatClient(endpoint, CommunicationTokenCredential(session['token']))
    chat_threads = chat_client.list_chat_threads()

    return  render_template('list-threads.html', chat_threads=chat_threads, userid=session['userid'], token=session['token'])

#Send chat message
#If HTTP Method is GET, return chat form
#If HTTP Method is POST, add the posted message to chat thread 
@app.route('/send-chat', methods=['GET', 'POST'])
def sendchat():
    if request.method == 'GET':
        return render_template('send-chat.html', userid=session['userid'], token=session['token'])

    elif request.method == 'POST': 
        thread_id = request.form.get('thread_id')
        display_name = request.form.get('display_name')
        content = request.form.get('content')

        #Form cannot be empty
        if thread_id is None or display_name is None or content is None:
            return render_template('send-chat.html', error='Fields cannot be empty', userid=session['userid'], token=session['token'])

        chat_client = ChatClient(endpoint, CommunicationTokenCredential(session['token']))
        chat_thread_client = chat_client.get_chat_thread_client(thread_id)
        send_message_result_w_enum = chat_thread_client.send_message(content=content, sender_display_name=display_name, chat_message_type=ChatMessageType.TEXT)

    return redirect('list-chats?thread_id='+thread_id)

#Adds a user
@app.route('/add-user', methods=['GET', 'POST'])
def adduser():
    if request.method == 'GET':
        return render_template('add-user.html',  userid=session['userid'], token=session['token'])

    elif request.method == 'POST':
        participantid = request.form.get('user_id')
        displayname = request.form.get('display_name')
        thread_id = request.form.get('thread_id')
        
        participants = [] 
        chat_thread_participant = ChatParticipant(
        identifier= CommunicationUserIdentifier(participantid),
        display_name=displayname,
        share_history_time=datetime.utcnow()
        )

        participants.append(chat_thread_participant)

        chat_client = ChatClient(endpoint, CommunicationTokenCredential(session['token']))
        chat_thread_client = chat_client.get_chat_thread_client(thread_id)

        chat_thread_client.add_participants(participants)

    return redirect('list-users?thread_id='+ thread_id)

#List all users in a thread
#Can optionally pass 'thread_id' parameter
@app.route('/list-users', methods=['GET', 'POST'])
def listusers():
    thread_id = request.args.get('thread_id')

    if request.method == 'GET' and thread_id is None:
        return render_template('list-users.html', userid=session['userid'], token=session['token'])
    
    elif request.method == 'POST':
        thread_id = request.form.get('thread_id')

    chat_client = ChatClient(endpoint, CommunicationTokenCredential(session['token']))
    chat_thread_client = chat_client.get_chat_thread_client(thread_id)

    chat_thread_participants = chat_thread_client.list_participants()

    serialized = []

    for user in chat_thread_participants:
        print(vars(user))
        print(vars(user.identifier))
        print(user.identifier.raw_id)

        #Extract Participant Info(ID, DisplayName) from ChatParticipant Object
        tmptuple = (user.identifier.raw_id, user.display_name)
        serialized.append(tmptuple)

    return render_template('list-users.html', participants=serialized, thread_id=thread_id, userid=session['userid'], token=session['token'])

#Run app
if __name__ == '__main__':
    #This session key is for testing purposes only.
    app.secret_key = 'xyz'
    app.run(debug=True)
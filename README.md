# acs-python-chat-test

This was made to be a very simple test for ACS Chat SDK python with Flask. You can run it by executing
```
python app.py
```

It also requires you to have an ACS Identity Provider. I suggest using Function App with HTTP Trigger.

Make sure to provide values for the following in app.py.
```python
#ACS Endpoint
endpoint = 'https://<acs-name>.communication.azure.com/'
#Function App Endpoint for Token 
tokenendpoint = 'https://<functionapp-name>.azurewebsite.net/api/<function-name>?code='
#Function Key for Token Endpoint
functionkey = '<functionkey>'
```
This code assumes your Identity Provider will return identity information as the following JSON.

```json
{
    "id":"8:acs:xxxx",
    "token": "<token_value>"
}
```
You can refer to this document for creating an Identity Provider.  
<br>
Quickstart: Create and manage access tokens 
<br>
https://docs.microsoft.com/en-us/azure/communication-services/quickstarts/access-tokens?pivots=programming-language-python


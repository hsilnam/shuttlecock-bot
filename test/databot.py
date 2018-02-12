import requests
import websocket
import json

res = 'world'

def on_message(ws, message):
	message = json.loads(message)
	print(message)
	if 'type' in message.keys() and message['type'] != 'message':
		return
	if 'hello' in message['text']:
		return_msg = {
			'channel' : message['channel'],
			'type' : 'message',
			'text' : res
		}
		ws.send(json.dumps(return_msg))
token = 'xoxb-313489507538-uLtHZlilNtnD7jn1X75NACxy'
get_url = requests.get('https://slack.com/api/rtm.connect?token=' + token)
print(get_url.json()['url'])
socket_endpoint = get_url.json()['url']
print('Connecting to', socket_endpoint)
websocket.enableTrace(True)
ws = websocket.WebSocketApp(socket_endpoint, on_message=on_message)
ws.run_forever()

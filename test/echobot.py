import requests
import websocket
import json

def on_message(ws, message):
	message = json.loads(message)
	if 'type' not in message.keys() or message['type'] != 'message':
		return
		# 전달 받은 메세지가 텍스트가 아닐 경우가 뭐가있지
	return_msg = {
		'channel' : message['channel'],
		'type': 'message',
		'text': message['text']
	}
	ws.send(json.dumps(return_msg))

token = 'xoxb-313489507538-uLtHZlilNtnD7jn1X75NACxy'
get_url = requests.get('https://slack.com/api/rtm.connect?token=' + token)
socket_endpoint = get_url.json()['url']


websocket.enableTrace(True)
ws = websocket.WebSocketApp(socket_endpoint, on_message=on_message)
ws.run_forever()

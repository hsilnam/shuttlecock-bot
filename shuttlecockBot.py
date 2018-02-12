import requests
import websocket
import json
import random
import datetime, time

msgs = None
message_text = ""

with open('busInfo.json', 'r') as fr:
	msgs = json.loads(fr.read())
def on_message(ws, message):
	message = json.loads(message)
	print(message)
	if 'type' in message.keys() and message['type'] != 'message':
		return
	message_text = message['text']
	if not message_text in msgs['kwds']:
		return
	weekday = get_key_by_weekday(msgs['info']['semester'])
	if message_text == '셔틀콕':
		return_msg = {
			'channel' : message['channel'],
			'type': 'message',
			'text': msgs['notice']
		}
	
	elif message_text == '셔틀콕 시간표':
		locations = get_bus_schedule(weekday)
		return_msg = show_bus_schedule(message, locations)
	else:
		location = get_key_by_location(message_text,weekday)
		current_bus_time = get_bus_and_time(location)
		return_msg = show_current_bus_time(message, current_bus_time)

	ws.send(json.dumps(return_msg))

#평일,토,일에 따른 value return
def get_key_by_weekday(term):
	weekday = datetime.date.today().weekday()
	if weekday == '5':
		return term['weekends']['sat']
	elif weekday == '6':
		return term['weekends']['sun']
	else:
		return term['weekday']

#입력한 장소에 따른 value return
def get_key_by_location(message_text, weekday):
	if message_text == '셔틀콕 예술인':
		return weekday['예술인']
	elif message_text == '셔틀콕 셔틀콕':
		return weekday['셔틀콕']
	elif message_text == '셔틀콕 한대앞':
		return weekday['한대앞']
	else:
		return weekday['창의원']

#제일 빨리 오는 버스 시간을 알려주는 문자열 return
def get_bus_and_time(buses):
	now = datetime.datetime.now().strftime("%H:%M")
	# now = '13:09'#test
	plus = ''
	result = ''
	for bus in buses:
		for time in buses[bus]:
			if now <= time:
				plus = bus + '\n' + time
				break
		result = result + '\n' + plus
	print(result)
	return result
#slack에 보낼 제일 빨리 오는 버스 시간 값 return
def show_current_bus_time(message, current_bus_time):
	return_msg = {
			'channel' : message['channel'],
			'type': 'message',
			'text': '<버스 시간>' + current_bus_time
		}
	return return_msg

#전체 버스 시간표의 문자열 return
def get_bus_schedule(locations):
	now = datetime.datetime.now().strftime("%H:%M")
	# now = '13:09'#test
	plus = ''
	result = ''
	for location in locations:
		result = result + '*' + location + '*' + '\n' 
		buses = locations[location]
		for bus in buses:
			result = result + bus + '\n'
			for time in buses[bus]:
				result = result + time + ' '
			result = result + '\n'
	return result	

#slack에 보낼 전체 버스 시간표 값 return
def show_bus_schedule(message,get_bus_schedule):
	return_msg = {
			'channel' : message['channel'],
			'type': 'message',
			'text': '<버스 시간>\n' + get_bus_schedule
		}
	return return_msg

token = 'xoxb-313489507538-uLtHZlilNtnD7jn1X75NACxy'
get_url = requests.get('https://slack.com/api/rtm.connect?token=' + token)
print(get_url.json()['url'])
socket_endpoint = get_url.json()['url']
print('Connecting to', socket_endpoint)

websocket.enableTrace(True)
ws = websocket.WebSocketApp(socket_endpoint, on_message=on_message)
ws.run_forever()

#chang-uiwon circulating-bus shuttlecock handaeap-bus yesul-in-bus
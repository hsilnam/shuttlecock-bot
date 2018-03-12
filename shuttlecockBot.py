import requests
import websocket
import json
import random
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time
import os

msgs = None
save_log = ''
busalarmtimedict = None
real_alarm_time_now = False
_message=None
_ws=None
_channel=''

with open('ShuttleCokeBot/busInfo.json', 'r', encoding='utf-8') as fr:
	msgs = json.loads(fr.read())
def on_message(ws, message):
	global save_log
	global busalarmtimedict
	global _message
	global _ws
	global _channel

	_ws = ws
	_message = json.loads(message)
	#입력한 값의 key에 type이 있는지, 그 타입이 message type이 message인지 안전코딩
	if 'type' in _message.keys() and _message['type'] != 'message':
		return
	message_text = _message['text']
	#입력된 값이 키워드에 있는지 안전코딩
	if not (message_text in msgs['shuttlekwds'] or message_text in msgs['alarmkwds']):
		return
	weekday = get_key_by_weekday(msgs['info']['semester'])
	#shuttlekwds에 있는 키워드
	if message_text in msgs['shuttlekwds']:
		if message_text == '셔틀콕' or message_text == '셔틀콕?':
			return_msg = {
				'channel' : _message['channel'],
				'type': 'message',
				'text': msgs['shuttlenotice']
			}
		
		elif message_text == '셔틀콕 시간표':
			locations = get_bus_schedule(weekday)
			return_msg = show_bus_schedule(locations)
		else:
			location = get_key_by_location(message_text,weekday)
			current_bus_time = get_bus_and_time(location)
			save_log = message_text
			return_msg = show_current_bus_time(current_bus_time)
	else:
		if message_text == '알람?':
			return_msg = {
				'channel' : _message['channel'],
				'type': 'message',
				'text': msgs['alarmnotice']
			}
		else:			
			if save_log == '':
				return_msg = {
					'channel' : _message['channel'],
					'type': 'message',
					'text': msgs['alarmwarning']
				}
			else:
				#전 busalarmtimedic
				busalarmtimedictbefore = busalarmtimedict
				busalarmtimedict = get_bus_alarm_time_dict(save_log, message_text, weekday)

				if(difference_from_now_and_alarm_time() == None):
					return_msg = {
					'channel' : _message['channel'],
					'type': 'message',
					'text': '알람완료'
					}
					_channel=_message['channel']
					_ws.send(json.dumps(return_msg))
					return

				time_difference=int(difference_from_now_and_alarm_time())
				time_remaining= 5 - time_difference
				if (0< time_difference & time_difference <= 5):
					return_msg = {
					'channel' : _message['channel'],
					'type': 'message',
					'text': busalarmtimedict['bus']+'가 '+str(time_remaining)+'분 밖에 안남았습니다'
					}
					busalarmtimedict = busalarmtimedictbefore
					_ws.send(json.dumps(return_msg))
					return
				else:
					return_msg = {
					'channel' : _message['channel'],
					'type': 'message',
					'text': '알람완료'
					}
					_channel=_message['channel']
					_ws.send(json.dumps(return_msg))
					return

				

	_ws.send(json.dumps(return_msg))

#평일,토,일에 따른 value return
def get_key_by_weekday(term):
	weekday = datetime.date.today().weekday()
	if weekday == 5:
		return term['weekends']['sat']
	elif weekday == 6:
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
	return result
#slack에 보낼 제일 빨리 오는 버스 시간 값 return
def show_current_bus_time(current_bus_time):
	return_msg = {
			'channel' : _message['channel'],
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
def show_bus_schedule(get_bus_schedule):
	return_msg = {
			'channel' : _message['channel'],
			'type': 'message',
			'text': '<버스 시간>\n' + get_bus_schedule
		}
	return return_msg

# 사용자가 고른 시간의 5분전 시간을 구함
def get_bus_alarm_time_dict(save_log,message_text,weekday):
	chosentimedict = None
	key =''
	buses = get_key_by_location(save_log,weekday)
	bustimedict = make_bus_time_dict(buses)
	if bustimedict == None:
		return
	if message_text == '알람':
		#key(시간) 중 시간이 가장 빠른 것 구하기
		valuelist = []
		keylist = list(bustimedict.keys())
		for key in keylist:
			valuelist.append(bustimedict[key]) 
		mintime = min(valuelist)
		for bus,time in bustimedict.items():
			if time == mintime:
				key = bus
				break
				
		chosentimedict = {key:mintime}

	else :
		# 시간:버스 => 버스 : 시간
		# inv_map = {v: k for k,v in bustimedict.items()}
		if message_text == '알람 한':
			chosentimedict = chosen_time_dict_by_bus('한대앞버스',bustimedict)
			key = '한대앞버스'
		elif message_text == '알람 예':
			chosentimedict = chosen_time_dict_by_bus('예술인버스',bustimedict)
			key = '예술인버스'
		else :
			chosentimedict = chosen_time_dict_by_bus('순환버스',bustimedict)
			key = '순환버스'

	return {'bus': key,'alarm_time': calculate_five_minutes_ago(chosentimedict[key])}

def chosen_time_dict_by_bus(bus,bustimedict):
	#해당 key(버스)가 없을 때
	if not bus in bustimedict.keys():
		return
	return {bus:bustimedict[bus]} 
		
# 5분전 시간 계산
def calculate_five_minutes_ago(chonsentime):
	result = datetime.datetime.strptime(chonsentime, "%H:%M")- datetime.timedelta(minutes=5)
	return result.strftime("%H:%M")

def make_bus_time_dict(buses):
	now = datetime.datetime.now().strftime("%H:%M")
	bustimedict = None
	for bus in buses:
		for time in buses[bus]:
			if now <= time:
				if bustimedict == None:
					bustimedict = {bus:time}
				else :
					bustimedict.update({bus:time})
				break
	return bustimedict

def give_alarm():
	global _channel
	if real_alarm_time_now == True:
		return_msg = {
				'channel' : _channel,
				'type': 'message',
				'text': busalarmtimedict['bus']+'가 출발하기 5분 전입니다'
			}
		_channel = ''
		_ws.send(json.dumps(return_msg))
		return
	else:
		return

def is_real_alarm_time_now():
	global real_alarm_time_now
	now = datetime.datetime.now().strftime("%H:%M")

	if busalarmtimedict == None:
		return
	if now == busalarmtimedict['alarm_time']:
		real_alarm_time_now = True
	else:
		real_alarm_time_now = False
def difference_from_now_and_alarm_time():
	form = "%H:%M"
	now = datetime.datetime.now().strftime(form)
	alarm_time = busalarmtimedict['alarm_time']
	if not now > alarm_time:
		return
	strpnow = datetime.datetime.strptime(now,form)
	strpalarm_time = datetime.datetime.strptime(alarm_time, form)
	tdelta = strpnow -strpalarm_time 
	minute = (tdelta.seconds%3600) // 60
	return minute

def my_interval_job():
	is_real_alarm_time_now()
	give_alarm()

sched = BackgroundScheduler()
sched.add_job(my_interval_job, 'interval', seconds=3)
sched.start()


token = os.environ.get('SLACK_BOT_TOKEN')
get_url = requests.get('https://slack.com/api/rtm.connect?token=' + token)
print(get_url.json()['url'])
socket_endpoint = get_url.json()['url']
print('Connecting to', socket_endpoint)

websocket.enableTrace(True)
_ws = websocket.WebSocketApp(socket_endpoint, on_message=on_message)
_ws.run_forever()

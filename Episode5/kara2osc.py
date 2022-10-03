import argparse
import functools
import os
import socketio
import threading
from pythonosc.udp_client import SimpleUDPClient


parser = argparse.ArgumentParser(description='Karafun Current Performer OSC Sender')
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='enable logging')
parser.add_argument('channel', help='karafun session id')
parser.add_argument('ip', help='IP to broadcast to')
parser.add_argument('port', help='port to broadcast on')
args = parser.parse_args()

sio = socketio.Client(logger=args.verbose)
mtx = threading.Lock()


def mlock(f):
	@functools.wraps(f)
	def inner(*args, **kwargs):
		with mtx:
			return f(*args, **kwargs)
	return inner

@sio.event
@mlock
def connect():
	if args.verbose:
		print('connection established')
	sio.emit('authenticate', {
		'login': 'fair scheduler',
		'channel': args.channel,
		'role': 'participant',
		'app': 'karafun',
		'socket_id': None,
	})

@sio.event
@mlock
def loginAlreadyTaken():
	if args.verbose:
		print('loginAlreadyTaken')
	sio.emit('authenticate', {
		'login': 'fair scheduler %d' % os.getpid(),
		'channel': args.channel,
		'role': 'participant',
		'app': 'karafun',
		'socket_id': None,
	})

@sio.event
@mlock
def permissions(data):
	if args.verbose:
		print('permissions received ', data)

@sio.event
@mlock
def preferences(data):
	if args.verbose:
		print('preferences received ', data)
	if not data['askSingerName']:
		print('You must turn on "Ask singer\'s name when adding to queue" in the Karafun remote control settings in order for the scheduler to work.')
		sio.disconnect()

@sio.event
@mlock
def status(data):
    if args.verbose:
        print('status received ', data)



@sio.event
@mlock
def queue(data):
    client = SimpleUDPClient(args.ip, int(args.port))
    singer = data[0]['singer']
    print('Current Singer: ', singer)
    client.send_message("/singer/current", singer)
    if args.verbose:
        print('queue received ', data)

@sio.event
@mlock
def serverUnreacheable():
	print('Server unreachable. Try restarting the Karafun App?')
	sio.disconnect()

@sio.event
@mlock
def queueChange(data):
    print(data)

@sio.event
@mlock
def disconnect():
	print('Disconnected from server.')

sio.connect('https://www.karafun.com/socket.io/?remote=kf%s' % args.channel)
sio.wait()

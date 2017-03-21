from __future__ import print_function
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
from sys import stdout, stdin
from termios import tcgetattr, tcsetattr, ECHO, ICANON, TCSANOW, TCSAFLUSH
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK
from select import select
from time import strftime

##################################################################
# Hana TCP Chat Client-Server Application
# Program Class and Function Definitions
#
##################################################################

##################################################################
# BEGIN
# Exception Classes
#	Intuitive names for
# exit conditions

class UserQuit(Exception):
	def __init__(self):
		pass

class ServerDown(Exception):
	def __init__(self):
		pass

class PeerQuit(Exception):
	def __init__(self):
		pass

##################################################################
# BEGIN
# Class to manage name association with a socket

class NamedSocket:
	def __init__(self, socketholder, alias):
		self.sock = socketholder
		self.alias = alias

	def changename(self, newname):
		self.alias = newname

	def showname(self):
		return self.alias

	def fileno(self):
		return self.sock.fileno()

	def recv(self, size, flags=0):
		return self.sock.recv(size, flags)

	def send(self, string, flags=0):
		return self.sock.send(string, flags)

	def shutdown(self, how):
		self.sock.shutdown(how)

	def close(self):
		self.sock.close()

##################################################################
# BEGIN
# Class that mimics the behavior of the wrapper class NamedSocket

class SelfIdentity(NamedSocket):
	def __init__(self, alias, prompt, clientmode):
		self.alias = alias
		self.prompt = prompt
		self.keybuffer = ''
		self.cursorpos = 0
		self.mode = clientmode

	def close(self):
		print('\nReturning terminal settings')
		tcsetattr(stdin, TCSAFLUSH, termold)
		fcntl(stdin, F_SETFL, oldflags)

	def fileno(self):
		return stdin.fileno()

	def send(self, string, flags=0):
		printf(' ' * (len(self.keybuffer) - self.cursorpos))
		printf('\b \b' * (len(self.prompt + self.keybuffer)) )
		print(string.decode(stdout.encoding).lstrip().rstrip())
		printf(self.prompt + self.keybuffer + ('\b' * (len(self.keybuffer) - self.cursorpos) ) )

	def keyboardin(self, broadcast_list):
		lels = stdin.read(10)
		if lels[:1] == '\x1b': #possible esc seq

			if lels == '\x1b[D': #Left Arrow
				if self.cursorpos > 0:
					self.cursorpos = self.cursorpos - 1
					printf('\b')

			elif lels == '\x1b[C': #Right Arrow
				if self.cursorpos < len(self.keybuffer):
					printf(self.keybuffer[self.cursorpos])
					self.cursorpos = self.cursorpos + 1

			elif lels == '\x1b[F': #End
				printf(self.keybuffer[self.cursorpos:])
				self.cursorpos = len(self.keybuffer)

			elif lels == '\x1b[H': #Home
				printf('\b' * self.cursorpos)
				self.cursorpos = 0
			elif lels == '\x1b[3~': #Delete
				printf(self.keybuffer[self.cursorpos + 1:] + ' ' + ('\b' * (len(self.keybuffer) - self.cursorpos) ) )
				self.keybuffer = self.keybuffer[:self.cursorpos] + self.keybuffer[self.cursorpos + 1:]

		elif (lels == '\b' or lels == '\x7f'): #Backspace
			if self.cursorpos > 0:
				printf('\b \b')
				printf(self.keybuffer[self.cursorpos:] + ' ' + ('\b' * (len(self.keybuffer) - self.cursorpos + 1) ) )
				self.keybuffer = self.keybuffer[:self.cursorpos - 1] + self.keybuffer[self.cursorpos:]
				self.cursorpos = self.cursorpos - 1
		elif lels == '\t': #Tab
				pass
		elif lels == '\n': #Enter (send)
			self.send(('You: ' + self.keybuffer + '\n').encode(stdout.encoding))
			if self.keybuffer.lstrip().rstrip() == 'QUIT':
				serverbroadcast(self.showname() + ': QUIT', self, broadcast_list, self, 0)
				raise UserQuit
			else:
				hana = self.showname() + ': ' + self.keybuffer.lstrip().rstrip() + '\n'
				serverbroadcast(hana, self, broadcast_list, self, 0)
			printf(' ' * (len(self.keybuffer) - self.cursorpos))
			printf('\b \b' * (len(self.keybuffer)) )
			self.cursorpos = 0
			self.keybuffer = ''	
		elif len(self.keybuffer) > self.cursorpos:
			printf(lels + self.keybuffer[self.cursorpos:] + ('\b' * (len(self.keybuffer) - self.cursorpos) ) )
			self.keybuffer = self.keybuffer[:self.cursorpos] + lels + self.keybuffer[self.cursorpos:]
			self.cursorpos = self.cursorpos + len(lels)
		else:
			printf(lels)
			self.keybuffer = self.keybuffer + lels
			self.cursorpos = self.cursorpos + len(lels)
		
##################################################################
# BEGIN
# 	wrapper class for terminal select graphic rendition aka
# terminal font color and style
#

class tcolor:
	def esc(colorlist):
		return '\033[' + ';'.join(colorlist) + 'm'
	def color(string, colorlist = []):
		colorstring = '\033[' + ';'.join(colorlist) + 'm'
		return colorstring + string + '\033[0m'
		
	def remove(string):
		store = string.split('\033[')
		clean = ''
		if len(store) > 1:
			if store[0] == '':
				store = store[1:]
			for s in store:
				sp = s.split('m',1)
				if len(sp) > 1:
					clean = clean + sp[1]
			return clean
		return string

	def reset():
		return '\033[0m'

class cc:
	bold	= '1'
	italic	= '3'
	under	= '4'
	black	= 0
	red	= 1
	green	= 2
	yellow	= 3
	blue	= 4
	magenta	= 5
	cyan	= 6
	white	= 7
	def b(colornum):
		return str(40+colornum)
	def f(colornum):
		return str(30+colornum)
	def bh(colornum):
		return str(100+colornum)
	def fh(colornum):
		return str(90+colornum)

##################################################################
# function wrapper for newlineless print (and refresh)
# needed when printing without newline because of termios
#

def printf(in_str=''):
	print(in_str, end='')
	stdout.flush()

##################################################################
# function for server broadcasting
#

def serverbroadcast(in_str, sock_source, broadcast_list, hostsocket, include=1):
	data = in_str.encode(stdout.encoding)
	for socker in (broadcast_list + [hostsocket]):
		try:
			if include or socker != sock_source:
				socker.send(data)
		except BrokenPipeError:
			socker.close()
			broadcast_list.remove(socker)
			data2 = socker.showname() + ' has disconnected unexpectedly\n'
			serverbroadcaster(in_str, sock_source, broadcast_list)

##################################################################
# Hana TCP Chat Client-Server Application
# Program Start
#
##################################################################

notice = [cc.f(cc.cyan), cc.bold]
noticed = [cc.b(cc.cyan), cc.bold]
menu = [cc.b(cc.red), cc.bold]
menuitem = [cc.f(cc.blue), cc.bold]
query = [cc.f(cc.yellow),cc.bold]
mote = [cc.f(cc.green), cc.bold]
moted = [cc.b(cc.green), cc.bold]

print(tcolor.color('Machine Problem 1 - Peer to Peer Chat 1.0', notice ))
print(tcolor.color('Compliant with T 2:30-5:30 Protocol Standards', notice))
print(tcolor.color('Programmed by: Jaime Bronozo (2013-18000)', notice))
print(tcolor.color('Menu:   \t          ', [cc.f(cc.red), cc.bold]))
print(tcolor.color('\t[1] Chat Client   ', menuitem) )
print(tcolor.color('\t[2] Chat Server   ', menuitem))
try:
	keyin = input(tcolor.color('Select mode',query) + ': ')
	if keyin == '1':
		mode = 0
		address = input(tcolor.color('Enter address', query) + ': ')
	elif keyin == '2':
		mode = 1
		address = ''
	else:
		print('Invalid mode. Exiting')
		exit()

	port = int(input(tcolor.color('Enter port', query) + ': '))

	name = input(tcolor.color('Please enter a name',query) + ': ')
except KeyboardInterrupt:
	print('\n' + tcolor.color('Exiting', menu))
	exit()

# setting up connection socket
mainsocket = socket(AF_INET, SOCK_STREAM)
if mode:
	mainsocket.bind( (address, port) )
	mainsocket.listen(5)
	print(tcolor.color('Awaiting connection...', notice))
	read_sockets, _, _ = select([mainsocket], [], [])
	for rsock in read_sockets:
		clientsocket, clientaddr = rsock.accept()
		newsock = NamedSocket(clientsocket, clientaddr)
		socklist = [newsock]

else:
	print(tcolor.color('Connecting to ', notice) + tcolor.color(address+':'+str(port),noticed) + tcolor.color('...',notice))
	mainsocket.connect( (address,port) )
	socklist = [mainsocket]

prompt = '>> '

myself = SelfIdentity(name, prompt, mode)


print(tcolor.color('Switching to chat mode', mote))

message =tcolor.color('You are now chatting with ', mote) + tcolor.color(name, moted) + '\n'
serverbroadcast(message, myself, socklist, myself, 0)

# going to termios to allow per character input
oldflags = fcntl(stdin, F_GETFL)
fcntl(stdin, F_SETFL, oldflags | O_NONBLOCK)
termold = tcgetattr(stdin)
termnew = tcgetattr(stdin)
termnew[3] = termnew[3] & ~ECHO & ~ICANON
tcsetattr(stdin, TCSANOW, termnew)

printf(prompt)

try:
	while 1:

		if mode == 1:
			read_sockets, _, _ = select([mainsocket], [], [], 0)
			for rsock in read_sockets:
				clientsocket, clientaddr = rsock.accept()
				data = 'Sorry, this peer is connected to someone else.\n'
				clientsocket.send(data.encode(stdout.encoding))
				data = myself.showname() + ': QUIT'
				clientsocket.send(data.encode(stdout.encoding))
				clientsocket.shutdown(SHUT_RDWR)
				clientsocket.close()

		if socklist == []:
			raise ServerDown
		
		# receives from connected peer
		read_sockets, _, _ = select(socklist, [], [], 0)
		for rsock in read_sockets:
			hana = ''
			song = ''
			data = rsock.recv(4096).decode(stdout.encoding).lstrip().rstrip()
			if data == '':
				raise ServerDown

			result = data.split(':', 1)
			if len(result) > 1:
				hana = result[1].lstrip().rstrip()
				if hana == 'QUIT':
					serverbroadcast(data, rsock, socklist, myself, 0)
					raise PeerQuit
			data = data + '\n'
			myself.send(data.encode(stdout.encoding))

		# polling for user input
		read_keys, _, _ = select([myself], [], [], 0)
		if read_keys != []:
			myself.keyboardin(socklist)

except (KeyboardInterrupt, UserQuit):
	print('\nUser quitting...')
except PeerQuit:
	print('\nPeer has exited')
except ServerDown:
	print('\nUnexpected disconnection...')
finally:
	if mode == 1:
		for hanasong in socklist:
			try:
				hanasong.shutdown(SHUT_RDWR)
				print('Shutting down client...')
			except:
				pass
			finally:
				hanasong.close()
				print('Closing connection to client')
	else:
		mainsocket.send((myself.showname() + ': QUIT').encode(stdout.encoding))

	try:
		mainsocket.shutdown(SHUT_RDWR)
		print('Shutting down connection')
	except:
		pass
	finally:
			mainsocket.close()
			print('Closing connection')
	print('\nReturning terminal settings')
	tcsetattr(stdin, TCSAFLUSH, termold)
	fcntl(stdin, F_SETFL, oldflags)

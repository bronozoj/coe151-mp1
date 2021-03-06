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
#	Intuitive names for exit conditions

class UserQuit(Exception):
	def __init__(self):
		pass

class ServerDown(Exception):
	def __init__(self):
		pass

##################################################################
# BEGIN
# Class to manage name association with a socket

class NamedSocket:
	def __init__(self, socketholder, address):
		self.sock = socketholder
		self.addr = address
		self.alias = address[0] + (':%d' % address[1])

	def changename(self, newname):
		self.alias = newname

	def showname(self):
		return self.alias

	def showaddress(self):
		return self.addr[0] + (':%d' % self.addr[1])

	def showip(self):
		return self.addr[0]

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
	def __init__(self, port, prompt, clientmode, colormode=0):
		self.addr = ('127.0.0.1', port)
		self.alias = '127.0.0.1:%d' % port
		self.prompt = prompt
		self.keybuffer = ''
		self.cursorpos = 0
		self.mode = clientmode
		self.colormode = colormode

	def close(self):
		print('\nReturning terminal settings')
		tcsetattr(stdin, TCSAFLUSH, termold)
		fcntl(stdin, F_SETFL, oldflags)

	def fileno(self):
		return stdin.fileno()

	def send(self, string, flags=0):
		printf(' ' * (len(self.keybuffer) - self.cursorpos))
		printf('\b \b' * (len(self.prompt + self.keybuffer)) )
		out = string.decode(stdout.encoding)
		if self.colormode:
			out = tcolor.remove(out)
		print(out.lstrip().rstrip())
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
				if self.colormode:
					self.colormode = 0
					self.send('Colored output enabled\n'.encode(stdout.encoding))
				else:
					self.colormode = 1
					self.send('Colored output disabled\n'.encode(stdout.encoding))
		elif lels == '\n': #Enter (send)
			hana = ''
			song = ''
			message = ''
			self.send(('You: ' + self.keybuffer + '\n').encode(stdout.encoding))
			if self.keybuffer[:1] == '/':
				parse = self.keybuffer[1:].split(' ', 1)
				hana = parse[0]
				if len(parse) > 1:
					song = parse[1]

				if hana.upper() == 'QUIT':
					printf(' ' * (len(self.keybuffer) - self.cursorpos))
					printf('\b \b' * (len(self.keybuffer + self.prompt)) )
					raise UserQuit
				elif hana != '':
					if self.mode:
						commandprocessor(hana.upper(), song, self, broadcast_list, self)
					else:
						message = hana.upper() + ' ' + song
						serverbroadcast(message, self, broadcast_list, self, 0)
				else:
					self.send('Please enter a command after the \'/\'\n')
			else:
				if self.mode:
					commandprocessor('MSG', self.keybuffer, self, broadcast_list, self)
				else:
					message = 'MSG ' + self.keybuffer
					serverbroadcast(message + '\n', self, broadcast_list, self, 0)
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
	if include == 2:
		try:
			if include or socker != sock_source:
				sock_source.send(data)
		except BrokenPipeError:
			sock_source.close()
			broadcast_list.remove(sock_source)
			data2 = sock_source.showname() + ' has disconnected unexpectedly\n'
			serverbroadcast(in_str, sock_source, broadcast_list, hostsocket)
		finally:
			return
	else:
		for socker in (broadcast_list + [hostsocket]):
			try:
				if include or socker != sock_source:
					socker.send(data)
			except BrokenPipeError:
				socker.close()
				broadcast_list.remove(socker)
				data2 = socker.showname() + ' has disconnected unexpectedly\n'
				serverbroadcast(in_str, sock_source, broadcast_list, hostsocket)

##################################################################
# function for command processing (used when in server config)
#

def commandprocessor(command, parameters, cursock, socketslist, hostsocket):
	if command == 'QUIT':
		text = [cc.f(cc.magenta), cc.bold]
		names = [cc.b(cc.magenta), cc.bold]

		cursock.shutdown(SHUT_RDWR)
		cursock.close()
		socklist.remove(cursock)
		data = tcolor.color(cursock.showname(), names) + tcolor.color(' has disconnected',text) + '\n'
		serverbroadcast(data, cursock, socketslist, hostsocket)

	elif command == 'MSG':
		item = [cc.bold]

		data = tcolor.color(cursock.showname() + ': ',item) + parameters + '\n'
		serverbroadcast(data, cursock, socketslist, hostsocket, 0)

	elif command == 'WHOAMI':
		value = [cc.italic]
		item = [cc.b(cc.blue), cc.bold]
		head = item + [cc.under]

		data = tcolor.color('User information:', head) +'\n\t' + tcolor.color('Address:', item) + ' '
		data += tcolor.color(cursock.showaddress(), value) + '\n\t' + tcolor.color('Alias:', item)
		data += ' ' + tcolor.color(cursock.showname(), value) + '\n'
		serverbroadcast(data, cursock, socketslist, hostsocket,2)

	elif command == 'TIME':
		item = [cc.f(cc.black), cc.b(cc.white), cc.bold]

		data = tcolor.color(strftime('%Y %b %d %I:%M:%S %p (%A)'), item) + '\n'
		serverbroadcast(data, cursock, socketslist, hostsocket,2)

	elif command == 'NAME':
		if parameters == '':
			value = [cc.b(cc.red)]
			item = value + [cc.bold]

			data = tcolor.color('Error:',item) + tcolor.color(' Please enter a new alias/name',value) + '\n'
			serverbroadcast(data, cursock, socketslist, hostsocket,2)
		else :
			names = [cc.b(cc.green), cc.bold]
			text = [cc.f(cc.green), cc.italic, cc.bold]

			data = tcolor.color('User ', text) + tcolor.color(cursock.showname(), names)
			data += tcolor.color(' is now ', text) + tcolor.color(parameters, names) + '\n'
			cursock.changename(parameters)
			serverbroadcast(data, cursock, socketslist, hostsocket)
	elif command == 'WHOIS':
		if parameters == '':
			data = '\nError: No search string\n\n'
			serverbroadcast(data, cursock, socketslist, hostsocket,2)
		else:
			value = [cc.italic]
			item = [cc.b(cc.blue), cc.bold]
			head = item + [cc.under]

			datalist = list([s for s in (socklist+[hostsocket]) if (s.showip() == parameters or s.showname() == parameters)])
			for sres in datalist:
				data = '\n' + tcolor.color('User information:', head) + '\n\t' + tcolor.color('Address:', item)
				data += ' ' + tcolor.color(sres.showaddress(), value) + '\n\t' + tcolor.color('Alias:',item)
				data += ' ' + tcolor.color(sres.showname(), value) + '\n'
				cursock.send(data.encode(stdout.encoding))	
	else:
		value = [cc.b(cc.red)]
		item = value + [cc.bold]

		data = '\n' + tcolor.color('Error:', item) + tcolor.color(' Unknown command entered...', value) + '\n'
		serverbroadcast(data, cursock, socketslist, hostsocket,2)

##################################################################
# Hana TCP Chat Client-Server Application
# Program Start
#
##################################################################

notice = [cc.f(cc.cyan), cc.bold]
menu = [cc.b(cc.red), cc.bold]
menuitem = [cc.f(cc.blue), cc.bold]
query = [cc.f(cc.yellow),cc.bold]

print(tcolor.color('Machine Problem 1 - Internet Relay Chat 1.1', notice ))
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
		print(tcolor.color('Invalid mode. Exiting', menu))
		exit()

	port = int(input(tcolor.color('Enter port', query) + ': '))
except KeyboardInterrupt:
	print('\n' + tcolor.color('Exiting', menu))
	exit()

# setting up connection socket
mainsocket = socket(AF_INET, SOCK_STREAM)
if mode:
	mainsocket.bind( (address, port) )
	mainsocket.listen(5)
	runningport = port
	socklist = []
else:
	mainsocket.connect( (address,port) )
	socklist = [mainsocket]
	(_, runningport) = mainsocket.getsockname()

prompt = '>> '

myself = SelfIdentity(runningport, prompt, mode)

print(tcolor.color('Switching to chat mode', [cc.f(cc.green), cc.bold]))

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
				newsock = NamedSocket(clientsocket, clientaddr)
				data = tcolor.color(newsock.showname(), [cc.b(cc.magenta), cc.bold])
				data += tcolor.color(' has connected',[cc.f(cc.magenta), cc.bold]) +'\n'
				socklist.append(newsock)
				serverbroadcast(data, newsock, socklist, myself, 0)
		
		# client - receives from connected server
		# server - receives and parses commands
		read_sockets, _, _ = select(socklist, [], [], 0)
		for rsock in read_sockets:
			hana = ''
			song = ''
			data = rsock.recv(4096).decode(stdout.encoding).lstrip().rstrip()
			if data == '':
				if mode == 0:
					print('data is ' + data)
					raise ServerDown
				hana = 'QUIT'
			if mode:
				result = data.split(' ', 1)
				hana = result[0]
				if len(result) > 1:
					song = result[1]
				commandprocessor(hana, song, rsock, socklist, myself)
			else:
				data = data + '\n'
				myself.send(data.encode(stdout.encoding))

		#polling for user input
		read_keys, _, _ = select([myself], [], [], 0)
		if read_keys != []:
			myself.keyboardin(socklist)

except (KeyboardInterrupt, UserQuit):
	print('\nUser quitting...')
except ServerDown:
	print('\nUnexpected disconnection...')
finally:
	if mode:
		for hanasong in socklist:
			try:
				hanasong.shutdown(SHUT_RDWR)
			except:
				pass
			finally:
				hanasong.close()
	else:
		mainsocket.send('QUIT'.encode(stdout.encoding))
	try:
		mainsocket.shutdown(SHUT_RDWR)
	except:
		pass
	finally:
		mainsocket.close()
	print('\nReturning terminal settings')
	tcsetattr(stdin, TCSAFLUSH, termold)
	fcntl(stdin, F_SETFL, oldflags)

from __future__ import print_function
import socket
import select
import sys
import signal
import time

def printf(in_str=''):
	print(in_str, end='')
	sys.stdout.flush()
	return

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

def broadcaster(data, cursock, socketslist, selfsend=1):
	for socker in socklist:
		try:
			if cursock != socker or selfsend:
				socker.send(data)
		except BrokenPipe:
			data2 = socker.showname() + ' has disconnected unexpectedly\n'
			socker.close()
			print(data2)
			data2 = data2.encode(sys.stdout.encoding)
			broadcaster(data2, cursock, socketslist)

def exitsequence():
	print('Closing Server')
	for esock in socklist:
		esock.shutdown(socket.SHUT_RDWR)
		esock.close()
	serversocket.shutdown(socket.SHUT_RDWR)
	serversocket.close()
	exit()

signal.signal(signal.SIGTERM, exitsequence)
			

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

socklist = []

host = socket.gethostname()
port = 52157

serversocket.bind(('', port))

serversocket.listen(5)

print('Server has been initialized in port %d' % port)

try:
	while 1:
		csock, _, _ = select.select([serversocket], [], [], 0)

		for clisock in csock:
			clientsocket, addr = serversocket.accept()
			sockname = NamedSocket(clientsocket, addr)
			data = tcolor.color(sockname.showname(),[cc.b(cc.magenta), cc.bold])
			data += tcolor.color(' has connected',[cc.f(cc.magenta), cc.bold]) + '\n'
			printf(tcolor.remove(data))
			data = data.encode(sys.stdout.encoding)
			socklist = socklist + [sockname]			
			broadcaster(data, sockname, socklist, 0)

		readsock, _, _ = select.select(socklist, [], [], 0)
		for rsock in readsock:
			#print('receiving data')
			try:
				data = rsock.recv(4096).decode(sys.stdout.encoding).lstrip().rstrip()
			except:	
				data = '/quit'
			result = data.split(' ', 1)
			hana = result[0]
			song = ''
			if len(result) > 1:
				song = result[1]
			if data == '':
				hana == 'QUIT'
			

			#print(hana)
			#input('trash')

			if hana == 'QUIT':
				text = [cc.f(cc.magenta), cc.bold]
				names = [cc.b(cc.magenta), cc.bold]

				print('closing connection for ' + rsock.showname())
				rsock.shutdown(socket.SHUT_RDWR)
				rsock.close()
				socklist.remove(rsock)
				data = tcolor.color(rsock.showname(),names) + tcolor.color(' has disconnected',text) + '\n'
				data = data.encode(sys.stdout.encoding)
				broadcaster(data, rsock, socklist, 0)
			elif hana == 'MSG':
				item = [cc.bold]

				data = tcolor.color(rsock.showname() + ' : ', item) + song + '\n'
				printf(tcolor.remove(data))
				data = data.encode(sys.stdout.encoding)
				broadcaster(data, rsock, socklist, 0)
			elif hana == 'WHOAMI':
				value = [cc.italic]
				item = [cc.b(cc.blue), cc.bold]
				head = item + [cc.under]

				print('Asked for self identification')
				data = tcolor.color('User information:', head)  + '\n\t' + tcolor.color('Address:', item) 
				data += ' ' + tcolor.color(rsock.showaddress(), value) + '\n\t'
				data += tcolor.color('Alias:', item) + ' ' + tcolor.color(rsock.showname(), value) + '\n'
				printf(tcolor.remove(data))
				rsock.send(data.encode(sys.stdout.encoding))

			elif hana == 'TIME':
				item = [cc.f(cc.black), cc.b(cc.white), cc.bold]

				data = tcolor.color(time.strftime('%Y %b %d %I:%M:%S %p (%A)'), item) + '\n'
				printf('Asked for time: ' + tcolor.remove(data))
				rsock.send(data.encode(sys.stdout.encoding))

			elif hana == 'NAME':
				if song == '':				
					value = [cc.b(cc.red)]
					item = value + [cc.bold]
					data = tcolor.color('Error:', item) + tcolor.color(' Please enter a new alias/name', value) + '\n'
					rsock.send(data.encode(sys.stdout.encoding))
				else :
					names = [cc.b(cc.green), cc.bold]
					text = [cc.f(cc.green), cc.italic, cc.bold]

					print('Changing name from ' + rsock.showname() + ' to ' + song)
					data = tcolor.color('User ', text) + tcolor.color(rsock.showname(), names)
					data += tcolor.color(' is now ', text) + tcolor.color(song, names) + '\n'
					rsock.changename(song)
					data = data.encode(sys.stdout.encoding)
					broadcaster(data, rsock, socklist, 1)
			elif hana == 'WHOIS':
				if song == '':
					data = '\nError: No search string\n\n'
					rsock.send(data.encode(sys.stdout.encoding))
				else:
					value = [cc.italic]
					item = [cc.b(cc.blue), cc.bold]
					head = item + [cc.under]
					print('Searched for ' + song)
					datalist = list([s for s in socklist if (s.showip() == song or s.showname() == song)])
					for sres in datalist:
						data = '\n' + tcolor.color('User information:', head) + '\n\t'
						data += tcolor.color('Address:', item) + ' ' + tcolor.color(sres.showaddress(), value)
						data += '\n\t' + tcolor.color('Alias:', item) + ' '
						data += tcolor.color(sres.showname(),value) + '\n'
						rsock.send(data.encode(sys.stdout.encoding))	
			else:				
				value = [cc.b(cc.red)]
				item = value + [cc.bold]
				data = ('\n' + tcolor.color('Error:', item) + tcolor.color(' Unknown command entered...', value) + '\n').encode(sys.stdout.encoding)
				try:
					rsock.send(data)
				except (BrokenPipeError, ConnectionResetError):
					socklist.remove(rsock)
					data = rsock.showname() + ' has disconnected'
					print(data)
					data = data.encode(sys.stdout.encoding)
					broadcaster(data, rsock, socklist, 0)
					rsock.close()
				
except KeyboardInterrupt:
	exitsequence()

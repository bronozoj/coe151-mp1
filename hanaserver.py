from __future__ import print_function
import socket
import select
import sys
import signal

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
			data = sockname.showname() + ' has connected\n'
			printf(data)
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
				print('closing connection for ' + rsock.showname())
				rsock.shutdown(socket.SHUT_RDWR)
				rsock.close()
				socklist.remove(rsock)
				data = rsock.showname() + ' has disconnected\n'
				data = data.encode(sys.stdout.encoding)
				broadcaster(data, rsock, socklist, 0)
			elif hana == 'MSG':
				data = rsock.showname() + ' : ' + song + '\n'
				printf(data)
				data = data.encode(sys.stdout.encoding)
				broadcaster(data, rsock, socklist, 0)
			elif hana == 'WHOAMI':
				data = 'User information:\n\tAddress: ' + rsock.showaddress()
				data = data + '\n\tAlias: ' + rsock.showname() + '\n'
				rsock.send(data.encode(sys.stdout.encoding))

			elif hana == 'TIME':
				data = 'Its High Noon...(somewhere in the world)\n'.encode(sys.stdout.encoding)
				rsock.send(data)

			elif hana == 'NAME':
				if song == '':
					data = 'Error: Please enter a new alias/name\n'
					rsock.send(data.encode(sys.stdout.encoding))
				else :
					print('Changing name from ' + rsock.showname() + ' to ' + song)
					data = 'User ' + rsock.showname() + ' is now ' + song + '\n'
					rsock.changename(song)
					data = data.encode(sys.stdout.encoding)
					broadcaster(data, rsock, socklist, 1)
			elif hana == 'WHOIS':
				if song == '':
					data = '\nError: No search string\n\n'
					rsock.send(data.encode(sys.stdout.encoding))
				else:
					datalist = list([s for s in socklist if (s.showip() == song or s.showname() == song)])
					for sres in datalist:
						data = '\nUser information:\n\tAddress: ' + sres.showaddress()
						data = data + '\n\tAlias: ' + sres.showname() + '\n'
						rsock.send(data.encode(sys.stdout.encoding))	
			else:
				data = '\nError: Unknown command entered...\n\n'.encode(sys.stdout.encoding)
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

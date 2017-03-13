from __future__ import print_function
from socket import *
from select import *
import fcntl
from os import O_NONBLOCK
import sys
import termios

def printf(in_str=''):
	print(in_str, end='')
	sys.stdout.flush()
	return

class UserQuit(Exception):
	def __init(self, expression, message):
		self.expression = expression
		self.message = message

class ServerDown(Exception):
	def __init(self, expression, message):
		self.expression = expression
		self.message = message

prompt = '~: '
serverName = input('Where to connect?: ')
if serverName == 'charles':
	serverName = '10.158.22.158'
elif serverName == 'maambelay':
	serverName = '10.158.22.207'
elif serverName == 'localhost':
	serverName = gethostname()
elif serverName == 'hanaserver':
	serverName = '10.158.22.151'

serverPort = int (input('Enter port: '))
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName,serverPort))

oldflags = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
fcntl.fcntl(sys.stdin, fcntl.F_SETFL, oldflags | O_NONBLOCK)
termold = termios.tcgetattr(sys.stdin)
termnew = termios.tcgetattr(sys.stdin)
termnew[3] = termnew[3] & ~termios.ECHO & ~termios.ICANON
termios.tcsetattr(sys.stdin, termios.TCSANOW, termnew)

printf(prompt)
keyin = ''
cursorpos = 0
try :
	while 1:
		read_sockets, _, _ = select([clientSocket], [], [], 0)
		if read_sockets != []:
			data = clientSocket.recv(4096).decode(sys.stdout.encoding).rstrip().lstrip()
			if data == '':
				raise ServerDown('Unexpected blank output', 'Socket may have been shut down')
			printf(' ' * (len(keyin) - cursorpos) )
			printf('\b \b' * (len(prompt + keyin)) )
			print(data)
			printf(prompt + keyin + ('\b' * (len(keyin) - cursorpos) ) )

		read_keys, _, _ = select([sys.stdin], [], [], 0)
		if read_keys != []:
			lels = sys.stdin.read(10)
			if lels[:1] == '\x1b': #possible esc seq
				if lels == '\x1b[D' and cursorpos > 0: # left arrow
					cursorpos = cursorpos - 1
					printf('\b')

				elif lels == '\x1b[C' and cursorpos < len(keyin):						
					printf(keyin[cursorpos])   # right arrow
					cursorpos = cursorpos + 1

				elif lels == '\x1b[F': #End
					printf(keyin[cursorpos:])
					cursorpos = len(keyin)

				elif lels == '\x1b[H': #Home
					printf('\b' * cursorpos)
					cursorpos = 0

				elif lels == '\x1b[5~': #PgUp
					pass#lels = sys.stdin.read(1)

				elif lels == '\x1b[6~': #PgDn
					pass#lels = sys.stdin.read(1)

				#else:
				#	printf(lels)
			elif (lels == '\b' or lels[:1] == '\x7f'): #backspace
				if cursorpos > 0:
					printf('\b \b')
					printf(keyin[cursorpos:] + ' ' + ('\b' * (len(keyin) - cursorpos + 1) ) )
					sys.stdout.flush()
					keyin = keyin[:cursorpos - 1] + keyin[cursorpos:]
					cursorpos = cursorpos - 1
			elif lels == '\n': #send
				hana = ''
				song = ''
				message = ''
				if keyin[:1] == '/':
					parse = keyin[1:].split(' ', 1)
					hana = parse[0]
					if len(parse) > 1:
						song = parse[1]
						#print('hey ' + song)

					if hana.upper() == 'QUIT':
						raise UserQuit('User Termination', 'typed /quit')
					elif hana != '':
						message = hana.upper() + ' ' + song
					else:
						printf('\b \b' * (len(prompt + keyin)) )
						printf('Please enter a command after the \'/\'\n')
						printf(prompt + keyin + ('\b' * (len(keyin) - cursorpos) ) )
				else:
					message = 'MSG ' + keyin
				clientSocket.send(message.encode(sys.stdout.encoding))
				print( ('\b \b' * (len(prompt + keyin)) ) + 'You: ' + keyin)
				cursorpos = 0
				keyin = ''
				printf(prompt)
				if hana[:1] == 'QUIT':
					break
			elif len(keyin) > cursorpos:
				printf(lels + keyin[cursorpos:] + ('\b' * (len(keyin) - cursorpos) ) )
				keyin = keyin[:cursorpos] + lels + keyin[cursorpos:]
				cursorpos = cursorpos + 1
			else:
				print(lels, end='')
				sys.stdout.flush()
				keyin = keyin + lels
				cursorpos = cursorpos + 1
except (KeyboardInterrupt, UserQuit):
	clientSocket.send("QUIT".encode(sys.stdout.encoding))
	print("\nGonna quit")
except ServerDown:
	print("\nServer has shut down")
finally :
	clientSocket.close()
	print("\nReturning system state")
	termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, termold)
	fcntl.fcntl(sys.stdin, fcntl.F_SETFL, oldflags)

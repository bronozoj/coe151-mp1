from __future__ import print_function
import termios
from os import O_NONBLOCK
import sys
import fcntl
from select import select

def printf(in_str=''):
	print(in_str, end='')
	sys.stdout.flush()
	return

def recvprint(data, p, k, cpos):
	printf(' ' * (len(k) - cpos))
	printf('\b \b' * (len(p) + len(k)) )
	print(data)
	printf(p + k + ('\b' * (len(k) - cpos) ) )

keyin = ''

oldflags = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
fcntl.fcntl(sys.stdin, fcntl.F_SETFL, oldflags | O_NONBLOCK)
termold = termios.tcgetattr(sys.stdin)
termnew = termios.tcgetattr(sys.stdin)

termnew[3] = termnew[3] & ~termios.ECHO & ~termios.ICANON
termios.tcsetattr(sys.stdin, termios.TCSANOW, termnew)

dva = 0

prompt = '~: '
printf(prompt)
sys.stdout.flush()
try:
	while 1:
		[noob, _, _] = select([sys.stdin], [], [], 0)
	
		if noob != []:#print('getting input')
			lels = sys.stdin.read(10)
			#print('debug input number %d' % ord(lels))
			if lels[:1] == '\x1b': # Escape Sequence Block

				if lels == '\x1b[A':
					recvprint('Up Arrow pressed', prompt, keyin, dva)
				elif lels == '\x1b[B':
					recvprint('Down Arrow pressed', prompt, keyin, dva)
				elif lels == '\x1b[D': # Left arrow
					if dva > 0:
						dva = dva - 1
						printf('\b')
				elif lels == '\x1b[C':
					if dva < len(keyin):
						printf(keyin[dva])   # right arrow
						dva = dva + 1
				elif lels == '\x1b[F': #End
					printf(keyin[dva:])
					dva = len(keyin)
				elif lels == '\x1b[H': #Home
					printf('\b' * dva)
					dva = 0
				elif lels == '\x1b[5~': #PgUp
					recvprint('Page Up pressed', prompt, keyin, dva)
				elif lels == '\x1b[6~': #PgDn
					recvprint('Page Down pressed', prompt, keyin, dva)
				elif lels == '\x1bOQ': #F2?
					recvprint('F2 pressed', prompt, keyin, dva)
				elif lels == '\x1bOR':
					recvprint('F3 pressed', prompt, keyin, dva)
				elif lels == '\x1bOS':
					recvprint('F4 pressed', prompt, keyin, dva)
				elif lels == '\x1b[15~':
					recvprint('F5 pressed', prompt, keyin, dva)
				elif lels == '\x1b[17~':
					recvprint('F6 pressed', prompt, keyin, dva)
				elif lels == '\x1b[18~':
					recvprint('F7 pressed', prompt, keyin, dva)
				elif lels == '\x1b[19~':
					recvprint('F8 pressed', prompt, keyin, dva)
				elif lels == '\x1b[20~':
						recvprint('F9 pressed', prompt, keyin, dva)
				elif lels == '\x1b[21~':
					recvprint('F10 pressed', prompt, keyin, dva)
				elif lels == '\x1b[24~':
					recvprint('F12 pressed', prompt, keyin, dva)
				elif lels == '\x1b[3~': # Delete
					#recvprint('Delete pressed', prompt, keyin, dva)
					if dva > 0:
						printf(keyin[dva + 1:] + ' ' + ('\b' * (len(keyin) - dva) ) )
						sys.stdout.flush()
						keyin = keyin[:dva] + keyin[dva + 1:]	
				else:
					printf(lels)
				#print('esc seq is ' + lels)
			elif (lels == '\b' or lels[:1] == '\x7f'):
				if dva > 0:
					printf('\b \b')
					printf(keyin[dva:] + ' ' + ('\b' * (len(keyin) - dva + 1) ) )
					sys.stdout.flush()
					keyin = keyin[:dva - 1] + keyin[dva:]
					dva = dva - 1
			elif lels == '\t':
				recvprint('Tab is pressed', prompt, keyin, dva)
			elif lels == '\n':
				print('\nexiting')
				break
			elif len(keyin) > dva:
				printf(lels + keyin[dva:] + ('\b' * (len(keyin) - dva) ) )
				keyin = keyin[:dva] + lels + keyin[dva:]
				dva = dva + 1
			else:
				print(lels, end='')
				sys.stdout.flush()
				keyin = keyin + lels
				dva = dva + 1
finally:
	print(('final output(%d): ' % len(keyin)) + keyin)
	termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, termold)
	fcntl.fcntl(sys.stdin, fcntl.F_SETFL, oldflags)

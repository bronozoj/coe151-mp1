import socket

class UserQuit(Exception):
	"""Base class"""
	def __init__(self, expression, message):
		self.expression = expression
		self.message = message

class NamedSocket(socket):
	def __init__(self, handledsocket)
		self.tsock = handledsocket
		handledsocket.

try:
	data = input('Test me: ')
	if data == 'dickbutt':
		raise UserQuit('lolXD', 'ggwp')
except (KeyboardInterrupt, UserQuit):
	print('dayum')

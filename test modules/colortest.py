class tcolor:
	def reset():
		return '\033[0m'
	def esc(colorlist):
		return '\033[' + ';'.join(colorlist) + 'm'
	def color(string, colorlist = []):
		colorstring = '\033[' + ';'.join(colorlist) + 'm'
		return colorstring + string + tcolor.reset()
		
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

	def len(string):
		store = string.split('\033[')
		clean = 0
		if len(store) > 1:
			if store[0] == '':
				store = store[1:]
			for s in store:
				sp = s.split('m',1)
				if len(sp) > 1:
					clean += len(sp[1])
			return clean
		return len(string)

class cc:
	bold	='1'
	italic	='3'
	under	='4'
	black	=0
	red	=1
	green	=2
	yellow	=3
	blue	=4
	magenta	=5
	cyan	=6
	white	=7
	def b(colornum):
		return str(40+colornum)
	def f(colornum):
		return str(30+colornum)
	def bh(colornum):
		return str(100+colornum)
	def fh(colornum):
		return str(90+colornum)

string = tcolor.esc([cc.f(cc.cyan), cc.bold]) + 'hello' + tcolor.color('[hi]', [cc.f(cc.yellow), cc.italic])
print(string + ' - %d' % len(string))
clean = tcolor.remove(string)
print(clean + ' - %d' % tcolor.len(string))
print(tcolor.color(clean, [cc.f(cc.red),cc.under]))

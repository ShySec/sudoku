import re
import sys
import copy
import string
import random
import collections

gPrefix = ''

def read_board(filename, analyze=True, debug=False):
	layout = []
	with open(filename,'rb') as reader:
		for line in reader.readlines():
			line = line.rstrip('\r\n')
			if not line: continue
			fixed = re.sub('[ _-]','0',line)
			row = map(lambda x:int(ord(x)-ord('0')),fixed)
			if debug: print '%s -> %s -> %s'%(line,fixed,row)
			layout.append(row)
	board = dict(layout=layout)
	if analyze: board = analyze_board(board,debug)
	board['states'] = [copy.deepcopy(board)]
	return board

def analyze_board(board, debug=False):
	layout = board['layout']
	width = len(layout)

	missing = 0
	analysis = collections.defaultdict(lambda:collections.defaultdict(set))
	for row,rdata in enumerate(layout):
		for col,value in enumerate(rdata):
			if value != 0: continue
			analysis[row][col].update(range(1,width+1))
			missing += 1
	board['analysis'] = analysis
	board['missing'] = missing

	for row in xrange(width): analyze_board_row(board, row)
	for col in xrange(width): analyze_board_column(board, col)
	for square in xrange(width): analyze_board_square(board, square)
	return board

def analyze_restriction(board, row, column, data):
	original = board['analysis'].get(row,{}).get(column)
	if not original: return board
	original.difference_update(data)
	return board

def analyze_board_row(board, row):
	layout,width = board['layout'],len(board['layout'])
	data = set(filter(lambda x:x,layout[row]))
	for column in xrange(width): analyze_restriction(board, row, column, data)
	return data

def analyze_board_column(board, column):
	layout,width = board['layout'],len(board['layout'])
	data = [layout[row][column] for row in xrange(width)]
	data = set(filter(lambda x:x,data))
	for row in xrange(width): analyze_restriction(board, row, column, data)
	return data

def analyze_board_square(board, square):
	layout,width = board['layout'],len(board['layout'])
	border = int(width**0.5)

	data = set()
	roffset = (square/border)*border
	coffset = (square%border)*border
	for row in xrange(border):
		for col in xrange(border):
			data.add(layout[row+roffset][col+coffset])
	data.discard(0)
	for row in xrange(border):
		for column in xrange(border):
			analyze_restriction(board, row+roffset, column+coffset, data)
	return data

def bordered(index, border, width):
	if index == width-1: return False
	if (index+1)%border: return False
	return True

def board_keys():
	alphabet = string.lowercase+string.punctuation+string.uppercase
	alphabet = re.sub('[ |-]','',alphabet)
	while True:
		for key in alphabet: yield key

def stringify_board(board, analysis=True):
	rval = ''
	layout = board['layout']
	width = len(layout)
	border = int(width**0.5)
	if analysis:
		mapping=dict()
		letters=board_keys()
	for rnum,rdata in enumerate(layout):
		for cnum,cdata in enumerate(rdata):
			if cdata:
				rval += str(cdata)
			elif analysis:
				key = letters.next()
				mapping[key] = board['analysis'][rnum][cnum]
				rval += key
			else:
				rval += ' '
			if bordered(cnum,border,width):
				rval += '|'
		rval += '\n'
		if bordered(rnum,border,width):
			rval += '-'*(width+border-1) + '\n'
	if analysis and len(mapping):
		rval += '\n'
		for key in mapping:
			rval += '%s %s\n'%(key,sorted(list(mapping[key])))

	return rval

def update_board(board, row, column, value, save_state=True):
	if board['layout'][row][column] == value: return
	if board['layout'][row][column] == 0: board['missing'] -= 1
	board['analysis'][row][column] = set()
	board['layout'][row][column] = value
	analyze_board_row(board, row)
	analyze_board_column(board, column)
	analyze_board_square(board, square_index(board,row,column))
	if save_state: board['states'].append(copy.deepcopy(dict(filter(lambda x:x[0]!='states',board.iteritems()))))
	return board

def square_index(board, row, column):
	layout,width = board['layout'],len(board['layout'])
	border = int(width**0.5)
	square = (row/border)*border + (column/border)
	return square

def report(data):
	if gPrefix: print '%s %s'%(gPrefix,data)
	else: print data

def solve_board(board, save_state=True, debug=False):
	while board['missing']:
		step = solve_board_step(board, debug=debug)
		if not step: pass
		if not step: raise Exception('failed to solve\n%s'%(stringify_board(board)))
		board = step
	return board

def solve_board_step(board, debug=False):
	update = None
	apply_update = lambda board,update:update_board(board,update[0],update[1],update[2])
	if not update: update = solve_board_step_last_remnant(board,debug)
	if not update: update = solve_board_step_last_in_row(board,debug)
	if not update: update = solve_board_step_last_in_column(board,debug)
	if update: return apply_update(board, update)
	return solve_board_step_random(board,debug)

def solve_board_step_last_remnant(board, debug=False):
	layout,width = board['layout'],len(board['layout'])
	for row in xrange(width):
		for col in xrange(width):
			if layout[row][col] != 0: continue
			cdata = board['analysis'][row][col]
			if len(cdata) == 0: raise Exception('unsolveable at %d,%d\n%s'%(row,col,stringify_board(board)))
			if len(cdata) != 1: continue
			update = (row,col,cdata.pop())
			if debug: report('%d,%d => %d (last-remnant)'%update)
			return update

def solve_board_step_last_in_row(board, debug=False):
	layout,width = board['layout'],len(board['layout'])
	for row in xrange(width):
		counter = collections.defaultdict(int)
		for col in xrange(width):
			if layout[row][col] != 0: continue
			for value in board['analysis'][row][col]:
				counter[value] += 1
		values = [k for k,v in filter(lambda p:p[1]==1,counter.items())]
		if not len(values): continue
		value = values[0]
		update = [(row,col,value) for col in xrange(width) if value in board['analysis'][row][col]][0]
		if debug: report('%d,%d => %d (last-in-row)'%update)
		return update

def solve_board_step_last_in_column(board, debug=False):
	layout,width = board['layout'],len(board['layout'])
	for col in xrange(width):
		counter = collections.defaultdict(int)
		for row in xrange(width):
			if layout[row][col] != 0: continue
			for value in board['analysis'][row][col]:
				counter[value] += 1
		values = [k for k,v in filter(lambda p:p[1]==1,counter.items())]
		if not len(values): continue
		value = values[0]
		update = [(row,col,value) for row in xrange(width) if value in board['analysis'][row][col]][0]
		if debug: report('%d,%d => %d (last-in-column)'%update)
		return update

def solve_board_step_last_in_square(board, debug=False):
	layout,width = board['layout'],len(board['layout'])
	border = int(width**0.5)
	for square in xrange(width):
		roffset = (square/border)*border
		coffset = (square%border)*border
		counter = collections.defaultdict(int)
		for row in xrange(border):
			for col in xrange(border):
				if layout[roffset+row][coffset+col] != 0: continue
				for value in board['analysis'][roffset+row][coffset+col]:
					counter[value] += 1
		values = [k for k,v in filter(lambda p:p[1]==1,counter.items())]
		if not len(values): continue
		value = values[0]
		for row in xrange(border):
			for col in xrange(border):
				if layout[roffset+row][coffset+col] != 0: continue
				if value in board['analysis'][roffset+row][coffset+col]:
					update = (roffset+row,coffset+col,value)
					if debug: report('%d,%d => %d (last-in-square)'%update)
					return update

def solve_board_step_random(board, debug=False):
	layout,width = board['layout'],len(board['layout'])
	print '\n%s'%stringify_board(board,False)
	for row in xrange(width):
		for col in xrange(width):
			if layout[row][col] != 0: continue
			values = sorted(list(board['analysis'][row][col]))
			for value in values:
				print 'brute forcing %d,%d=%s => %d'%(row,col,values,value)
				global gPrefix
				gPrefix += '-'
				bruting_board = copy.deepcopy(board)
				bruting_board = update_board(bruting_board,row,col,value)
				try:
					bruting_board = solve_board(bruting_board, debug=debug)
				except:
					print 'brute forcing failed; unwinding'
					bruting_board = None
				gPrefix = gPrefix[:-1]
				if bruting_board: return bruting_board

if __name__ == '__main__':
	if len(sys.argv)<2:
		sys.stderr.write('usage: %s <filename>\n'%(sys.argv[0],))
		sys.stderr.flush()
		sys.exit(0)
	board = read_board(sys.argv[1])
	print stringify_board(board)
	#board = update_board(board, 0, 1, 4)
	#print stringify_board(board)
	board = solve_board(board,debug=True)
	if not board['missing']: print '\npuzzle solved\n'
	print stringify_board(board)
	sys.exit(1)
	print_board(solution)

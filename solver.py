import re
import sys
import copy
import string
import random
import logging
import collections

gPrefix = ''

class Unsolveable(Exception): pass

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
	for square in xrange(width): analyze_board_square_implied(board, square)
	return board

def analyze_restriction(board, row, column, data):
	original = board['analysis'].get(row,{}).get(column)
	if original: original.difference_update(data)
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

def get_board_square_entries(board, square):
	layout,width = board['layout'],len(board['layout'])
	border = int(width**0.5)
	roffset = (square/border)*border
	coffset = (square%border)*border

	data = list()
	for row in xrange(border):
		for col in xrange(border):
			data.append(layout[row+roffset][col+coffset])
	return data

def analyze_board_square(board, square):
	layout,width = board['layout'],len(board['layout'])
	border = int(width**0.5)
	roffset = (square/border)*border
	coffset = (square%border)*border

	data = set(get_board_square_entries(board, square))
	for row in xrange(border):
		for column in xrange(border):
			analyze_restriction(board, row+roffset, column+coffset, data)
	return data

def analyze_board_square_implied(board, square, recursive=True):
	layout,width = board['layout'],len(board['layout'])
	border = int(width**0.5)
	roffset = (square/border)*border
	coffset = (square%border)*border

	analysis = list()
	for row in xrange(border):
		for col in xrange(border):
			analysis.extend(board['analysis'][row+roffset][col+coffset])
	data = collections.Counter(analysis)

	squares = set()
	for row in xrange(border): squares.update(analyze_board_square_implied_row(board, square, row, data))
	for col in xrange(border): squares.update(analyze_board_square_implied_column(board, square, col, data))
	if recursive:
		for modified_square in squares: analyze_board_square_implied(board, modified_square)
	return data

def str_index(row, column):
	return '%d,%d'%(column+1,row+1)

def analyze_board_square_implied_row(board, square, row, data):
	layout,width = board['layout'],len(board['layout'])
	border = int(width**0.5)
	roffset = (square/border)*border
	coffset = (square%border)*border

	squares = set()
	entries = list()
	for col in xrange(border):
		entries.extend(board['analysis'][row+roffset][col+coffset])
	entries = collections.Counter(entries)
	for entry in entries:
		if entries[entry] != data[entry]: continue
		# the values -must- be in this square, not outside on this row
		for col in xrange(width):
			if col/border == coffset/border: continue # same square
			if entry not in board['analysis'][row+roffset][col]: continue
			logging.debug('analysis eliminating %d from %s by row-implication from square %d',entry,str_index(row+roffset,col),square)
			analyze_restriction(board, row+roffset, col, [entry]) # eliminate the option
			squares.add(square_index(board,row+roffset,col)) # record updated square
	return squares

def analyze_board_square_implied_column(board, square, column, data):
	layout,width = board['layout'],len(board['layout'])
	border = int(width**0.5)
	roffset = (square/border)*border
	coffset = (square%border)*border

	squares = set()
	entries = list()
	for row in xrange(border):
		entries.extend(board['analysis'][row+roffset][column+coffset])
	entries = collections.Counter(entries)
	for entry in entries:
		if entries[entry] != data[entry]: continue
		# the values -must- be in this square, not outside on this row
		for row in xrange(width):
			if row/border == roffset/border: continue # same square
			if entry not in board['analysis'][row][column+coffset]: continue
			logging.debug('analysis eliminating %d from %s by column-implication from square %d',entry,str_index(row,column+coffset),square)
			analyze_restriction(board, row, column+coffset, [entry]) # eliminate the option
			squares.add(square_index(board,row,column+coffset)) # record updated square
	return squares

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
	analyze_board_square_implied(board, square_index(board,row,column))
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

def solve_board(board, brute=True, save_state=True, debug=False):
	while board['missing']:
		step = solve_board_step(board, brute=brute, debug=debug)
		if not step: raise Unsolveable('failed to solve\n%s'%(stringify_board(board)))
		board = step
	return board

def solve_board_step(board, brute=True, debug=False):
	update = None
	if not update: update = solve_board_step_last_remnant(board,debug)
	if not update: update = solve_board_step_last_in_row(board,debug)
	if not update: update = solve_board_step_last_in_column(board,debug)
	if update: return update_board(board,update[0],update[1],update[2])
	if brute: return solve_board_step_random(board,debug)

def solve_board_step_last_remnant(board, debug=False):
	layout,width = board['layout'],len(board['layout'])
	for row in xrange(width):
		for col in xrange(width):
			if layout[row][col] != 0: continue
			cdata = board['analysis'][row][col]
			if len(cdata) == 0: raise Exception('unsolveable at %d,%d\n%s'%(row,col,stringify_board(board)))
			if len(cdata) != 1: continue
			update = (row,col,cdata.pop())
			if debug: report('%d,%d => %d (single-option)'%update)
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
	if debug: print '\n%s'%stringify_board(board,False)
	for row in xrange(width):
		for col in xrange(width):
			if layout[row][col] != 0: continue
			values = sorted(list(board['analysis'][row][col]))
			for value in values:
				if debug: print 'brute forcing %d,%d=%s => %d'%(row,col,values,value)
				global gPrefix
				gPrefix += '-'
				bruting_board = copy.deepcopy(board)
				bruting_board = update_board(bruting_board,row,col,value)
				try:
					bruting_board = solve_board(bruting_board, debug=debug)
				except:
					if debug: print 'brute forcing failed; unwinding'
					bruting_board = None
				gPrefix = gPrefix[:-1]
				if bruting_board: return bruting_board

def unittest(path='boards'):
	import os
	blacklist=['t04.csv']
	for test in os.listdir(path):
		if test in blacklist: continue
		print test
		board = read_board(os.path.join(path,test))
		board = solve_board(board,debug=False)

if __name__ == '__main__':
	if len(sys.argv)<2:
		sys.stderr.write('usage: %s <filename>\n'%(sys.argv[0],))
		sys.stderr.flush()
		sys.exit(0)
	board = read_board(sys.argv[1])
	print stringify_board(board)
	board = solve_board(board,brute=True,debug=True)
	if not board['missing']: print '\npuzzle solved\n'
	print stringify_board(board)
	sys.exit(1)
	print_board(solution)

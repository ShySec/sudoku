import re
import sys
import copy

def read_board(filename, analyze=True, debug=False):
	layout = []
	with open(filename,'rb') as reader:
		for line in reader.readlines():
			if not line: continue
			line = line.rstrip('\r\n')
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

	board['rows'] = width*[set()]
	for row in xrange(width): analyze_board_row(board, row)

	board['cols'] = width*[set()]
	for col in xrange(width): analyze_board_column(board, col)

	board['squares'] = width*[set()]
	for square in xrange(width): analyze_board_square(board, square)
	return board

def analyze_board_row(board, row):
	layout,width = board['layout'],len(board['layout'])
	data = set(filter(lambda x:x,layout[row]))
	board['rows'][row] = data
	return data

def analyze_board_column(board, column):
	layout,width = board['layout'],len(board['layout'])
	data = [layout[row][column] for row in xrange(width)]
	data = set(filter(lambda x:x,data))
	board['cols'][column] = data
	return data

def analyze_board_square(board, square):
	layout,width = board['layout'],len(board['layout'])
	border = int(width**0.5)

	sdata = set()
	roffset = (square/border)*border
	coffset = (square%border)*border
	for row in xrange(border):
		for col in xrange(border):
			sdata.add(layout[row+roffset][col+coffset])
	sdata.discard(0)
	board['squares'][square] = sdata
	return sdata

def bordered(index, border, width):
	if index == width-1: return False
	if (index+1)%border: return False
	return True

def stringify_board(board, analysis=True):
	rval = ''
	layout = board['layout']
	width = len(layout)
	border = int(width**0.5)
	for rnum,rdata in enumerate(layout):
		for cnum,cdata in enumerate(rdata):
			rval += str(cdata) if cdata else ' '
			if bordered(cnum,border,width):
				rval += '|'
		if analysis:
			rval += ' -> %s'%sorted(list(board['rows'][rnum]))
		rval += '\n'
		if bordered(rnum,border,width):
			rval += '-'*(width+border-1) + '\n'
	if analysis:
		rval += '\n'
		for rnum in xrange(width):
			segment = ''
			for cnum in xrange(width):
				if len(board['cols'][cnum])>rnum:
					rval += str(sorted(list(board['cols'][cnum]))[rnum])
				else:
					rval += ' '
				if bordered(cnum,border,width):
					rval += ' '
			snum = rnum
			rval += ' || %s'%(sorted(list(board['squares'][snum])))
			rval += '\n'
	return rval

def update_board(board, row, column, value, save_state=True):
	if board['layout'][row][column] == value: return
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

def solve_board(board, debug=False):
	pass


if __name__ == '__main__':
	if len(sys.argv)<2:
		sys.stderr.write('usage: %s <filename>\n'%(sys.argv[0],))
		sys.stderr.flush()
		sys.exit(0)
	board = read_board(sys.argv[1])
	print stringify_board(board)
	#board = update_board(board, 0, 1, 4)
	#print stringify_board(board)
	solution = solve_board(board,True)
	sys.exit(1)
	print_board(solution)

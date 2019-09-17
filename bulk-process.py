import sys, getopt, os
import subprocess
from colours import colours

def second_last(s: str, o: str) -> int:
	return s[:s.rfind(o)].rfind(o)

# Get command-line args
PATH = None
try:
	opts, args = getopt.getopt(sys.argv[1:], 'f:', ['file='])
except getopt.GetoptError:
	print('USAGE: python bulk-process.py -f <FILE>')
	exit()

for opt, arg in opts:
	if opt in ('-f', '--file'):
		PATH = arg.replace('\\', '/')

if PATH == None:
	print('USAGE: python bulk-process.py -f <FILE>')
	exit()


# Read in the file containing a list of paths
f = open(PATH, 'r')
paths = f.readlines()

# Lists to hold names of (un)successfully preprocessed issues
success = []
failure = []

# Preprocess the files at each listed path
for path in paths:
	path = path.strip().replace('\\', '/')
	if not path == '':
		print('--------------------------------')
		try:
			res = os.system(f'python preprocess.py -p {path}')
			
			# Check if our subprocess exited with a non-zero exit code (i.e. error)
			if res != 0:
				raise Exception
			else:
				success.append(path[second_last(path, '/')+1:path.rindex('/')])
		except:
			failure.append(path[second_last(path, '/')+1:path.rindex('/')] + f' - ERR CODE {res}')

# Print summary of preprocessing results to user
print('\n\n--------------------------------\nSummary\n--------------------------------')
if len(success) > 0:
	print(f'Successfully preprocessed: {colours.GREEN}{success}{colours.ENDC}')
if len(failure) > 0:
	print(f'Failed to preprocess: {colours.RED}{failure}{colours.ENDC}')



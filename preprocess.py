import os
import re
import sys
import getopt
from typing import List, Dict, Tuple, Union, Optional
from species_link import insertSpeciesLinks
from colours import colours
from xml import xml

# Constants
YESNO = f'({colours.GREEN}y{colours.ENDC}/{colours.RED}n{colours.ENDC})'

# Global variables. 
# Journal Issue information. inf prefixe stands for 'inferred'
inf_year = ""
inf_volume = ""
inf_number = ""
inf_journal_code = ""




def remove_NA_authors(lines: List[str]) -> None:
	"""
	Removes NA from any of the <author> and <authors> tags if applicable.
	Mutates the list of lines passed in.

	:param lines: list of lines in an xml file
	:returns: None
	"""

	# N.B.: <author> tag is always line 2.
	if re.match(
				r'\s*\<author seq=\"1\"\>((n\/?a)|none)\<\/author\>',
				lines[1], re.IGNORECASE
				) and re.match(r'\s*\<authors seq=\"1\"\>', lines[2]):
		# Replace line 2 with empty tag if NA was supplied as author's name
		lines[1] = "  <author seq=\"1\"></author>"

		# Replace line 4 with empty last name tag
		lines[3] = "    <lastname/>"


def common_text_subs(text: str) -> str:
	"""
	Formats words that predominantly require the processor to manually format 
	them with their most commonly formatted variant.

	:param text: text in which to replace unformatted words
	:returns: text with proper xml format tags applied
	"""
	
	txt_substitutions = {
		'H2O2': 'H<sub>2</sub>O<sub>2</sub>',
		'H2O': 'H<sub>2</sub>O',
		'H20': 'H<sub>2</sub>0',
		'H2SO4': 'H<sub>2</sub>SO<sub>4</sub>',
		'&lt;!--': '<!--',
		'--&gt;': '-->',
		'\\\'': '\''
	}

	# Store the regexes as single-item tuples (so they'll work in the loop)
	reg_substitutions = {
		# simple tags
		(r'&lt;(|/)(i|b|sup|sub)&gt;',): (r'<\1\2>',),
		# inverse units  
		(r'(m|g|ha| L|ml)-1',): (r'\1<sup>-1</sup>',),
		# scientific notation
		(r'(\d?\.?\d+ ?\n?(x|&#215;)\n? ?10)(-?\d+)',): (r'\1<sup>\3</sup>',),
		# extra whitespace in hyphenations
		(r'-\n ?',): (r'-',),
		# 50-doses
		(r'(LC|LD|IC)50',): (r'\1<sub>50</sub>',),
		# Bi-elemental oxygen compounds
		(r'([A-Z]|\d)O(\d)(\d?(\+|-|))',): (r'\1O<sub>\2</sub><sup>\3</sup>',),
		# metre-based units
		(r'/(cm|km|m)(\d)',): (r'/\1<sup>\2</sup>',),
		# Ammonia-based compounds
		(r'NH(\d)(\+?)',): (r'NH<sub>\1</sub><sup>\2</sup>',),
	}

	# Replace all above simple text matches
	for key in txt_substitutions.keys():
		text = text.replace(key, txt_substitutions[key])

	# Replace all the above regex patterns
	for key in reg_substitutions.keys():
		text = re.sub(key[0], reg_substitutions[key][0], text, re.IGNORECASE)

	# Remove any empty tags (a few may be added during the above loops)
	text = re.sub(r'<(i|b|sup|sub)><\/\1>', '', text, re.IGNORECASE)

	return text
	

def surround_headers(text: str, front: str, special_front: str, back: str) -> str:
	"""
	For a header in common_headers below, it is replaced by the sequence
	(special_)front+header+back, thereby automatically applying bold, italics,
	or linebreaks to the different sections within an abstract.

	special_front is only applied for introduction headers that don't require
	a preceeding linebreak.

	:param text: the text containing headers to format
	:param front: the opening format tag
	:param special_front: the opening format tag (for intro headers only)
	:param back: the closing format tag
	:returns: text with format tags applied to the headers in it
	"""
	intro_headers = ["background:", "Background:", "Background\n", "Context:", "Introduction:", "Introduction\n", 'BACKGROUND', 'Purpose:']
	common_headers = ["materials and methods:", "Materials and methods:", "Materials and Methods:", "Data and methods:", "Data Source &amp; Method:", "Data Source and Methods:",
					  "result:", "results:",
					  "Result:", "Results:", "Results\n", "conclusion:",
					  "conclusions:", "Conclusion:", "Conclusions:",
					  "Conclusions\n", "Objective:", "Objectives:", 'OBJECTIVES',
					  "Discussion:", "Discussions:", "Antecedente:",
					  "Objetivo:", "M&#233;todos:", "Resultados:",
					  "Objectif:", "M&#233;thodologie:", "R&#233;sultats:",
					  "Conclusiones:", "Aim", "Aims", 'FINDINGS', 'Findings:', 'MAIN CONCLUSION', 'MAIN CONCLUSIONS', 'RESULTS']
	method_headers = ["methods:", "method:", "Methods:", "Method:", "Method"
					  "Methods\n", "Methodology:", 'METHODS']

	for header in intro_headers + common_headers + method_headers:
		# If not an intro header
		if header.lower() not in [h.lower() for h in intro_headers]:
			text = text.replace(header, "\n" + front + header + back)
		else:
			text = text.replace(header, "\n" + special_front + header + back)

	# I know this is a bit of a cheap way to fix the problem of METHODS getting
	# extra headers applied to it when its in MATERIALS AND METHODS. But it
	# works for now.
	problematic_headers = {"<br/><b>Materials and \n<br/><b>Methods:</b></b>":
						   "<br/><b>Materials and Methods:</b>",
						   "<br/><b>Materials and \n<br/><b>methods:</b></b>":
						   "<br/><b>Materials and methods:</b>"}
	for key in problematic_headers.keys():
		text = text.replace(key, problematic_headers[key])

	return text





def exists_discrepencies(d: Dict[str, str], expected: str) -> bool:
	"""
	Returns True if any of the files (keys of d) maps to a value other than
	expected. Returns False otherwise.

	:param d: the dictionary
	:param expected: the value we're comparing each value of dict to
	:returns: True if at least one value in d != expected. False otherwise
	"""

	for key in d.keys():
		if d[key] != expected:
			return True
	return False


def print_discrepancy_report(d: Dict[str, str], disc_type: str) -> bool:
	"""
	Displays a message to the user listing all the errors found of type
	disc_type as well as what the expected value should be.

	:param d: the dictionary containing discrepancies (errors)
	:param disc_type: the type of discrepencies (number, volume, or year)
	:returns: None
	"""

	print(f'{colours.RED}Journal {disc_type} discrepancies:{colours.ENDC}')
	proper_values = {"number": inf_number, "year": inf_year,
					 "volume": inf_volume}
	expected = proper_values[disc_type]

	problems = dict()
	for key in d.keys():
		if d[key] != expected:
			problems[key] = d[key]
	for key in problems.keys():
		print(key + ": Expected " + disc_type + "=\"" + str(expected) +
			  "\" but got " + disc_type + "=\"" + problems[key] + "\"")
	print("")
	return problems


def update_index(line: str, to_update: str, article_id: Optional[str]=None) -> str:
	spaces = 0
	while(line[spaces] == ' '):
		spaces += 1

	tokens = line[spaces:].split(' ')

	# Split the 3rd token in half
	tokens[2] = tokens[2].split('N')

	# All together, our index has been split like so:
	#           <index>year  JOURNAL    Volume        Number            ID</index>
	components = [tokens[0], tokens[1], tokens[2][0], 'N'+tokens[2][1], tokens[3]]

	to_update = to_update.lower()
	if to_update == 'y':   # Update year
		components[0] = '<index>' + inf_year
	elif to_update == 'v': # Update volume
		components[2] = 'V' + inf_volume
	elif to_update == 'n': # Update number
		components[3] = 'N' + inf_number
	elif to_update == 'i':
		components[4] = article_id + '</index>'

	line = ''
	for i in range(len(components)):
		line += components[i]
		if i != 2 and i != 4:
			line += ' '

	return spaces * ' ' + line



def fix_redundant_page_numbers(line: str) -> str:
	"""
	Replaces redunant page numbering (of the form pages="x-x") with
	the simplified version (pages="x")
	:param line: line containing pages attribute to fix
	:returns: line with redundant page numbering removed
	"""

	pages = xml.get_attribute("pages", line)
	if (re.match(r'(\d+)-\1$', pages)):
		line = xml.set_attribute("pages", pages[:pages.index("-")], line)
	return line


def fix_discrepencies(files: Dict[str, str], directory_path: str, disc_type: str, expected: str) -> None:
	"""
	For each file in files, the incorrect attribute (disc_type) is updated
	with the correct value (expected).

	:param files: a 'discrepancy dictionary' mapping filenames to their value
				  for disc_type (only the keys are used)
	:param directory_path: path to xml file directory
	:param disc_type: the type of discrepencies (number, volume, year)
	:param expected: the correct value for the given discrepancy
	:returns: None
	"""

	# Loop through each file that needs fixing
	for filename in files.keys():
		print("Fixing " + filename + "...")

		# read in file contents
		f = open(directory_path + filename, "r")
		lines = f.read().splitlines()
		f.close()

		# replace the incorrect attribute with the expected one
		lines[0] = xml.set_attribute(disc_type, expected, lines[0])

		# If volume or number or were changed, we also need to update the index
		# tag
		if disc_type == "volume" or disc_type == "number":
			# Locate the index line. Should always be 3rd last line
			lines[-3] = update_index(lines[-3], disc_type[0])
		# If the year was updated, we also need to change the index tag
		if disc_type == "year":
			lines[-3] = update_index(lines[-3], 'y')

		# Rejoin all lines on newline and write to file
		body = "\n".join(lines)
		f = open(directory_path + filename, "w")
		f.write(body)
		f.close()
	print("")


def write_problems_file(path: str, files: Dict[str, str]) -> None:
	"""
	Generates proofing file to be filled out by Proofing Student.

	:param path: the path (including name) of the proofing file
	:param files: a dict where all the keys are the filenames of the xml files
				  for this issue (values of dict are not used)
	:returns: None
	"""
	file_body = "Proofed by: \n\n"
	for file in files.keys():
		file_body += file[:len(file)-4] + ":\n\n"

	f = open(path, 'w')
	f.write(file_body)
	f.close()


def extract_implicit_info(path: str) -> Tuple[str, str, str, str]:
	"""
	(str) -> (str, str, str, str)
	Returns the volume, number, year, and journal code for this particular
	journal by extracting info from the directory structure and file-naming
	conventions for Bioline tickets.

	:param path: filepath matching .*/\w\w\d+(\d+)/
	:returns: volume, number, year, and journal code for this issue
	"""

	# Filepath looks like .../.../jjVV(N)/
	folder = path[:-5]
	folder = folder[folder.rindex("/")+1:]

	# Pull out the journal code, volume, and issue
	inf_journal_code = folder[0:2].lower()
	inf_volume = folder[2:folder.index("(")]
	inf_number = folder[folder.index("(")+1:folder.index(")")]

	# Nest a level deeper and get the year
	for filename in os.listdir(path):
		# XML files are ALWAYS of the form JJYY###.xml
		year = filename[2:4]
		year = "19" + year if int(year) > 80 else "20" + year
		return (inf_volume, inf_number, year, inf_journal_code)


def bval(b: str) -> bool:
	'''
	Converts a string to boolean with custom True-words

	:param b: string to be made into a bool
	:returns: truth value of the string passed in
	'''
	return b.lower() in ['y', 'yes', 'true']


def save_config(config: Dict[str, Union[str, bool, int]]) -> None:
	'''
	Writes a journal configuration out to a .config file

	:param config: dict of config tokens to values
	'''
	config_f = open(f'./config/{inf_journal_code}.config', 'w')
	for key in config.keys():
		config_f.write(key + '=' + str(config[key]) + '\n' * (0 if key == 'SPECIESLINKS' else 1))
	config_f.close()


def get_input(message: str, input_type: str) -> Union[str, int, bool]:
	'''
	(str, str) -> str or int or bool
	Repeatedly prompts user for input, displaying message, and returning user input
	converted to type input_type.

	:param message: message to display in input() prompt
	:param type: 's' -> str, 'i' -> int, 'b' -> bool
	:returns: valid input of type input_type
	'''
	input_type = input_type.lower()
	valid_input = False
	while not valid_input:
		user_input = input(message).strip('\n')
		
		if len(user_input) == 0:
			pass
		elif input_type == 's':
			valid_input = True
		elif input_type == 'i':
			try:
				user_input = int(user_input)
				valid_input = True
			except ValueError:
				print('Please enter an integer.\n')
			except Exception as ex:
				print(f'{colours.RED}(ERR 03):{colours.ENDC} {str(ex)}')
		elif input_type == 'b':
			user_input = bval(user_input)
			valid_input = True
			
	return user_input




# MAIN CODE #
# Handle command line arguments
DEBUG = False
PATH = None

try:
	opts, args = getopt.getopt(sys.argv[1:], 'p:d', ['path=', 'debug'])
except getopt.GetoptError:
	print('GetoptError')
	exit(3)

for opt, arg in opts:
	if opt in ('-p', '--path'):
		PATH = arg.replace('\\', '/')
	if opt in ('-d', '--debug'):
		DEBUG = True


# Get the file path of the xml folder and appropriately format it
filepath = PATH
if (filepath == None):
	filepath = get_input("Enter path to xml folder to process: ", 's').replace('\\', '/')
if not filepath.endswith("/"):
	filepath += "/"

# Make sure path meets the pattern: .../jjv(n)/xml/
if not re.match(r'.*\/[a-z]{2}\d+\(.+\)\/xml\/$', filepath):
	print(f"{colours.RED}FILEPATH FORMAT ERROR (ERR 002):{colours.ENDC}" + \
		" Filepath should end with /jjvv(n)/xml (regex .*\/[a-z]{2}\d+\(.+\)\/xml\/$)")
	exit(2)

# Determine volume, year, issue, and number based on the path to the xml folder
(inf_volume, inf_number, inf_year, inf_journal_code) = extract_implicit_info(filepath)

# Declare variables read in from config files
copyright = 'default'
textSubs = False
before_newline_count = 0
after_newline_count = 0
boldHeaders = False
italicHeaders = False
speciesLinks = False
split_keywords = True

try:
	# Read in the data from the config file if it exists
	config_f = open(f'./config/{inf_journal_code}.config', 'r')

	print(f'Loading configuration for \'{inf_journal_code}\'...\n')
	for line in config_f.readlines():
		tokens = [t.strip() for t in line.split('=')]
		if tokens[0] == 'COPYRIGHT':
			copyright = tokens[1]
		elif tokens[0] == 'TEXTSUBS':
			textSubs = bval(tokens[1])
		elif tokens[0] == 'NEWLINESBEFORE':
			before_newline_count = int(tokens[1])
		elif tokens[0] == 'NEWLINESAFTER':
			after_newline_count = int(tokens[1])
		elif tokens[0] == 'BOLD':
			boldHeaders = bval(tokens[1])
		elif tokens[0] == 'ITALIC':
			italicHeaders = bval(tokens[1])
		elif tokens[0] == 'SPECIESLINKS':
			speciesLinks = bval(tokens[1])
		elif tokens[0] == 'SPLITKEYWORDS':
			split_keywords = bval(tokens[1])
		elif len(tokens[0]) > 0: #UNKNOWN TOKEN
			print(f'{colours.RED}UNKNOWN TOKEN (ERR 001):{colours.ENDC}: Unknown token \'{tokens[0]}\' in file \'{inf_journal_code}.config\'')
			exit(1)

except FileNotFoundError:
	# Manually retrieve config values from user

	copyright = get_input("Enter the journal copyright (or \"default\" if unsure): ", 's')
	textSubs = get_input(f"Auto-format common words? {YESNO}: ", 'b')
	addNewLine = get_input(f"Add newlines before abstract section headers? {YESNO}: ", 'b')
	if (addNewLine):
		before_newline_count = get_input("How many? ", 'i')
	addNewLine = get_input(f"Add newlines after abstract section headers? {YESNO}: ", 'b')
	if (addNewLine):
		after_newline_count = get_input("How many? ", 'i')
	boldHeaders = get_input(f"Bold abstract headers? {YESNO}: ", 'b')
	italicHeaders = get_input(f"Italic abstract headers? {YESNO}: ", 'b')
	speciesLinks = get_input(f"Attempt to automatically insert species links? {YESNO}: ", 'b')
	split_keywords = get_input(f"Keywords uploaded as comma-delimited strings? {YESNO}: ", 'b')
	
	# Save configuration for later reuse if desired
	save = get_input(f'Save this configuration for {inf_journal_code}? {YESNO}: ', 's')
	if (save):
		config = {
			'COPYRIGHT': copyright,
			'TEXTSUBS': textSubs,
			'NEWLINESBEFORE': before_newline_count,
			'NEWLINESAFTER': after_newline_count,
			'BOLD': boldHeaders,
			'ITALIC': italicHeaders,
			'SPECIESLINKS': speciesLinks,
			'SPLITKEYWORDS': split_keywords
		}
		save_config(config)
		print(f'{colours.GREEN}Configuration saved!{colours.ENDC}\n')

# Define dictionaries to search for discrepancies
file_to_volume = dict()
file_to_number = dict()
file_to_year = dict()

print(f'{colours.YELLOW}Starting XML processing{colours.ENDC}')
# Loop through each xml file in the directory
for filename in os.listdir(filepath):
	if filename.endswith(".xml"):

		# Read the file contents into a list
		lines = []
		with open(filepath + filename) as f:
			lines = f.read().splitlines()
			f.close()

		# NB: LINE 0 IS ALWAYS THE <abstract> LINE IN A BIOLINE XML!

		# Check if this file as already been processed
		if not lines[0].strip().startswith("<article id=\"" + filename[0:2] + "xxx\""):
			print("Already processed " + filename + "...")
			continue

		# Replace id="JJxxx" with appropriate values
		print("Processing " + filename + "...")
		lines[0] = xml.set_attribute('id', filename[0:-4], lines[0])

		# Fix redundant page numbers if possible
		lines[0] = fix_redundant_page_numbers(lines[0])

		# Add elements to our discrepancy dictionaries
		file_to_volume[filename] = xml.get_attribute('volume', lines[0])
		file_to_number[filename] = xml.get_attribute('number', lines[0])
		file_to_year[filename] = xml.get_attribute('year', lines[0])

		# Remove NA from authors if applicable
		remove_NA_authors(lines)

		# Loop through remaining lines and replace values as appropriate
		for i in range(len(lines)):

			# Replace NA titles if applicable
			if lines[i].strip().startswith('<title') or lines[i].strip().startswith('<abstract') or lines[i].strip().startswith('<keyword'):
				lines[i] = xml.remove_NA(lines[i])

			# Replace copyright if applicable
			if xml.get_tag(lines[i]) == 'copyright':
				if (copyright != "default"):
					lines[i] = f"  <copyright>Copyright {inf_year} - {copyright}</copyright>"
				else:
					lines[i] = f'  <copyright>Copyright {inf_year} - {lines[i][lines[i].find("<copyright>")+11:-12]} </copyright>'

			# Remove superfluous commas from keywords if applicable
			elif xml.get_tag(lines[i]) == 'keyword':
				lines[i] = lines[i].replace(",;", ";")
				if split_keywords:
					lines[i] = lines[i].replace(',', ';')

			# Replace the id in the index tag with the appropriate value
			elif xml.get_tag(lines[i]) == 'index':
				lines[i] = update_index(lines[i], 'i', filename[0:-4])

		# Join list of lines on newline char
		body = "\n".join(lines)

		# Add linebreaks, italics, and bolds to common abstract sections
		if (boldHeaders and italicHeaders):
			body = surround_headers(body, '<br/>' * before_newline_count + '<b><i>', '<b><i>', '</i></b>' + '<br/>' * after_newline_count)
		elif boldHeaders:
			body = surround_headers(body, '<br/>' * before_newline_count + '<b>', '<b>', '</b>' + '<br/>' * after_newline_count)
		elif italicHeaders:
			body = surround_headers(body, '<br/>' * before_newline_count + '<i>', '<i>', '</i>' + '<br/>' * after_newline_count)
		elif before_newline_count > 0:
			body = surround_headers(body, '<br/>' * before_newline_count, '', '<br/>' * after_newline_count)

		# Perform common textual substitutions
		if textSubs:
			body = common_text_subs(body)

		# Add species links if the user requested it
		if speciesLinks:
			body = insertSpeciesLinks(body)

		# If we're in debug mode, print lines to console. 
		if DEBUG:
			print(f'------------------------------\n{body}\n------------------------------')
		else:
			# Otherwise, write processed lines back to file
			f = open(filepath + filename, "w")
			f.write(body)
			f.close()

print(f"{colours.GREEN}Completed XML processing!{colours.ENDC}")
print(f"\n{colours.YELLOW}Generating proofing file{colours.ENDC}")
write_problems_file(filepath + "../" + inf_journal_code + inf_volume + "(" +
					inf_number + ") Problems.txt", file_to_volume)
print(f"{colours.GREEN}Proofing file generated!{colours.ENDC}")


# Exit at this stage if in debug mode
if DEBUG:
	exit(0)

print(f"\n{colours.YELLOW}Performing Discrepancy Analysis{colours.ENDC}")

# Fix any problems with volume numbers (if so desired by user)
confirmation = f"Would you like to automatically fix these problems? {YESNO}: "

if exists_discrepencies(file_to_volume, inf_volume):
	problems = print_discrepancy_report(file_to_volume, "volume")
	if get_input(confirmation, 'b'):
		fix_discrepencies(problems, filepath, "volume", inf_volume)

# Fix any problems with issue numbers (if so desired by user)
if exists_discrepencies(file_to_number, inf_number):
	problems = print_discrepancy_report(file_to_number, "number")
	if get_input(confirmation, 'b'):
		fix_discrepencies(problems, filepath, "number", inf_number)

# Fix any problems with published year (if so desired by user)
if exists_discrepencies(file_to_year, inf_year):
	problems = print_discrepancy_report(file_to_year, "year")
	if get_input(confirmation, 'b'):
		fix_discrepencies(problems, filepath, "year", inf_year)

print(f'{colours.GREEN}Discrepancies resolved!{colours.ENDC}\n\nPlease proceed to manual processing of each file.')

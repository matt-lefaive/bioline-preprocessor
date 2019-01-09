import os
import re
from species_link import insertSpeciesLinks

# Global variables
inf_year = ""
inf_volume = ""
inf_number = ""
inf_journal_code = ""

### FUNCTIONS ###
def set_article_id(filename, line):
	''' (str, str) -> str
	Sets id="jjxxx" to id=${filename} in the <article> line
	'''
	# First item in lines is always the <article> tag
	new_line = "<article id=\"" + filename[0:-4] + "\" "
	new_line += line[line.index("lang="):]
	return new_line

def remove_NA(line, tag):
	'''(str) -> str
	Removes n/a and its derivatives from tag specified by *tag*.

	>>> remove_NA("<title>NA</title>", "title")
	"<title></title>"
	'''
	derivatives = ["na", "n/a", "none"]
	for derivative in derivatives:
		if (line.lower().endswith(">" + derivative + "</" + tag + ">")):
			return line[0:line.index(">")+1] + "</" + tag + ">"
	# There were no na derivatives. Return the line as is.
	return line

def remove_NA_Authors(lines):
	''' ([str,]) -> None
	Removes NA from any of the <author> and <authors> tags if applicable.
	Mutates the list of lines passed in.
	'''
	# <author> tag is always line 2. 
	if re.match(r'\s*\<author seq=\"1\"\>((n\/?a)|none)\<\/author\>', lines[1], re.IGNORECASE) and \
	   re.match(r'\s*\<authors seq=\"1\"\>', lines[2]):
	    # Replace line 2 with empty tag if NA was supplied as author's name
		lines[1] = "  <author seq=\"1\"></author>"
		
		# Replace line 4 with empty last name tag
		lines[3] = "    <lastname/>"

def setIndexId(filename, line):
	'''(str) -> str
	Sets the last element of the <index> tag to the filename (minus extension of course)
	'''
	return line[0:line.index("xxx<")-2] + filename[0:-4] + "</index>"

def commonTextSubs(text):
	'''(str) -> str
	Replaces words or sequences in abstract that predominantly require the processor to manually format
	them with their most commonly formatted version.
	'''
	substitutions = {"H2O2":"H<sub>2</sub>O<sub>2</sub>",
					 "H2O": "H<sub>2</sub>O",
					 "CO2": "CO<sub>2</sub>",
					 "NO3-": "NO<sub>3</sub><sup>-</sup>",
					 "NO3": "NO<sub>3</sub>",
					 "NO2-": "NO<sub>2</sub><sup>-</sup>",
					 "NO2": "NO<sub>2</sub>",
					 "NH4+": "NH<sub>4</sub><sup>+</sup>",
					 "&lt;i&gt;": "<i>",
					 "&lt;/i&gt;": "</i>",
					 "&lt;b&gt;": "<b>",
					 "&lt;/b&gt;": "</b>",
					 "&lt;!--": "<!--",
					 "--&gt;": "-->",
					 " L-1": " L<sup>-1</sup>", # leading space prevents formatting IL-1 (interleukin)
					 "ha-1": "ha<sup>-1</sup>",
					 "\\\'": "\'",
					 "LC50": "LC<sub>50</sub>",
					 "LD50": "LD<sub>50</sub>",
					 "IC50": "IC<sub>50</sub>",
					 "/m2": "/m<sup>2</sup>",
					 "m-1": "m<sup>-1</sup>"}

	for key in substitutions.keys():
		text = text.replace(key, substitutions[key])

	return text

def surroundHeaders(text, front, special_front, back):
	'''(str, str, str, str) -> str
	For a header h in common_headers, it is replaced by the sequence (special_)front+header+back, thereby
	automatically applying bold, italics, or linebreaks to the different sections within an abstract.
	'''
	intro_headers = ["background:", "Background:", "Background\n", "Context:", "Introduction:", "Introduction\n"]
	common_headers = ["materials and methods:", "Materials and methods:", "Materials and Methods:",
					  "result:", "results:", "Result:", "Results:", "Results\n",
					  "conclusion:", "conclusions:", "Conclusion:", "Conclusions:", "Conclusions\n",
					  "Objective:", "Objectives:",
					  "Discussion:", "Discussions:",
					  "Antecedente:", "Objetivo:", "M&#233;todos:", "Resultados:", "Conclusiones:"]
	method_headers = ["methods:", "method:", "Methods:", "Method:", "Methods\n", "Methodology:"]

	for header in intro_headers + common_headers + method_headers:
		# If not an intro header
		if header.lower() not in [h.lower() for h in intro_headers]:
			text = text.replace(header, "\n" + front + header + back)
		else:
			text = text.replace(header, "\n" + special_front + header + back)

	# I know this is a bit of a hacky way to fix the problem of METHODS getting extra headers
	# applied to it when its in MATERIALS AND METHODS. But it works for now. Sorry, will make
	# this more elegant later.
	problematic_headers = {"<br/><b>Materials and \n<br/><b>Methods:</b></b>": "<br/><b>Materials and Methods:</b></b>",
						   "<br/><b>Materials and \n<br/><b>methods:</b></b>": "<br/><b>Materials and methods:</b></b>"}
	for key in problematic_headers.keys():
		text = text.replace(key, problematic_headers[key])

	return text

def getAttribute(text, attribute):
	''' (str, str) -> str
	Returns the value of a given attribute in a line of text (where text is a valid xml tag)

	>>> getAttribute('<article year="1997"></article>', 'year')
	"1997"
	'''
	start = attribute + "=\""
	if start not in text:
		return ""
	text = text[text.index(start) + len(start):]
	return text[:text.index("\"")]

def existsDiscrepencies(d, expected):
	''' (dict {str:str}, str) -> bool
	Returns true if any of the files (keys of d) maps to a value other than expected.
	Returns false otherwise.
	'''
	for key in d.keys():
		if d[key] != expected:
			return True
	return False

def printDiscrepancyReport(d, disc_type):
	print("Journal " + disc_type + " discrepancies:")
	proper_values = {"number":inf_number, "year":inf_year, "volume":inf_volume}
	expected = proper_values[disc_type]

	problems = dict()
	for key in d.keys():
		if d[key] != expected:
			problems[key] = d[key]
	for key in problems.keys():
		print(key +": Expected " + disc_type + "=\"" + str(expected) + "\" but got " + disc_type + "=\""+ problems[key] + "\"")
	print("")
	return problems

def updateAttribute(attribute, new_val, text):
	# Get everything up to the point we have to change
	att = attribute + "=\""
	front_index = text.index(attribute) + len(att)
	front_text = text[:front_index]

	# Get everything after the point we have to change
	i = front_index
	while (text[i] != '\"' and i < len(text)):
		i = i + 1
	end_text = text[i:]

	# Sandwich in new attribute
	return front_text + new_val + end_text

def updateIndexVN(line, VN, to_update):
    spaces = 0
    while(line[spaces] == ' '):
    	spaces += 1

    tokens = line[spaces:].split(" ")
    
    # The third token is the one we need to update. But first must be split
    tokens[2] = tokens[2].split("N")
    components = [tokens[0], tokens[1], tokens[2][0], "N"+tokens[2][1], tokens[3]]
    
    if to_update.upper() == 'V':
        components[2] = 'V' + str(VN)
    elif to_update.upper() == 'N':
        components[3] = 'N' + str(VN)
        
    line = ""
    for i in range(len(components)):
        line += components[i]
        if i != 2 and i != 4:
            line += " "
        
    return spaces * " " + line

def update_index_year(line):
	''' (str) -> str
	Replace the year in the <index> line with inf_year (global variable)
	'''
	spaces = 0;
	while(line[spaces] == ' '):
		spaces += 1

	tokens = line[spaces:].split(" ")

	# The first token, <index>YYYY, is the one we need to change
	tokens[0] = "<index>" + inf_year

	# Return the line put back together
	return spaces * " " + " ".join(tokens)

def fix_redundant_page_numbers(line):
	''' (str) -> str
	Replaces redunant page numberings (those of the form pages="x-x") with
	the simplified version (pages="x")
	'''
	pages = getAttribute(line, "pages")
	if (re.match(r'(\d+)-\1', pages)):
		line = updateAttribute("pages", pages[:pages.index("-")], line)
	return line

def fix_discrepencies(files, directory_path, disc_type, expected):
	''' (dict, str, str, str) ->
	For each file in files, the incorrect attribute (disc_type) is updated
	with the correct value (expected).
	'''
	# Loop through each file that needs fixing
	for filename in files.keys():
		print("... Fixing " + filename)

		# read in file contents
		f = open(directory_path + filename, "r")
		lines = f.read().splitlines()
		f.close()

		# replace the incorrect attribute with the expected one
		lines[0] = updateAttribute(disc_type, expected, lines[0])

		# If volume or number or were changed, we also need to update the index tag
		if disc_type == "volume" or disc_type == "number":
			# Locate the index line. Should always be 3rd last line
			lines[-3] = updateIndexVN(lines[-3], expected, disc_type[0])
		# If the year was updated, we also need to change the index tag
		if disc_type == "year":
			lines[-3] = update_index_year(lines[-3])

		# Rejoin all lines on newline and write to file
		body = "\n".join(lines)
		f = open(directory_path + filename, "w")
		f.write(body)
		f.close()
	print("")

def write_problems_file(path, files):
	''' (str, {str->str}) -> Null
	Generates proofing file to be filled out by Proofing Student.
	'''
	file_body = "Proofed by: \n\n"
	for file in files.keys():
		file_body += file[:len(file)-4] + ":\n\n"

	f = open(path, 'w')
	f.write(file_body)
	f.close()


def extract_implicit_info(path):
	''' (str) -> (str, str, str, str)
	Returns the volume, number, year, and journal code for this particular
	journal by extracting info from the directory structure and file-naming
	conventions for Bioline tickets.
	'''

	# Filepath looks like .../.../jjVV(N)/
	folder = path[:-5]
	folder = folder[folder.rindex("/")+1:]

	# Pull out the journal code, volume, and issue
	inf_journal_code = folder[0:2]
	inf_volume = folder[2:folder.index("(")]
	inf_number = folder[folder.index("(")+1:folder.index(")")]

	# Nest a level deeper and get the year
	for filename in os.listdir(path):
		# XML files are ALWAYS of the form JJYY###.xml
		year = filename[2:4]
		year = "19" + year if int(year) > 80 else "20" + year
		return (inf_volume, inf_number, year, inf_journal_code)


### MAIN CODE ###
# Get the file path of the /xml folder and appropriately format it
filepath = input("Enter path to xml folder to process: ")
filepath = filepath.replace("\\", "/")
if not filepath.endswith("/"):
	filepath += "/"

# Make sure path meets the pattern: .../jjv(n)/xml/
if not re.match(r'.*\/[a-z]{2}\d+\(.+\)\/xml\/$', filepath):
	print("Error in filepath. Filepath should look like C:/.../jjvv(n)/xml")
	exit()

# Get various other parameters about what to change
copyright     = input("Enter the journal copyright (or \"default\" to leave it as is): ")
textSubs      = input("Autoformat common words? (y/n): ").lower()
addNewLine    = input("Add newlines before results, method, conclusions, etc.? (y/n): ").lower()
boldHeaders   = input("Make background, methods, results, etc. bold? (y/n): ").lower()
italicHeaders = "n" if boldHeaders.lower() == "y" else input("Make background, methods, results, etc. italicized? (y/n): ").lower()
speciesLinks  = input("Automatically attempt to insert species links? (y/n): ").lower()

# Define dictionaries to search for discrepancies
file_to_volume = dict()
file_to_number = dict()
file_to_year   = dict()

# Determine volume, year, issue, and number based on the path to the xml folder
(inf_volume, inf_number, inf_year, inf_journal_code) = extract_implicit_info(filepath)

print("\nPerforming preprocessing...\n------------------------")
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
			print("... Already processed " + filename)
			continue

		# Replace id="JJxxx" with appropriate values
		print("Processing " + filename + "...")
		lines[0] = set_article_id(filename, lines[0])

		# Fix redundant page numbers if possible
		lines[0] = fix_redundant_page_numbers(lines[0])

		# Add elements to our discrepancy dictionaries
		file_to_volume[filename] = getAttribute(lines[0], "volume")
		file_to_number[filename] = getAttribute(lines[0], "number")
		file_to_year[filename] = getAttribute(lines[0], "year")

		# Remove NA from authors if applicable
		remove_NA_Authors(lines)

		# Loop through remaining lines and replace values as appropriate
		for i in range(len(lines)):
			
			# Replace NA titles if applicable
			if lines[i].strip().startswith("<title"):
				lines[i] = remove_NA(lines[i], "title")

			# Replace NA keywords if applicable
			elif lines[i].strip().startswith("<keyword"):
				lines[i] = remove_NA(lines[i], "keyword")

			# Replace NA abstracts if applicable
			elif lines[i].strip().startswith("<abstract"):
				lines[i] = remove_NA(lines[i], "abstract")

			# Replace copyright if applicable
			if lines[i].strip().startswith("<copyright") and lines[i].strip().endswith("</copyright>"):
				if (copyright != "default"):
					lines[i] = "  <copyright>" + copyright + "</copyright>"
				else:
					lines[i] = "  <copyright>Copyright " + inf_year + " - " + lines[i][lines[i].find("<copyright>")+11:-12] + "</copyright>"

			# Remove superfluous commas from keywords if applicable
			elif lines[i].strip().startswith("<keyword") and lines[i].strip().endswith("</keyword>"):
				lines[i] = lines[i].replace(",;", ";")

			# Replace the id in the index tag with the appropriate value
			elif lines[i].strip().startswith("<index>") and lines[i].strip().endswith("</index>"):
				lines[i] = setIndexId(filename, lines[i])

		# Join list of lines on newline char
		body = "\n".join(lines)

		# Add linebreaks, italics, and bolds to common abstract sections
		if (addNewLine == "y"):
			if (boldHeaders == "y"):
				body = surroundHeaders(body, "<br/><b>", "<b>", "</b>")
			elif (italicHeaders == "y"):
				body = surroundHeaders(body, "<br/><i>", "<i>", "</i>")
			else:
				body = surroundHeaders(body, "<br/>", "", "")
		else:
			if (boldHeaders == "y"):
				body = surroundHeaders(body, "<b>", "<b>", "</b>")
			elif (italicHeaders == "y"):
				body = surroundHeaders(body, "<i>", "<i>", "</i>")

		# Perform common textual substitutions
		if (textSubs == "y"):
			body = commonTextSubs(body)

		# Add species links if the user requested it
		if speciesLinks:
			body = insertSpeciesLinks(body)

		# Write processed lines back to the file
		f = open(filepath + filename, "w")
		f.write(body)
		f.close()

print("Done preprocessing!\n")
print("Generating proofing file...\n------------------------")
write_problems_file(filepath + "../" + inf_journal_code + inf_volume + "(" + inf_number + ") Problems.txt", file_to_volume)
print("Proofing file generated!\n")

print("Performing Discrepancy Analysis...\n------------------------")

# Fix any problems with volume numbers (if so desired by user)
if existsDiscrepencies(file_to_volume, inf_volume):
	problems = printDiscrepancyReport(file_to_volume, "volume")
	if input("Would you like to automatically fix these problems? (y/n): ").lower() == "y":
		fix_discrepencies(problems, filepath, "volume", inf_volume)

# Fix any problems with issue numbers (if so desired by user)
if existsDiscrepencies(file_to_number, inf_number):
	problems = printDiscrepancyReport(file_to_number, "number")
	if input("Would you like to automatically fix these problems? (y/n): ").lower() == "y":
		fix_discrepencies(problems, filepath, "number", inf_number)

# Fix any problems with published year (if so desired by user)
if existsDiscrepencies(file_to_year, inf_year):
	problems = printDiscrepancyReport(file_to_year, "year")
	if input("Would you like to automatically fix these problems? (y/n): ").lower() == "y":
		fix_discrepencies(problems, filepath, "year", inf_year)

print("Discrepancies resolved!\nPlease proceed to manual processing of each file.")

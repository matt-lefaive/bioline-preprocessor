import os
import re

# Global variables
inf_year = ""
inf_volume = ""
inf_number = ""
inf_journal_code = ""

### FUNCTIONS ###
def setArticleId(filename, line):
	''' (str, str) -> str
		Sets id="jjxxx" to id=${filename} in the <article> line
	'''
	# First item in lines should be the <article> tag
	new_line = "<article id=\"" + filename[0:-4] + "\" "
	new_line += line[line.index("lang="):]
	return new_line

def removeNA(line, tag):
	'''(str) -> str
		Removes n/a and its derivatives from tag specified by *tag*.

		>>> removeNA("<title>NA</title>", "title")
		"<title></title>"
	'''
	derivatives = ["na", "n/a", "none"]
	for derivative in derivatives:
		if (line.lower().endswith(">" + derivative + "</" + tag + ">")):
			return line[0:line.index(">")+1] + "</" + tag + ">"
	# There were no na derivatives. Return the line as is.
	return line

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
					 "E. coli": "<i>E. coli</i>",
					 "E.coli": "<i>E.coli</i>",
					 "S. aureus": "<i>S. aureus</i>",
					 "&lt;i&gt;": "<i>",
					 "&lt;/i&gt;": "</i>",
					 " L-1": " L<sup>-1</sup>", # leading space prevents formatting IL-1 (interleukin)
					 "ha-1": "ha<sup>-1</sup>",
					 "\\\'": "\'",
					 "LC50": "LC<sub>50</sub>",
					 "LD50": "LD<sub>50</sub>",
					 "/m2": "/m<sup>2</sup>"}

	for key in substitutions.keys():
		text = text.replace(key, substitutions[key])

	return text

def surroundHeaders(text, front, special_front, back):
	'''(str, str, str, str) -> str
		For a header h in common_headers, it is replaced by the sequence (special_)front+header+back, thereby
		automatically applying bold, italics, or linebreaks to the different sections within an abstract.
	'''
	common_headers = ["background:", "Background:", "Background\n",
					  "materials and methods:", "Materials and methods:",
					  "methods:", "method:", "Methods:", "Method:", "Methods\n", "Methodology:",
					  "result:", "results:", "Result:", "Results:", "Results\n",
					  "conclusion:", "conclusions:", "Conclusion:", "Conclusions:", "Conclusions\n",
					  "Introduction:", "Introduction\n",
					  "Objective:", "Objectives:",
					  "Discussion:", "Discussions:",
					  "Antecedente:", "Objetivo:", "M&#233;todos:", "Resultados:", "Conclusiones:",
					  ]
	for header in common_headers:
		if header.lower() not in {"background:", "background\n", "antecedente:", "introduction:", "introduction"}:
			text = text.replace(header, "\n" + front + header + back)
		else:
			text = text.replace(header, "\n" + special_front + header + back)
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
	for key in d.keys():
		if d[key] != expected:
			return True
	return False

def printDiscrepancyReport(d, disc_type):
	print("---------------------------------------")
	print("Journal " + disc_type + " discrepancies:")
	print("---------------------------------------")
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

def updateIndexYear(line):
	spaces = 0;
	while(line[spaces] == ' '):
		spaces += 1

	tokens = line[spaces:].split(" ")

	# The first token, <index>YYYY, is the one we need to change
	tokens[0] = "<index>" + inf_year

	# Return the line put back together
	return spaces * " " + " ".join(tokens)

def fixRedundantPageNumbers(line):
	pages = getAttribute(line, "pages")
	if (re.match(r'(\d+)-\1', pages)):
		line = updateAttribute("pages", pages[:pages.index("-")], line)
	return line

def fixDiscrepencies(files, directory_path, disc_type, expected):
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
			lines[-3] = updateIndexYear(lines[-3])

		# Rejoin all lines on newline and write to file
		body = "\n".join(lines)
		f = open(directory_path + filename, "w")
		f.write(body)
		f.close()
	print("")

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
if not re.match(r'.*\/[a-z]{2}\d+\(\d+\)\/xml\/$', filepath):
	print("Error in filepath. Filepath should look like C:/.../jjvv(n)/xml")
	exit()

# Get various other parameters about what to change
copyright = input("Enter the journal copyright (or 'default' to leave it as is): ")
textSubs = input("Autoformat common words? (y/n): ").lower()
addNewLine = input("Add newlines before results, method, conclusions, etc.? (y/n): ").lower()
boldHeaders = input("Make background, methods, results, etc. bold? (y/n): ").lower()
italicHeaders = "n" if boldHeaders.lower() == "y" else input("Make background, methods, results, etc. italicized? (y/n): ").lower()

# Define dictionaries to search for discrepancies
file_to_volume = dict()
file_to_number = dict()
file_to_year = dict()

# Implicitly determine year, issue, and number
(inf_volume, inf_number, inf_year, inf_journal_code) = extract_implicit_info(filepath)

print("\n------------------------\nPerforming preprocessing\n------------------------")
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
		print("... Processing " + filename)
		lines[0] = setArticleId(filename, lines[0])

		# Fix redundant page numbers if possible
		lines[0] = fixRedundantPageNumbers(lines[0])

		# Add elements to our discrepancy dictionaries
		file_to_volume[filename] = getAttribute(lines[0], "volume")
		file_to_number[filename] = getAttribute(lines[0], "number")
		file_to_year[filename] = getAttribute(lines[0], "year")

		# Loop through remaining lines and replace values as appropriate
		for i in range(len(lines)):
			
			# Replace NA titles if applicable
			if lines[i].strip().startswith("<title"):
				lines[i] = removeNA(lines[i], "title")

			# Replace NA keywords if applicable
			elif lines[i].strip().startswith("<keyword"):
				lines[i] = removeNA(lines[i], "keyword")

			# Replace NA abstracts if applicable
			elif lines[i].strip().startswith("<abstract"):
				lines[i] = removeNA(lines[i], "abstract")

			# Replace copyright if applicable
			if lines[i].strip().startswith("<copyright") and lines[i].strip().endswith("</copyright>"):
				if (copyright != "default"):
					lines[i] = "<copyright>" + copyright + "</copyright>"
				else:
					lines[i] = "<copyright>Copyright " + inf_year + " - " + lines[i][lines[i].find("<copyright>")+11:-12] + "</copyright>"

			# Remove superfluous commas from keywords if applicable
			elif lines[i].strip().startswith("<keyword") and lines[i].strip().endswith("</keyword>"):
				lines[i] = lines[i].replace(",;", ";")
				lines[i] = lines[i].replace(",<", ",")

			# Replace the id in the index tag with the appropriate value
			elif lines[i].strip().startswith("<index>") and lines[i].strip().endswith("</index>"):
				lines[i] = setIndexId(filename, lines[i])

		# Join list of lines on newline char
		body = "\n".join(lines)

		# Perform common textual substitutions
		if (textSubs == "y"):
			body = commonTextSubs(body)

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

		# Write processed lines back to the file
		f = open(filepath + filename, "w")
		f.write(body)
		f.close()

print("Done preprocessing!")
print("\n... Performing Discrepancy Analysis\n")

if existsDiscrepencies(file_to_volume, inf_volume):
	problems = printDiscrepancyReport(file_to_volume, "volume")
	if input("Would you like to automatically fix these problems? (y/n): ").lower() == "y":
		fixDiscrepencies(problems, filepath, "volume", inf_volume)

if existsDiscrepencies(file_to_number, inf_number):
	problems = printDiscrepancyReport(file_to_number, "number")
	if input("Would you like to automatically fix these problems? (y/n): ").lower() == "y":
		fixDiscrepencies(problems, filepath, "number", inf_number)

if existsDiscrepencies(file_to_year, inf_year):
	problems = printDiscrepancyReport(file_to_year, "year")
	if input("Would you like to automatically fix these problems? (y/n): ").lower() == "y":
		fixDiscrepencies(problems, filepath, "year", inf_year)

print("Discrepancies resolved!\nPlease proceed to manual processing of each file.")
input()

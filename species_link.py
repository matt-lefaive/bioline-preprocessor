import re

### Allows species links to be added to highlighted text (as a Sublime Text plugin)
try:
	import sublime
	import sublime_plugin

	class SpeciesLinkCommand(sublime_plugin.TextCommand):
		def run(self, edit):
			view = self.view
			for region in view.sel():
				if not region.empty():
					# If a species link was highlighted, revert it to it's non-linked form
					if is_species_link(view.substr(region)):
						view.replace(edit, region, remove_species_link(view.substr(region)))
					# Otherwise, a species was highlighted, so insert a link for it
					else:
						view.replace(edit, region, get_species_link(view.substr(region)))
except ImportError:
	pass
except NameError:
	pass


### MAIN SPECIES LINK CODE ###
def insertSpeciesLinks(text):
	# Read in common species
	f = open("./common_species.txt")
	species_list = f.read().splitlines()
	f.close()

	# Split text as we are only considering the first title to last abstract (main_body)
	pre_title = text[:text.index("<title")]
	main_body = text[text.index("<title"):text.rindex("<keyword")]
	post_abstract = text[text.rindex("<keyword"):]

	# Get indices for each different language body stuff (title-/abstract for each language)
	start_title_indices = [m.start() for m in re.finditer("<title", main_body)]
	end_abstract_indices = [m.start() for m in re.finditer("</abstract>", main_body)]

	# Move backwards from last language 
	for j in range(len(start_title_indices) - 1, -1, -1):
		# Clear lists cuz we're starting a new language
		linked_species = []
		short_forms = []

		# Chunk out the portion of the body we want to work on
		body = main_body[start_title_indices[j]:end_abstract_indices[j]]

		# Check the body for each individual species in common_species.txt
		for species in species_list:
			index = 0
			while index != -1:
				try:
					index = body[index:].lower().index(species.lower()) + index
				except ValueError:
					index = -1
				else: # Index was found
					front_body = body[:index]
					end_body = body[index + len(species):]

					# Get our species, case sensitive
					case_sens_species = body[index : index + len(species)]

					# If first occurrence of species add a link
					if species.lower() not in linked_species:
						insert = get_species_link(case_sens_species)
						linked_species += [species.lower(), species.split(" ")[0].lower()]

						# Add shortened genus form to list of short forms
						add_short_forms(short_forms, species.lower())


					# Not first occurrence, italicize if not in a species link tag and not italicized.
					else:
						if not in_sp_tag(body, index) and not is_italicized(body, index):
							insert = "<i>" + case_sens_species + "</i>"
						else:
							insert = case_sens_species

					# Insert either a species link or italicized species name
					index = index + len(insert)
					body = front_body + insert + end_body

		# Go through body once more and italicize short forms for linked species
		for sf in short_forms:
			body = body.replace(sf, "<i>" + sf + "</i>")
	
		# Rejoin body to end of main_body
		main_body = main_body[:start_title_indices[j]] + body + main_body[end_abstract_indices[j]:]


	# Rejoin all three parts of the article
	return pre_title + main_body + post_abstract
					

def in_sp_tag(body, index):
	if (body[:index].endswith("<sp>")):
		return True
	elif (body[:index].endswith("genus=\"")):
		return True
	else:
		return False

def is_italicized(body, index):
	return body[:index].endswith("<i>")

def is_species_link(text):
	return re.match(r'^<taxon genus=".*" species=".*" sub-prefix=".*" sub-species=".*">.*<\/taxon>$', text)

def remove_species_link(text):
	text = re.sub(r'<taxon genus=".*" species=".*" sub-prefix=".*" sub-species=".*">', '', text)
	text = re.sub(r'<\/?sp>', '', text)
	text = text.replace("</taxon>", "")
	return text

def add_short_forms(short_forms, species):
	components = species.split(" ")
	if len(components) > 1:
		short_forms += [components[0][0] + ". " + " ".join(components[1:])]

def get_species_link(link):
	#return "sp(" + species + ")"

	tokens = link.split()

	# Single genus name
	if len(tokens) == 1:
		link = genus_spp(tokens)

	# Genus and subspecies
	elif len(tokens) == 2:
		if (tokens[1] == "sp." or tokens[1] == "spp."):
			link = genus_spp(tokens)
		else: # Note, judgement is required in cases of abbreviated species names. They get caught here
			link = genus_species(tokens)

	# Genus species subspecies, or links including "sp." and it's derivatives
	elif len(tokens) == 3:
		if (tokens[1] not in {"sp.", "spp."}):
			if (is_parenthetical_match(tokens[0], tokens[1])):
				link = genus_PARgenusPAR_subspecies(tokens)
		
			elif (is_parenthetical(tokens[1])):
				link = genus_PARnamePAR_species(tokens)

			else:
				link = genus_species_subspecies(tokens)

	# Standard genus, species, subprefix, and subspecies all in one link
	elif len(tokens) == 4:
		link = genus_species_subprefix_subspecies(tokens)

	# Species name with multiple subprefixes
	elif len(tokens) > 4:
		link = genus_species_MERGE_subspecies(tokens)

	return link
				

def genus_spp(tokens):
	'''
	Input:  Brassica
	Output: <taxon genus="Brassica" species="" sub-prefix="" sub-species=""><sp>Brassica</sp></taxon>
	'''
	genus = tokens[0]
	link = "<taxon genus=\"" + genus + "\" species=\"\" sub-prefix=\"\" sub-species=\"\">"
	link += "<sp>" + genus + "</sp></taxon>"
	return link

def genus_species(tokens):
	'''
	Input:  Brassica oleracea
	Output: <taxon genus="Brassica" species="oleracea" sub-prefix="" sub-species=""><sp>Brassica</sp> <sp>oleracea</sp></taxon>
	'''
	(genus, species) = (tokens[0], tokens[1])
	link = "<taxon genus=\"" + genus + "\" species=\"" + species + "\" sub-prefix=\"\" sub-species=\"\">"
	link += "<sp>" + genus + "</sp> <sp>" + species + "</sp></taxon>"
	return link

def genus_species_subspecies(tokens):
	'''
	Input:  Brassica oleracea capitata
	Output: <taxon genus="Brassica" species="oleracea" sub-prefix="" sub-species="capitata"><sp>Brassica</sp> <sp>oleracea</sp> <sp>capitata</sp></taxon>
	'''
	return genus_species_subprefix_subspecies([tokens[0], tokens[1], "", tokens[2]]).replace("  ", " ")

def genus_species_subprefix_subspecies(tokens):
	'''
	Input:  Brassica oleracea var. capitata
	Output: <taxon genus="Brassica" species="oleracea" sub-prefix="var" sub-species="capitata"><sp>Brassica</sp> <sp>oleracea</sp> var <sp>capitata</sp></taxon>
	'''
	(genus, species, subprefix, subspecies) = (tokens[0], tokens[1], tokens[2], tokens[3])
	link = "<taxon genus=\"" + genus + "\" species=\"" + species + "\" sub-prefix=\"" + subprefix + "\" sub-species=\"" + subspecies + "\">"
	link += "<sp>" + genus + "</sp> <sp>" + species + "</sp> " + subprefix + " <sp>" + subspecies + "</sp></taxon>"
	return link

def genus_PARgenusPAR_subspecies(tokens):
	'''
	Input:  Brassica (brassica) oleracea
	Output: <taxon genus="Brassica" species="brassica" subprefix="" subspecies="oleracea"><sp>Brassica</sp> <sp>(brassica)</sp> <sp>oleracea</sp></taxon>
	'''
	genus = tokens[0]
	species = tokens[1][1:len(tokens[1])-1]
	subspecies = tokens[2]
	link = "<taxon genus=\"" + genus + "\" species=\"" + species + "\" sub-prefix=\"\" sub-species=\"" + subspecies + "\">"
	link += "<sp>" + genus + "</sp> <sp>" + tokens[1] + "</sp> <sp>" + subspecies + "</sp></taxon>"
	return link

def genus_PARnamePAR_species(tokens):
	'''
	Input:  Brassica (cabbage) oleracea
	Output: <taxon genus="Brassica" species="oleracea" sub-prefix="" sub-species=""><sp>Brassica</sp> (cabbage) <sp>oleracea</sp></taxon>
	'''
	(genus, name, species) = tokens[0:3]
	link = "<taxon genus=\"" + genus + "\" species=\"" + species + "\" sub-prefix=\"\" sub-species=\"\">"
	link += "<sp>" + genus + "</sp> " + name + " <sp>" + species + "</sp></taxon>"
	return link

def genus_species_MERGE_subspecies(tokens):
	'''
	Input:  Brassica oleracea var. nov. capitata
	Output: <taxon genus="Brassica" species="oleracea" sub-prefix="" sub-species="capitata"><sp>Brassica</sp> <sp>oleracea</sp> var. nov. <sp>capitata</sp></taxon>
	'''
	genus = tokens[0]
	species = tokens[1]
	merge = ' '.join(tokens[2:-1])
	subspecies = tokens[-1]
	link = "<taxon genus=\"" + genus + "\" species=\"" + species + "\" sub-prefix=\"\" sub-species=\"" + subspecies + "\">"
	link += "<sp>" + genus + "</sp> <sp>" + species + "</sp> " + merge + " <sp>" + subspecies + "</sp></taxon>"
	return link

def is_parenthetical_match(s1, s2):
	'''
	Returns True if s2 = ^s1$, where ^ and $ can be any character. False otherwise. Comparison is case-insensitive.

	>>> is_parenthetical_match("ham", "(ham)")
	True
	'''
	if len(s2) != len(s1) + 2:
		return False
	else:
		return s1.lower() == s2[1:len(s2)-1].lower()

def is_parenthetical(s):
	'''
	Returns True if s starts with ( and ends with )
	'''
	if len(s) < 2:
		return False
	else:
		return s[0] == "(" and s[-1] == ")"

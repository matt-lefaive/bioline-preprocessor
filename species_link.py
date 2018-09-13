import re


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
						insert = getSpeciesLink(case_sens_species)
						linked_species += [species.lower(), species.split(" ")[0].lower()]

						# Add shortened genus form to list of short forms
						addShortForms(short_forms, species.lower())


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

def alreadyLinked(linked_species, species):
	for l in linked_species:
		if species.lower() == l.lower() or species in short_forms:
			return True
	return False

def addShortForms(short_forms, species):
	components = species.split(" ")
	if len(components) > 1:
		short_forms += [components[0][0] + ". " + " ".join(components[1:])]

def getSpeciesLink(link):
	#return "sp(" + species + ")"

	tokens = link.split()

	if len(tokens) == 1:
		link = genus_spp(tokens)
	elif len(tokens) == 2:
		if (tokens[1] == "sp." or tokens[1] == "spp."):
			link = genus_spp(tokens)
		else: # Note, judgement is required in cases of abbreviated species names. They get caught here
			link = genus_species(tokens)
	elif len(tokens) == 3:
		if (tokens[1] not in {"sp.", "spp."}):
			if (is_parenthetical_match(tokens[0], tokens[1])):
				link = genus_PARgenusPAR_subspecies(tokens)
			elif (is_parenthetical(tokens[1])):
				link = genus_PARnamePAR_species(tokens)
	elif len(tokens) == 4:
		link = genus_species_varXcv_subspecies(tokens)
	elif len(tokens) > 4:
		link = genus_species_MERGE_subspecies(tokens)

	return link
				

# 2 Tokens
def genus_spp(tokens):
	genus = tokens[0]
	link = "<taxon genus=\"" + genus + "\" species=\"\" subprefix=\"\" subspecies=\"\">"
	link += "<sp>" + genus + "</sp></taxon>"
	return link

def genus_species(tokens):
	genus = tokens[0]
	species = tokens[1]
	link = "<taxon genus=\"" + genus + "\" species=\"" + species + "\" subprefix=\"\" subspecies=\"\">"
	link += "<sp>" + genus + "</sp> <sp>" + species + "</sp></taxon>"
	return link

def genus_species_varXcv_subspecies(tokens):
	genus = tokens[0]
	species = tokens[1]
	subprefix = tokens[2]
	subspecies = tokens[3]
	link = "<taxon genus=\"" + genus + "\" species=\"" + species + "\" subprefix=\"" + subprefix + "\" subspecies=\"" + subspecies + "\">"
	link += "<sp>" + genus + "</sp> <sp>" + species + "</sp> " + subprefix + " <sp>" + subspecies + "</sp></taxon>"
	return link

def genus_PARgenusPAR_subspecies(tokens):
	genus = tokens[0]
	species = tokens[1][1:len(tokens[1])-1]
	subspecies = tokens[2]
	link = "<taxon genus=\"" + genus + "\" species=\"" + species + "\" subprefix=\"\" subspecies=\"" + subspecies + "\">"
	link += "<sp>" + genus + "</sp> <sp>" + tokens[1] + "</sp> <sp>" + subspecies + "</sp></taxon>"
	return link

def genus_PARnamePAR_species(tokens):
	genus = tokens[0]
	name = tokens[1]
	species = tokens[2]
	link = "<taxon genus=\"" + genus + "\" species=\"" + species + "\" subprefix=\"\" subspecies=\"\">"
	link += "<sp>" + genus + "</sp> " + tokens[1] + " <sp>" + species + "</sp></taxon>"
	return link

def genus_species_MERGE_subspecies(tokens):
	genus = tokens[0]
	species = tokens[1]
	merge = ' '.join(tokens[2:-1])
	subspecies = tokens[-1]
	link = "<taxon genus=\"" + genus + "\" species=\"" + species + "\" subprefix=\"\" subspecies=\"" + subspecies + "\">"
	link += "<sp>" + genus + "</sp> <sp>" + species + "</sp> " + merge + " <sp>" + subspecies + "</sp></taxon>"
	return link

def is_parenthetical_match(s1, s2):
	if len(s2) != len(s1) + 2:
		return False
	else:
		return s1.lower() == s2[1:len(s2)-1].lower()

def is_parenthetical(s):
	if len(s) < 2:
		return False
	else:
		return s[0] == "(" and s[-1] == ")"
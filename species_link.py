import re

# Allows species links to be added to highlighted text
# (as a Sublime Text plugin)
try:
    import sublime
    import sublime_plugin

    class SpeciesLinkCommand(sublime_plugin.TextCommand):
        def run(self, edit):
            view = self.view
            for region in view.sel():
                if not region.empty():
                    # If a species link was highlighted, revert it to it's
                    # non-linked form
                    if is_species_link(view.substr(region)):
                        view.replace(edit, region, remove_species_link(view.substr(region)))
                    # Otherwise, a species was highlighted, so insert a link
                    # for it
                    else:
                        view.replace(edit, region, get_species_link(view.substr(region)))
except ImportError:
    pass
except NameError:
    pass


# MAIN SPECIES LINK CODE #
def insertSpeciesLinks(text):
    """
    (str) -> str
    Inserts species links into text where possible, and returns the new text.
    Requires text to match the following regex:
    .*<title.*</title>.*<abstract.*</abstract>.*<keyword.*</keyword>

    :param text: the text to insert species links in
    :returns: text with species links inserted
    """

    # Read in common species
    f = open("./common_species.txt")
    species_list = f.read().splitlines()
    f.close()

    # Split text as we are only considering the first title to last abstract
    # (main_body)
    pre_title = text[:text.index("<title")]
    main_body = text[text.index("<title"):text.rindex("<keyword")]
    post_abstract = text[text.rindex("<keyword"):]

    # Get indices for each different language body stuff (title-/abstract for
    # each language)
    start_title_indices = [m.start() for m in re.finditer("<title", main_body)]
    end_abstract_indices = [m.start() for m in re.finditer("</abstract>",
                                                           main_body)]

    # Move backwards from last language
    for j in range(len(start_title_indices) - 1, -1, -1):
        # Clear lists and dicts cuz we're starting a new language
        short_forms = []
        genus_to_species = dict()

        # Chunk out the portion of the body we want to work on
        body = main_body[start_title_indices[j]:end_abstract_indices[j]]

        # PART ONE

        # Check the body for each individual species in common_species.txt
        for species in species_list:  
            # EACH SPECIES MUST MATCH '.* .*'
            if not re.search(r'.* .*', species):
                print("HEY")
                continue

            matches = []
            short_matches = []
            genus_matches = []
            shortform = ''
            parts = species.split(' ')

            # Fill in the genus_to_species dict
            if parts[0] not in genus_to_species:
                genus_to_species[parts[0]] = []
            if parts[1] not in genus_to_species[parts[0]]:
                genus_to_species[parts[0]].append(parts[1])

            # Get indices of all occurences of full species name
            shortform = f'''{parts[0][0]}. {' '.join(parts[1:])}'''
            for match in re.finditer(re.escape(parts[0]) + r' *\n? *' + re.escape(parts[1]), body, re.IGNORECASE):
                matches.append(match.span())

            # Replace all full occurences with a standard '{genus} {species}' format.
            # Italicize all but the first occurence
            for i in range(len(matches) -1, -1, -1):
                spec = remove_blank_chars(body[matches[i][0]: matches[i][1]])
                if (i == 0):
                    body = body[:matches[i][0]] + get_species_link(spec) + body[matches[i][1]:]
                else:
                    body = body[:matches[i][0]] + f'<i>{spec}</i>' + body[matches[i][1]:]

            # Get indices of all occurences of short form of species name
            short_parts = shortform.split(' ')
            if len(short_parts) > 1:
                for match in re.finditer(re.escape(short_parts[0]) + r' *\n? *' + re.escape(' '.join(parts[1:])), body, re.IGNORECASE):
                    short_matches.append(match.span())

            # Replace all short form occurences with standard 'C. {species}' format.
            # Italicize all occurences
            for i in range(len(short_matches) -1, -1, -1):
                spec = remove_blank_chars(body[short_matches[i][0]: short_matches[i][1]])
                body = body[:short_matches[i][0]] + f'<i>{spec}</i>' + body[short_matches[i][1]:]

        # PART TWO

        # For each linked species, if it's genus occurs on its own before any links of the same
        # genus (but different species), add a species link

        # Find all species links for a given genus
        for genus in genus_to_species.keys():

            #matches = []
            #for match in re.finditer(r'''<taxon genus="''' + re.escape(genus) + '\"', body, re.IGNORECASE):
            #    matches.append(match.span())

            # The following regex matches species links for any species of a given genus currently processed
            master_reg = r'''<taxon genus="''' + re.escape(genus) + r'''" species="('''
            for i in range(len(genus_to_species[genus])):
                if i < len(genus_to_species[genus]) - 1:
                    master_reg += re.escape(f'{genus_to_species[genus][i]}') + '|'
                else:
                    master_reg += re.escape(f'{genus_to_species[genus][i]}') + ''')"'''
            
            # Find all links that match said expression
            matches = []
            for match in re.finditer(master_reg, body, re.IGNORECASE):
                matches.append(match.span())

            if len(matches) > 0:
                # Find first occurence of genus (on its own)
                first_genus = re.search(re.escape(genus), body[:matches[0][0]], re.IGNORECASE)
                if first_genus is not None:
                    first_genus = first_genus.span()
                
                    # if first occurrence of genus preceedes 1st species link for it, add another link
                    if (first_genus[1] < matches[0][0]):
                        body = body[:first_genus[0]] + get_species_link(body[first_genus[0]:first_genus[1]]) + body[first_genus[1]:]

                #Italicize subsequent occurrences of just the genus
                matches = []
                for match in re.finditer(r' ' + re.escape(genus) + r'[ \n\.,\?\!]', body, re.IGNORECASE):
                    matches.append(match.span())

                for i in range(len(matches) -1, -1, -1):
                                                           #+1 and -1 to trim off surrounding chars
                    body = body[:matches[i][0]] + ' <i>' + body[matches[i][0]+1:matches[i][1]-1] + "</i>" + body[matches[i][1]-1] + body[matches[i][1]:] 

        # Rejoin body to end of main_body
        main_body = main_body[:start_title_indices[j]] + body + main_body[end_abstract_indices[j]:]

    # Rejoin all three parts of the article
    return pre_title + main_body + post_abstract


def is_species_link(text):
    """
    (str) -> bool
    Returns True if text is a species link, False otherwise

    :param text: the text to check
    :returns: True if text is a species link
    """

    return re.match(r'''^<taxon genus=".*" species=".*" sub-prefix=
        ".*" sub-species=".*">.*<\/taxon>$''', text)


def remove_blank_chars(text):
    """
    (str) -> str
    Removes superfluous blank characters from text, leaving at most
    a single space behind where there was more than one (space or newline)
    
    >>> remove_blank_chars('Happy    \n   \n Birthday')
    "Happy Birthday"

    :param text: text from which to remove superfluous blanks
    :returns: text with superfluous blanks removed
    """
    text = text.replace('\n', ' ')
    while '  ' in text:
        text = text.replace('  ', ' ')
    return text


def remove_species_link(text):
    """
    (str) -> str
    Removes any species links in text and replaces them with the species name.
    The resulting text contains just the text within the <taxon></taxon> tags,
    sans <sp></sp> tags.
    N.B.: Only used in the plugin

    :param text: text to remove species links from
    :returns: text with species links removed
    """

    text = re.sub(r'''<taxon genus=".*" species=".*" sub-prefix=
        ".*" sub-species=".*">''', '', text)
    text = re.sub(r'<\/?sp>', '', text)
    text = text.replace("</taxon>", "")
    return text



def get_species_link(link):
    """
    (str) -> str
    Given text link containing (ideally) just a species name, returns a species
    link for said species (if possible). If not possible, simply returns link
    unaltered.

    :param link: the text to convert to a species link
    :returns: link converted to a species link
    """

    tokens = link.split()

    # Single genus name
    if len(tokens) == 1:
        link = genus_spp(tokens)

    # Genus and subspecies
    elif len(tokens) == 2:
        if (tokens[1] == "sp." or tokens[1] == "spp."):
            link = genus_spp(tokens)
        else:
            # Note, judgement is required in cases of abbreviated species
            # names. They get caught here
            link = genus_species(tokens)

    # Genus species subspecies, or links including "sp." and it's derivatives
    elif len(tokens) == 3:
        if (tokens[1] not in {"sp.", "spp."}):
            if (is_enclosed_match(tokens[0], tokens[1])):
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


def is_enclosed_match(s1, s2):
    """
    (str, str) -> bool
    Returns True if s2 = @s1%, where @ and % can be any character, False
    otherwise. Comparison is case-insensitive.

    >>> is_enclosed_match("ham", "(ham)")
    True

    :param s1: 1st string to compare
    :param s2: 2nd string to compare (possible enclosed match)
    :returns: True if s2 is an enclosed match of s1
    """

    if len(s2) != len(s1) + 2:
        return False
    else:
        return s1.lower() == s2[1:len(s2)-1].lower()


def is_parenthetical(s):
    """
    (str) -> bool
    Returns True if s starts with '(' and ends with ')'
    """
    if len(s) < 2:
        return False
    else:
        return s[0] == "(" and s[-1] == ")"




# The following methods all convert a species name into a species link. The
# reST style of docstrings is not used here in favour of this ad-hoc method
# that better captures each type of link.

def genus_spp(tokens):
    """
    Input:  Brassica
    Output: <taxon genus="Brassica" species="" sub-prefix="" sub-species="">
            <sp>Brassica</sp></taxon>
    """
    genus = tokens[0]
    return f'''<taxon genus="{genus}" species="" sub-prefix="", sub-species="">
    <sp>{genus}</sp></taxon>'''


def genus_species(tokens):
    """
    Input:  Brassica oleracea
    Output: <taxon genus="Brassica" species="oleracea" sub-prefix=""
    sub-species=""><sp>Brassica</sp> <sp>oleracea</sp></taxon>
    """
    (genus, species) = (tokens[0], tokens[1])
    return f'''<taxon genus="{genus}" species="{species}" sub-prefix="", sub-species="">
    <sp>{genus}</sp> <sp>{species}</sp></taxon>'''


def genus_species_subspecies(tokens):
    """
    Input:  Brassica oleracea capitata
    Output: <taxon genus="Brassica" species="oleracea" sub-prefix=""
            sub-species="capitata"><sp>Brassica</sp> <sp>oleracea</sp>
            <sp>capitata</sp></taxon>
    """
    return genus_species_subprefix_subspecies([tokens[0], tokens[1], "", tokens[2]]).replace("  ", " ")


def genus_species_subprefix_subspecies(tokens):
    """
    Input:  Brassica oleracea var. capitata
    Output: <taxon genus="Brassica" species="oleracea" sub-prefix="var"
            sub-species="capitata"><sp>Brassica</sp> <sp>oleracea</sp> var
                <sp>capitata</sp></taxon>
    """
    (genus, species, subprefix, subspecies) = (tokens[0], tokens[1], tokens[2], tokens[3])
    return f'''<taxon genus="{genus}" species="{species}" sub-prefix="{subprefix}", sub-species="{subspecies}">
    <sp>{genus}</sp> <sp>{species}</sp> {subprefix} <sp>{subspecies}</sp></taxon>'''


def genus_PARgenusPAR_subspecies(tokens):
    """
    Input:  Brassica (brassica) oleracea
    Output: <taxon genus="Brassica" species="brassica" subprefix=""
            subspecies="oleracea"><sp>Brassica</sp> <sp>(brassica)</sp>
            <sp>oleracea</sp></taxon>
    """
    genus = tokens[0]
    species = tokens[1][1:len(tokens[1])-1]
    subspecies = tokens[2]
    return f'''<taxon genus="{genus}" species="{species}" sub-prefix="", sub-species="{subspecies}">
    <sp>{genus}</sp> <sp>{tokens[1]}</sp> <sp>{subspecies}</sp></taxon>'''


def genus_PARnamePAR_species(tokens):
    """
    Input:  Brassica (cabbage) oleracea
    Output: <taxon genus="Brassica" species="oleracea" sub-prefix=""
            sub-species=""><sp>Brassica</sp> (cabbage) <sp>oleracea</sp>
            </taxon>
    """
    (genus, name, species) = tokens[0:3]
    return f'''<taxon genus="{genus}" species="{species}" sub-prefix="", sub-species="">
    <sp>{genus}</sp> {name} <sp>{species}</sp></taxon>'''


def genus_species_MERGE_subspecies(tokens):
    """
    Input:  Brassica oleracea var. nov. capitata
    Output: <taxon genus="Brassica" species="oleracea" sub-prefix=""
            sub-species="capitata"><sp>Brassica</sp> <sp>oleracea</sp> var.
            nov. <sp>capitata</sp></taxon>
    """
    genus = tokens[0]
    species = tokens[1]
    merge = ' '.join(tokens[2:-1])
    subspecies = tokens[-1]
    return f'''<taxon genus="{genus}" species="{species}" sub-prefix="", sub-species="{subspecies}">
    <sp>{genus}</sp> <sp>{species}</sp> {merge} <sp>{subspecies}</sp></taxon>'''


# Sample XML article for testing
if __name__ == '__main__':
    article = '''    <article >
        <title lang="en">Citrus limonum</title>
        <abstract lang="en">This is a fake article about Citrus. There are two varieties
        of Citrus, namely citrus medica and citrus limonum. A variety of people try to use
        citrus like c. limonum and C. 
        medica to treat wounds.
        </abstract>
        <keyword lang="en"></keyword>
        <index></index>
        <copyright></copyright>
    </article>
    '''
    
    print(insertSpeciesLinks(article))
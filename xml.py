import re

class XMLError(Exception):
	pass


class xml:

	@staticmethod
	def get_attributes(text):
		if not xml.is_valid(text):
			return None

		# Ignore the inner XML and closing tag
		text = re.sub(r'^\s*<([\w-]+) (\w+=\".*\")?>.*</\1>$', r'\2', text)

		# Parse out each match and add them to a dict
		matches = dict()
		for match in re.findall(r'[\w]+-?[\w]+=\"[\w\d\s\.\-_]*\"', text):
			tokens = match.split('=')
			key = tokens[0]
			value = ''.join(tokens[-1:]).strip('\'\"')
			matches[key] = value

		return matches


	@staticmethod
	def get_attribute(attribute, text):
		"""
		(str, str) -> str
		Returns the value of a given attribute in a line of text (where text is
		enclosed in valid xml tags of the form <X></X>)
	
		>>> get_attribute('<article year="1997"></article>', 'year')
		"1997"
	
		:param text: text from which to extract the value of an attribute
		:param attribute: the attribute who's value we're extracting
		:returns: the value of attribute
		"""
		
		try:
			return xml.get_attributes(text)[attribute]
		except KeyError:
			return None


	@staticmethod
	def set_attribute(attribute, new_val, text):
		"""
		(str, str, str) -> str
		Replaces the value of attribute in (XML) text with new_val
	
		>>> update_attribute('id', '222', '<a id=\"111\"></a>')
		"<a id="222"></a>
	
		:param attribute: the attribute who's value is to be updated
		:param new_val: the new value for attribute
		:param text: the text containing attribute
		:returns: text with value of attribute set to new_val
		"""

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


	@staticmethod
	def get_tag(text):
		if not xml.is_valid(text):
			return None

		match = re.search(r'^\s*<(\w+)( \w+=\".*\")?>', text)
		return None if match == None else match.group(1)

	@staticmethod
	def get_inner_xml(text):
		if not xml.is_valid(text):
			return None

		# <abstract> is the only Bioline xml tag that exceeds one line
		return re.search(r'^<(\w+)( \w+=\".*\")?>(.*)</\1>$', text).group(3)


	@staticmethod
	def opens_with(tag, text):
		return text.strip().startswith('<' + tag)

	@staticmethod
	def set_inner_xml(text, inner):
		if not xml.is_valid(text):
			return None

		return re.sub(r'^(\s*)<(\w+)( \w+=\".*\")?>(.*)</\1>$', r'\1<\2\3>' + inner + r'</\2>', text)


	@staticmethod
	def is_valid(text):
		"""
		Returns true iff text starts and ends with equivalent opening
		and closing tags

		>>> is_valid("<title>Hello world</title>")
		True
		>>> is_valid("<title>Cats are cool")
		False

		:param text: the text to check validity of
		:returns: true if text is enclosed in tags
		"""
		return True
		#return bool(re.match(r'^<(\w+)( \w+=\".*\")?>.*</\1>$', text.strip()))


	@staticmethod
	def remove_NA(text):
		derivatives = ["na", "n/a", "none"]
		for derivative in derivatives:
			match = re.search(re.escape(derivative) + r'</(title|abstract|keyword)>$', text, flags=re.IGNORECASE)
			if match != None:
				return text[0:text.index(">")+1] + "</" + match.group(1) + ">"
		# There were no na derivatives. Return the text as is.
		return text


if __name__ == "__main__":
	print(xml.get_attributes('''<article id="ocxxx" lang="en" content="pdf" volume="112" number="10" month="10" year="2017" pages="692-697" version="xml" accepted-date="" bioline-date="20190510" type="AA">'''))

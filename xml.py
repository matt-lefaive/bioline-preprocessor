class xml:
	def get_attribute(text, attribute):
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
	
		start = attribute + "=\""
		if start not in text:
			return ""
		text = text[text.index(start) + len(start):]
		return text[:text.index("\"")]
	

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
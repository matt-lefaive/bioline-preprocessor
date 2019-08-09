# -*- coding: utf-8 -*-

import sublime, sublime_plugin, re

class EncodeSpecialCharsCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		view = self.view
		for region in view.sel():
			text = view.substr(region)
			text = encode_special(text)
			view.replace(edit, region, text)

def encode_special(text):
	#text = text.replace(u'', '')

	

	# Miscellaneous Symbols
	text = text.replace(u'°', '&#176;'); text = text.replace('\\degrees','&#176;'); text = text.replace('\\degree', '&#176;')
	text = text.replace(u'¿', '&#191;')
	text = text.replace(u'‘', '&#2037;')
	text = text.replace(u'®', '&#174;')
	text = text.replace(u'©', '&#169;')
	text = text.replace(u'€', '&#128;')
	text = text.replace(u'£', '&#163;')
	text = text.replace(u'¥', '&#165;')

	# Quotations and Apostrophes
	text = text.replace(u'‘', '&#039;')
	text = text.replace(u'“', '&#034;')
	text = text.replace(u'‘', '&#145;')
	text = text.replace(u'’', '&#146;')
	text = text.replace(u'“', '&#147;')
	text = text.replace(u'”', '&#148;')

	# Greek Uppercase
	text = text.replace(u'Δ', '&#916;'); text = text.replace('\\Delta', '&#916;')
	text = text.replace(u'Ω', '&#937;'); text = text.replace('\\Omega', '&#937;'); text = text.replace('\\ohm', '&#937;')

	# Greek Lowercase



	# Large dictionary of text substitutions and shortcuts
	substitutions = {
		# Accented Latin lowercase
		(u'à'): '&#224;',
		(u'á', '\\aaigu'): '&#225;',
		(u'â'): '&#226;',
		(u'ã'): '&#227;',
		(u'ä'): '&#228;',
		(u'å'): '&#229;',
		(u'æ'): '&#230;',
		(u'ç'): '&#231;',
		(u'è'): '&#232;',
		(u'é', '\\eaigu'): '&#233;',
		(u'ê'): '&#234;',
		(u'ë'): '&#235;',
		(u'ì'): '&#236;',
		(u'í', '\\iaigu'): '&#237;',
		(u'î'): '&#238;',
		(u'ï'): '&#239;',
		(u'ñ'): '&#241;',
		(u'ò'): '&#242;',
		(u'ó', '\\oaigu'): '&#243;',
		(u'ô'): '&#244;',
		(u'õ'): '&#245;',
		(u'ö'): '&#246;',
		(u'ø'): '&#248;',
		(u'š'): '&#154;',
		(u'ù'): '&#249;',
		(u'ú', '\\uaigu'): '&#250;',
		(u'û'): '&#251;',
		(u'ü'): '&#252;',
		(u'ÿ'): '&#255;',
		(u'ý', '\\yaigu'): '&#253;',
		(u'ž'): '&#158;',

		# Accented Latin uppercase
		(u'À'): '&#192;',
		(u'Ã'): '&#195;',
		(u'Ç'): '&#199;',

		# Greek lowercase
		(u'α', '\\alpha'): '&#945;',
		(u'β', '\\beta'): '&#946;',
		(u'γ', '\\gamma'): '&#947;',
		(u'δ', '\\delta'): '&#948;',
		(u'ε', '\\epsilon'): '&#949;',
		(u'λ', '\\lambda'): '&#955;',
		(u'µ', '\\mu', '\\micro'): '&#181;',
		(u'π', '\\pi'): '&#960;',
		(u'σ', '\\sigma'): '&#963;',
		(u'ω', '\\omega'): '&#969;',

		# Intellectual property
		(u'®', '\\textregistered'): '&#174;',

		# International Phonetic Alphabet
		(u'ɪ',): '&#618;',

		# Math
		(u'≤', '\\leq'): '&#8804;',
		(u'≥', '\\geq'): '&#8805;',
		(u'×', '\\times'): '&#215;',
		(u'±', '\\plusorminus', '\\plusminus/'): '&#177;',

		# Whitespace
		('\\emspace',): '&#8195;',

		# Personal text macros 
		('\\authors',): '''<authors seq="">\n\t\t<lastname></lastname>\n\t\t<firstname></firstname>\n\t</authors>''' 
	} 

	for substitution_set in substitutions.keys():
		for sub in substitution_set:
			text = text.replace(sub, substitutions[substitution_set])

	return text
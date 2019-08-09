import re
import sublime
import sublime_plugin

class SwapNamesCommand(sublime_plugin.TextCommand):
	""" This Sublime Text plugin will attempt to swap first and last
	names for all authors in selected <author> tags. It will also
	attempt to place articles/determiners in the correct spot. For
	example, running the plugin on:

		<author seq="1">Mohamed, el-Gamdi</author>

	will yield:

		<author seq="1">Gamdi, Mohamed el-</author>
	"""

	def run(self, edit):
		""" Function that's called when the plugin is invoked """
		view = self.view

		for region in view.sel():
			if not region.empty():
				text = view.substr(region)

				# If the user highlighted non-<author> tags, don't do anything
				if not self.valid_author_tags(text):
					print('Selection must only contain <author> tags')
					continue

				authors = text.split('\n')

				new_tags = []

				for author in authors:
					(lastname, firsname) = (None, None)
					if ',' in author:
						(lastname, firstname) = author.split(',')
					else: 
						new_tags.append(author)
						continue
						#(lastname, firstname) = (author, '')

					# Extract the sequence number
					seq = re.match(r'\s*<author seq="(\d+)">', lastname).group(1)

					# Trim the extra XML off the last and first name
					lastname = re.sub(r'\s*</?author ?(seq="(\d+)")?>', '', lastname).strip()
					firstname = firstname.replace('</author>', '').strip()

					# Join the last and first names into [first last] format, then re-split them
					name = lastname + ' ' + firstname

					# Search for some common articles upon which to split
					articles = re.findall(r'( de | da | el-)', name, flags=re.IGNORECASE)
					if articles != None and len(articles) > 0:
						# Find occurrence of last article in name
						i = name.rfind(articles[-1])
						tag = ('  <author seq="%s">' % seq) + name[i + len(articles[-1]):].strip() + ', ' + name[:i + len(articles[-1])].strip() + '</author>'
						new_tags.append(tag)
					else:
						# Take last token by default to be the last name, the rest is a first name
						comps = name.split(' ')
						lastname = comps[-1].strip()
						firstname = ' '.join(comps[:-1]).strip()
						tag = ('  <author seq="%s">' % seq) + lastname + ', ' + firstname + '</author>'
						new_tags.append(tag)

				# Make replacement
				view.replace(edit, region, '\n'.join(new_tags))


	def valid_author_tags(self, text):
		""" Returns true iff text consists entirely of valid <author> tags """

		# First, remove extra whitespace and newlines
		text = re.sub(r'\t\n\r ', '', text)
		return re.match(r'^(\s*<author seq=\"(\d)+\">.*</author>[\n ]?)+$', text)
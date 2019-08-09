import re
import sublime
import sublime_plugin

class GenerateAuthorsTagsCommand(sublime_plugin.TextCommand):
	""" This Sublime Text plugin will insert <authors> tags beneath selected
	<author> tags. For example, running this plugin on:

		<author seq="1">Doe, Jane</author>

	will yield:

		<author seq="1">Doe, Jane</author>
		<authors seq="1">
			<lastname>Doe</lastname>
			<firstname>Jane</firstname>
		</authors>
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
						(lastname, firstname) = (author, '')

					# Extract the sequence number
					seq = re.match(r'\s*<author seq="(\d+)">', lastname).group(1)

					# Trim the extra XML off the last and first name
					lastname = re.sub(r'\s*</?author ?(seq="(\d+)")?>', '', lastname).strip()
					firstname = firstname.replace('</author>', '').strip()

					# Create short-hand first name tag if applicable
					firstname_tag = '<firstname/>' if firstname == '' else '<firstname>' + firstname + '</firstname>'
					lastname_tag = '<lastname>' + lastname + '</lastname>'

					# Create new <authors> tag to add later
					new_tags.append('  <authors seq="%s">\n    %s\n    %s\n  </authors>' % (seq, lastname_tag, firstname_tag))

				# Add the new <authors> tags below the selected <author> tags
				view.replace(edit, region, text + '\n' + '\n'.join(new_tags))


	def valid_author_tags(self, text):
		""" Returns true iff text consists entirely of valid <author> tags """

		# First, remove extra whitespace and newlines
		text = re.sub(r'\t\n\r ', '', text)
		return re.match(r'^(\s*<author seq=\"(\d)+\">.*</author>[\n ]?)+$', text)


__module_name__ = 'Name Colourer'
__module_version__ = '1.7'
__module_description__ = 'Colours names in chat messages using HexChat colouring'

import hexchat
import re

#colour codes
colours = [ 19, 20, 22, 24, 25, 26, 27, 28, 29 ]
#valid name pattern
name_start = "a-zA-Z_\-\[\]\\\^{}|`"
name_other = "0-9" + name_start

halt = False

def colour_names(word, word_eol, event, attrs):

	global halt

	if halt:
		return

	users = hexchat.get_list("users")
	message = word[1]

	for user in users:
		name = format_name(user.nick)
		if name_search(message, name):
			colour = get_colour(user.nick)
			message = re.sub(r'(?<![' + name_start + '])' + name + '(?![' + name_other + '])', '\003' + str(colour) + user.nick.replace('\\','\\\\') + '\003', message)
	word[1] = message
	halt = True
	hexchat.emit_print(event, *word)
	hexchat.command('gui color 2')
	halt = False
	return hexchat.EAT_ALL

#get colour for name
def get_colour(name):

	global colours
	raw = list(name)
	total = 0
	for ch in raw:
		total += ord(ch)
	return colours[total % len(colours)]

def name_search(text, name):

	global name_start, name_other
	m = re.search(r'(^|[^' + name_start + '])' + name + '($|[^' + name_other + '])', text)
	return m

#format the name text to avoid regex errors
def format_name(name):
	return re.escape(name) #name.replace('\\','\\\\').replace('|','\|').replace('^','\^').replace('[','\[').replace(']','\]')


#events to colour text
hooks = ["Your Message", "Channel Message", "Channel Msg Hilight", "Your Action", "Channel Action", "Channel Action Hilight"]

for hook in hooks:
	hexchat.hook_print_attrs(hook, colour_names, hook, hexchat.PRI_HIGH)

print("\00304" + __module_name__ + " successfully loaded.\003")

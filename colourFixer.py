__module_name__ = 'Colour Fixer'
__module_version__ = '0.8'
__module_description__ = 'Fixes Colour Removal'

import hexchat
import re

halt = False

#channel is nick
def test(word, word_eol, event, attrs):

    global halt
    if halt:
        return

    code = ""
    message = word[1]
    #message.replace("\x03","\\003")
    if "Hilight" in event:
        code = "19"
    elif "Your" in event:
        code = "30"
    message = re.sub(r'(?<=\x03)' + '(?![0-9])', code, message)
    word[1] = message
    halt = True
    hexchat.emit_print(event, *word)
    halt = False
    return hexchat.EAT_ALL

hooks = ["Your Message", "Channel Message", "Channel Msg Hilight", "Your Action", "Channel Action", "Channel Action Hilight"]

for hook in hooks:
	hexchat.hook_print_attrs(hook, test, hook, hexchat.PRI_LOW)

print("\00304" + __module_name__ + " successfully loaded.\003")

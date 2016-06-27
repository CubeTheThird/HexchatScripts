__module_name__ = 'Event Viewer'
__module_version__ = '0.1'
__module_description__ = 'Displays the name of triggered events'

import hexchat

def printer(word, word_eol, event, attrs):
    print(event)
    return hexchat.EAT_PLUGIN

hooks = ["Your Message", "Channel Message", "Channel Msg Hilight", "Your Action", "Channel Action", "Channel Action Hilight", "Join", "Change Nick", "Part", "Part with Reason", "Quit"]
for hook in hooks:
    hexchat.hook_print_attrs(hook, printer, hook, hexchat.PRI_HIGH)
print("\00304" + __module_name__ + " successfully loaded.\003")

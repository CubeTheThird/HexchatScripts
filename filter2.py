__module_name__ = 'Filter2'
__module_version__ = '3.3'
__module_description__ = 'Filters join/part messages by hosts'

import hexchat
import sys
if sys.version_info[0] < 3:
	import urllib2
else: 
	import urllib.request
import json
from time import time

last_seen = {}	# List where key is host
				# 0 : last seen
				# 1 : boolean has spoken (0 false 1 true)
				# 2 : previous username
user_timeout = 600	#ignore if timeout is surpassed

halt = False

debug_output = False

def human_readable(s):
	deltas = [
		("seconds", int(s)%60),
		("minutes", int(s/60)%60),
		("hours", int(s/60/60)%24),
		("days", int(s/24/60/60)%30),
		("months", int(s/30/24/60/60)%12),
		("years", int(s/12/30/24/60/60))
	]
	tarr = ['%d %s' % (d[1], d[1] > 1 and d[0] or d[0][:-1])
		for d in reversed(deltas) if d[1]]
	return " ".join(tarr[:2])

def new_msg(word, word_eol, event, attrs):
	#handles normal messages
	global halt
	global last_seen
	if halt == True:
		return

	user = hexchat.strip(word[0])
	users = hexchat.get_list("users")
	host = "NULL"
	for u in users:
		if(u.nick == user):
			host = u.host

	#user was logged in before script started
	if host not in last_seen:
		last_seen[host] = [time(), 1, user]

	#invalid host case
	if host == "" or host == "NULL":
		halt = True
		hexchat.emit_print(event, *word)
		halt = False
		if debug_output:
			print("\00315Supressed invalid host name")
		return hexchat.EAT_ALL

	#user never spoke before
	if last_seen[host][1] == 0:
		time_diff = time() - last_seen[host][0]
		
		#get geoip
		#Python3, urllib2.urlopen("http://example.com/foo/bar").read()
		try:
			if sys.version_info[0] < 3:
				data = json.loads(urllib.request.urlopen("https://freegeoip.net/json/" + host.split('@')[1]).read().decode("utf-8"))
			else: 
				data = json.loads(urllib2.urlopen("https://freegeoip.net/json/" + host.split('@')[1]).read().decode("utf-8"))
				geoip = data["region_name"] + ", " + data["country_name"]
		except:
			geoip = ""

		if user == last_seen[host][2]:
			word[1] += " \00307(logged in %s ago from \00302%s %s\00307)" % (human_readable(time_diff),host,geoip)
		else:
			word[1] += " \00307(logged in %s ago. Formerly \00302%s\00307 from \00302%s %s\00307)" % (human_readable(time_diff),last_seen[host][2],host,geoip) #added host for debug purposes
			last_seen[host][2] = user
		halt = True
		hexchat.emit_print(event, *word)
		halt = False
		last_seen[host][1] = 1
		return hexchat.EAT_ALL
	else:
		last_seen[host][0] = time()

def filter_msg(word, word_eol, event, attrs):

	global halt
	global last_seen
	if halt == True:
		return

	#filter join and part messages
	user = hexchat.strip(word[0])
	host = "NULL"
	#Join event
	if event == "Join":
		host = hexchat.strip(word[2])
		if debug_output:
			host2 = "NULL"
			for u in hexchat.get_list("users"):
				if(u.nick == word[1]):
					host2 = u.host
					if host != host2:
						print("\00315---Inconsistent host error between " + host + " and " + host2 + " ---")
					break
		if host not in last_seen:
			last_seen[host] = [time(), 0, user]
			if debug_output:
				print("\00315Supressed join of " + user + " from " + host)
			return hexchat.EAT_ALL
		elif(last_seen[host][2] != user):
			if last_seen[host][1] == 1:
				word[2] = "Formerly \00302%s\00307" % (last_seen[host][2])
				halt = True
				hexchat.emit_print(event, *word)
				halt = False
			last_seen[host][2] = user
			return hexchat.EAT_ALL
		elif last_seen[host][0] + user_timeout > time():
			last_seen[host][0] = time()
	#Change username event
	elif event == "Change Nick":
		for idx, h in enumerate(last_seen):
			if(last_seen[h][2] == user):
				host = h
				break
		if(host == "NULL"):
			for u in hexchat.get_list("users"):
				if(u.nick == word[1]):
					host = u.host
					last_seen[host] = [time(), 0, user]
					break
		if host == "NULL" and debug_output:
			print("\00315Error in Change Nick event: NULL host")
		last_seen[host][2] = word[1]
		if last_seen[host][0] + user_timeout > time():
			last_seen[host][0] = time()
	#find host
	for idx, h in enumerate(last_seen):
		if(last_seen[h][2] == user):
			host = h
			break

	#if user joined before chat started, quit or something before talking
	if(host == "NULL"):
		if debug_output:
			print("\00315Supressed NULL host output for " + user + " from event " + event)
		return hexchat.EAT_ALL

	#if user never spoke, or spoke too long ago
	if last_seen[host][1] == 0:
		if debug_output:
			print("\00315Supressed new user event " + event + " for user " + user)
		return hexchat.EAT_ALL
	if ( last_seen[host][0] + user_timeout < time() and event not in ["Join", "Change Nick"] ):
		if debug_output:
			print("\00315Supressed old user event " + event + " from user " + user)
		return hexchat.EAT_ALL

def toggle_debug_output(word, word_eol, userdata):

	global debug_output
	text = "Debug output is now "
	if debug_output:
		text += "disabled."
	else:
		text += "enabled."

	debug_output = not debug_output
	print(text)

hooks_new = ["Your Message", "Channel Message", "Channel Msg Hilight", "Your Action", "Channel Action", "Channel Action Hilight"]
hooks_filter = ["Join", "Change Nick", "Part", "Part with Reason", "Quit"]
# hook_print_attrs is used for compatibility with my other scripts, since priorities are hook specific
for hook in hooks_new:
	hexchat.hook_print_attrs(hook, new_msg, hook, hexchat.PRI_HIGH)
for hook in hooks_filter:
	hexchat.hook_print_attrs(hook, filter_msg, hook, hexchat.PRI_HIGH)

hexchat.hook_command("toggledebug", toggle_debug_output, help="/toggledebug shows or hides " + __module_name__ + " debug output")

print("\00304" + __module_name__ + " successfully loaded.\003")

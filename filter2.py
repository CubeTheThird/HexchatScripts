__module_name__ = 'Filter2'
__module_version__ = '4.0'
__module_description__ = 'Filters join/part messages by hosts'

import hexchat
#Import based on python version
import sys
if sys.version_info[0] < 3:
	import urllib2
else:
	import urllib.request

import json
from time import time
import socket

last_seen = {}	# List where key is ip address/hostname
				# 0 : last seen time
				# 1 : boolean has spoken
				# 2 : previous username
				# 3 : last IP address resolved from hostname

#TODO load preferences from stored settings
user_timeout = 600	#ignore if timeout is surpassed
tmp = hexchat.get_pluginpref(__module_name__ + '_' + "debug")
debug_output = (tmp if tmp is not None else 0)
tmp = hexchat.get_pluginpref(__module_name__ + '_' + "geoip")
geoip_output = (tmp if tmp is not None else 0)
tmp = hexchat.get_pluginpref(__module_name__ + '_' + "short")
short_times = (tmp if tmp is not None else 0)

halt = False
t_units = {("seconds",0):"seconds",("seconds",1):"s",
			("minutes",0):"minutes",("minutes",1):"m",
			("hours",0):"hours",("hours",1):"h",
			("days",0):"days",("days",1):"d",
			("months",0):"months",("months",1):"mon",
			("years",0):"years",("years",1):"y"}
#TODO shorten timestamp names
def human_readable(s):
	deltas = [
		(t_units[("seconds",short_times)], int(s)%60),
		(t_units[("minutes",short_times)], int(s/60)%60),
		(t_units[("hours",short_times)], int(s/60/60)%24),
		(t_units[("days",short_times)], int(s/24/60/60)%30),
		(t_units[("months",short_times)], int(s/30/24/60/60)%12),
		(t_units[("years",short_times)], int(s/12/30/24/60/60))
	]
	tarr = ['%d %s' % (d[1], (d[1] > 1 or short_times) and d[0] or d[0][:-1])
		for d in reversed(deltas) if d[1]]
	return " ".join(tarr[:2])

def new_msg(word, word_eol, event, attrs):
	#handles normal messages
	global last_seen
	global halt
	if halt:
		return

	#get username from message
	user_name = hexchat.strip(word[0])

	users = hexchat.get_list("users")

	#Try to find the user based on the users list
	user = "NULL"
	user_host = "NULL"
	user_ip = "NULL"
	for u in users:
		if(u.nick == user_name):
			user = u.host
			user_host = ''.join(user.split('@')[1:])
			user_ip = get_ip(user)
			break

	#user was logged in before script started
	if user_host not in last_seen:
		last_seen[user_host] = [time(), True, user_name, user_ip]

	#invalid user case (typically user is no longer connected)
	if  user_host == "NULL" or user == "NULL":
		halt = True
		hexchat.emit_print(event, *word)
		halt = False
		if debug_output:
			print("\00315Supressed invalid user case")
		return hexchat.EAT_ALL

	#user never spoke before
	if not last_seen[user_host][1]:
		time_diff = time() - last_seen[user_host][0]

		#get geoip
		geoip = get_geoip(user_ip)

		#add information to message
		if user_name == last_seen[user_host][2]:
			word[1] += " \00307(logged in %s ago from \00302%s \00310%s\00307)" % (human_readable(time_diff),user.split('@')[0] + '@' + user_ip,geoip)
		else:
			word[1] += " \00307(logged in %s ago. Formerly \00302%s\00307 from \00302%s \00310%s\00307)" % (human_readable(time_diff),last_seen[user_host][2],user.split('@')[0] + '@' + user_ip,geoip) #added host for debug purposes
			last_seen[user_host][2] = user_name
		#print message
		halt = True
		hexchat.emit_print(event, *word)
		halt = False
		last_seen[user_host][1] = True
		return hexchat.EAT_ALL
	else:
		last_seen[user_host][0] = time()

def filter_msg(word, word_eol, event, attrs):

	global last_seen
	global halt

	if halt:
		return

	#filter join and part messages
	user_name = hexchat.strip(word[0])
	user = "NULL"
	user_ip = "NULL"
	user_host = "NULL"

	#Join event
	if event == "Join":
		user = hexchat.strip(word[2])
		user_host = ''.join(user.split('@')[1:])
		user_ip = get_ip(user)

		if user_host not in last_seen:
			#Search known IP addresses
			if user_host != user_ip:
				for idx, host in enumerate(last_seen):
					if(last_seen[host][3] == user_ip):
						last_seen[user_host] = last_seen.pop(host)
						break

		if user_host not in last_seen:
			#First time join from IP
			last_seen[user_host] = [time(), False, user_name, user_ip]
			if debug_output:
				print("\00315Supressed join of " + user_name + " from " + user_ip)
			return hexchat.EAT_ALL
		elif(last_seen[user_host][2] != user_name):
			#User logged in with different name
			if last_seen[user_host][1]:
				word[2] = "Formerly \00302%s\00307 from \00302%s \00310%s\00307" % (last_seen[user_host][2],user_ip,get_geoip(user_ip))
				halt = True
				hexchat.emit_print(event, *word)
				halt = False
			last_seen[user_host][2] = user_name
			return hexchat.EAT_ALL
		#Update user time
		last_seen[user_host][0] = time()

	#Change username event
	elif event == "Change Nick":

		#Find user in seen list
		for idx, host in enumerate(last_seen):
			if(last_seen[host][2] == user_name):
				user_host = host
				break
		#User was not in seen list
		if(user_host == "NULL"):
			#Find user in users list
			for u in hexchat.get_list("users"):
				if(u.nick == word[1]):
					user = u.host
					user_host = ''.join(user.split('@')[1:])
					user_ip = get_ip(user)
					last_seen[user_host] = [time(), False, user_name, user_ip]
					break
		#User was not in either list
		if user_host == "NULL" and debug_output:
			print("\00315Error in Change Nick event: NULL ip")

		#Continue as though nothing is wrong :Z

		#Update username and time
		last_seen[user_host][2] = word[1]
		last_seen[user_host][0] = time()

	#Find user IP if not already found
	if(user_host == "NULL"):
		for idx, host in enumerate(last_seen):
			if(last_seen[host][2] == user_name):
				user_host = host
				break

	#User parted or quit before sending a message
	if(user_host == "NULL"):
		if debug_output:
			print("\00315Supressed NULL host output for " + user_name + " from event " + event)
		return hexchat.EAT_ALL

	#if user never spoke, or spoke too long ago
	if not last_seen[user_host][1]:
		if debug_output:
			print("\00315Supressed new user event " + event + " for user " + user_name)
		return hexchat.EAT_ALL
	#Hide part and quit messages after timeout
	if ( last_seen[user_host][0] + user_timeout < time() and event not in ["Join", "Change Nick"] ):
		if debug_output:
			print("\00315Supressed old user event " + event + " from user " + user_name)
		return hexchat.EAT_ALL

def get_ip(host):
	try:
		ip = socket.gethostbyname(host.split('@')[1])
	except Exception as e:
		ip = host.split('@')[1:]
	return ''.join(ip)

def get_geoip(ip):
	global geoip_output
	global debug_output
	geoip = ""
	if geoip_output and (len(''.join(ip).split('.')) > 1 or len(''.join(ip).split(':')) > 1):
		try:
			if sys.version_info[0] < 3:
				data = json.loads(urllib2.urlopen("http://ip-api.com/json/" + ip, timeout=1).read().decode("utf-8"))
			else:
				data = json.loads(urllib.request.urlopen("http://ip-api.com/json/" + ip, timeout=1).read().decode("utf-8"))
			if data["status"] == "success":
				geoip = data["regionName"] + ", " + data["country"]
		except Exception as e:
			if debug_output:
				print("\00315 " + e)
	return geoip

def toggle_debug_output(word, word_eol, userdata):

	global debug_output
	text = "Debug output is now "
	if debug_output:
		text += "disabled."
	else:
		text += "enabled."

	debug_output = (debug_output + 1) % 2
	if not hexchat.set_pluginpref(__module_name__ + '_' + "debug",debug_output):
		print("Error saving setting to file.")
	print(text)

def toggle_geoip(word, word_eol, userdata):

	global geoip_output
	text = "Geoip info is now "
	if geoip_output:
		text += "hidden."
	else:
		text += "shown."
	geoip_output = (geoip_output + 1) % 2
	if not hexchat.set_pluginpref(__module_name__ + '_' + "geoip",geoip_output):
		print("Error saving setting to file.")
	print(text)

def toggle_short_times(word, word_eol, userdata):

	global short_times
	text = "Time format is now "
	if short_times:
		text += "full length."
	else:
		text += "abbreviated."
	short_times = (short_times + 1) % 2
	if not hexchat.set_pluginpref(__module_name__ + '_' + "short",short_times):
		print("Error saving setting to file.")
	print(text)

hooks_new = ["Channel Message", "Channel Msg Hilight", "Channel Action", "Channel Action Hilight"]
hooks_filter = ["Join", "Change Nick", "Part", "Part with Reason", "Quit"]
# hook_print_attrs is used for compatibility with my other scripts, since priorities are hook specific
for hook in hooks_new:
	hexchat.hook_print_attrs(hook, new_msg, hook, hexchat.PRI_HIGH)
for hook in hooks_filter:
	hexchat.hook_print_attrs(hook, filter_msg, hook, hexchat.PRI_HIGH)

hexchat.hook_command("toggledebug", toggle_debug_output, help="/toggledebug shows or hides " + __module_name__ + " debug output")
hexchat.hook_command("togglegeoip", toggle_geoip, help="/togglegeoip shows or hides " + __module_name__ + " geoip output")
hexchat.hook_command("toggletimeformat", toggle_short_times, help="/toggletimeformat shortens or lengthens " + __module_name__ + " timestamp name")
print("\00304" + __module_name__ + " successfully loaded.\003")

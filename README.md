# HexchatScripts
Python scripts for IRC chat client Hexchat

Current IRC scripts include:

## Filter 2
An adaptation of the [Smart Filter](https://github.com/hexchat/hexchat-addons/tree/master/python/smart_filter), it removes join and part (quit) messages from chat, unless the user has spoken. This version of the script tracks users based on their host name, instead of their username, and indicates when a user logs in under a different name. Functionality has also been added to indicate a user's region based on said host name, or IP address, though this is experimental.

Update with version 4.0: Improved persistence of user identity based on IP address. Added optional Geo-IP lookup to resolved user IP addresses. Added persistence for all settings within the script.

## Split
A filter to remove `*.net *.split` part messages from chat, which can occur when a server on an IRC network is disconnected. It also hides part messages of the users that have been disconnected.

## Slack
A script to improve the usability of [Slack](https://slack.com) communication via IRC. Currently only removes voice and devoice messages.

## Colour Name
A script that colours usernames within messages, following the standard HexChat colouring scheme. Regex is used for pattern matching, to avoid conflicts and collisions. This script is currently being tested, though no major issues seem to be present.

## Colour Fixer
A script that corrects incorrect removal and changes to colours. This most commonly occurs when another script, such as the Colour Name script, adds colour information. When the colour is "removed" through an empty colour tag, it does not reset to the previous or default colour. This script corrects this.

#! /usr/bin/env python
# -*- coding: utf8 -*-

"""
Copyright (C) 2008 Adolfo González Blázquez <code@infinicode.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version. 

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details. 

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

If you find any bugs or have any suggestions email: code@infinicode.org
"""

"""
wifi-scanner is a prettifier for the linux 'iwlist scan' command
You will get something like:

infinito@laptop:~$ sudo wifi-scanner 
MAC                  	ESSID      	Channel    	Encryption 	Quality   
-------------------- 	---------- 	---------- 	---------- 	----------
00:23:J5:B8:A2:C0    	Truman    	11         	WPA2       	70/100    
00:21:3F:FF:CC:AA    	WLAN_02    	6          	WEP        	64/100    
00:A9:AD:02:AA:BB    	Wireless   	6          	Open       	27/100


infinito@laptop:~$ wifi-scanner -h
Usage: wifi-scanner [-i interface] [-c scan_count] [-s sleep_time]
Options:
	-i, --interface		Network interface to scan (default: wlan0)
						Use 'help' for displaying available interfaces
						Use 'all' for scanning all available interfaces
	-c, --count			Number of times to repeat the scanning (default: 1)
	-s, --sleep			Seconds to sleep between scannings (default: 0)
"""

import os
import sys
import time


#################################################################
## FIND WIRELESS INTERFACES USING THE /proc FILESYSTEM
#################################################################

def find_interfaces():

	try:
		procfile = open('/proc/net/wireless', 'r')
		data = procfile.read().strip()
		procfile.close()
		data = data.split('\n')[2:]
		for i in range(len(data)):
			data[i] = data[i].split(':')[0].strip()
		return data
	except Exception, e:
		print e
		return []
	

#################################################################
## SCANNING USING iwlist
#################################################################

def exec_iwscan():

	global interface
	
	import commands
	data = commands.getstatusoutput('iwlist ' + interface + ' scan')
	data = data[1].split('Cell ')[1:]

	networks = []
	
	for net in data:
		
		info = {
			"mac": '',
			"essid": '',
			"channel": '',
			"encrypted": '',
			"enctype": '',
			"quality": ''
		}
	
		lines = net.split('\n')
		
		for line in lines:
		
			line = line.strip()
			
			if "Address: " in line:
				mac = line.split(': ')[1]
				info["mac"] = mac
				
			elif "ESSID" in line:
				essid = (line.split(':', 1)[1]).replace('"','')
				info["essid"] = essid
				
			elif "(Channel" in line:
				channel = (line.split('(Channel ')[1]).replace(')', '')
				info["channel"] = channel
				
			elif "Encryption key:" in line:
				encrypted = line.split(':')[1]
				info["encrypted"] = encrypted
				
			elif "IE: " in line:
				enctype = line.split(': ', 1)[1]
				if "WPA2" in enctype:
					info["enctype"] = "WPA2"
				elif "WPA" in enctype:
					info["enctype"] = "WPA"
				
			elif "Quality=" in line:
				quality = line.split('=')[1]
				quality = quality.split('  Signal')[0]
				info["quality"] = quality
				
		if info["encrypted"] == "on" and info["enctype"] == '':
			info["enctype"] = "WEP"
		if info["encrypted"] == 'off':
			info["enctype"] = "Open"
				
		networks.append(info)
		
	return networks


#################################################################
## SORT FOUND NETWORKS BY SIGNAL STRENGTH
#################################################################

def sort_networks(networks):

	from operator import itemgetter
	return sorted(networks, key=itemgetter("quality"), reverse=True)
	
	
#################################################################
## PRINT OUTPUT
#################################################################

def print_networks(networks):

	global interface

	if networks == []:
		print "No results obtained scanning interface '%s'" % interface
		sys.exit(0)
	
	print "MAC".ljust(20), '\t',
	print "ESSID".ljust(20), '\t', 
	print "Channel".ljust(10), '\t',
	print "Encryption".ljust(10), '\t',
	print "Quality".ljust(10)
	
	print ''.ljust(20, '-'), '\t',
	print ''.ljust(20, '-'), '\t',
	print ''.ljust(10, '-'), '\t',
	print ''.ljust(10, '-'), '\t',
	print ''.ljust(10, '-')
	
	for net in networks:
		print net["mac"].ljust(20), '\t', 
		print net["essid"].ljust(20), '\t', 
		print net["channel"].ljust(10), '\t',
		print net["enctype"].ljust(10), '\t',
		print net["quality"].ljust(10)


#################################################################
## COMMAND LINE PARSING
#################################################################

def command_usage():
	global interface, count, sleep
	
	print "Usage: %s [-i interface] [-c scan_count] [-s sleep_time]" % os.path.basename(sys.argv[0])
	print "Options:"
	print "	-i, --interface		Network interface to scan (default: %s)"  % interface
	print "				Use 'help' for displaying available interfaces"
	print "				Use 'all' for scanning all available interfaces"
	print "	-c, --count		Number of times to repeat the scanning (default: %s)" % count
	print "	-s, --sleep		Seconds to sleep between scannings (default: %s)" % sleep


def command_unknown(cmd):
	print "Unknown command:", cmd
	#print "Run '%s --help' to see a full list of available command line options." % os.path.basename(sys.argv[0])
	print


def command_parse():

	import getopt
	global interface, count, sleep, interfaces

	try:
	    opts, args = getopt.getopt(sys.argv[1:],"hi:c:s:", ["help","interface=","count=","sleep="])
	except getopt.GetoptError, err:
		command_unknown(sys.argv[1])
		command_usage()
		sys.exit(2)
	
	for o, a in opts:
		if o in ("-h", "--help"):
			command_usage()
			sys.exit()
		if o in ("-i", "--interface"):
			if a == "help":
				print "Wireless interfaces:", interfaces
				sys.exit()
			interface = a
		elif o in ("-c", "--count"):
			try:
				count = int(a)
			except:
				print "Error: count value must be integer"
				sys.exit(2)
		elif o in ("-s", "--sleep"):
			try:
				sleep = float(a)
			except:
				print "Error: sleep value must be float"
				sys.exit(2)
				
	return interface, count, sleep


#################################################################
## CHECK IF ROOT
#################################################################

def check_root():

	import commands
	if commands.getoutput('whoami') != 'root':
		print "---------------------------------------------"
		print "  You should be root to get better results!  "
		print "---------------------------------------------"
		print


#################################################################
## MAIN FUNCTIONS
#################################################################

def scan_loop():
	
	global count, sleep
	
	for n in range(count):
		networks = exec_iwscan()
		if count > 1: time.sleep(sleep)
	networks = sort_networks(networks)
	print_networks(networks)


if __name__ == "__main__":

	interface = 'wlan0'
	count = 1
	sleep = 0

	interfaces = find_interfaces()
	interface = interfaces[0]
	interface, count, sleep = command_parse()
	check_root()
	
	if interface == "all":
		for i in range(len(interfaces)):
			interface = interfaces[i]
			print "Scanning using interface '%s'\n" % interface
			scan_loop()
			print
	else:
		scan_loop()

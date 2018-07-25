#!/usr/bin/python

import os
from graphviz import Digraph
import subprocess
import json
import requests
import base64

url = "http://10.0.1.1/cgi-bin/luci/rpc"
headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}


#OpenWRT Authentication token function
def authtoken():
	data = {'id': 1, 'method': 'login', 'params': ['user', 'password']}
	result = requests.post(url + "/auth", data=json.dumps(data), headers=headers).json()
	if result['error'] == None:
		authtoken = result['result']
	else:
		print "There was an error requesting authentication token from API."
	return authtoken

#get auth token once
authtoken = authtoken()

#OpenWRT API calls
def apicall(endpoint, data, authtoken):
	result = requests.post(url + "/" + endpoint + "?auth=" + authtoken, data=json.dumps(data), headers=headers).json()	
	return result

#decode base64 strings
def decode64(coded_string):
	result = base64.b64decode(coded_string)
	return result

#Ping function
def ping(ip):
	response = os.system("ping -c 1 " + ip + " > /dev/null 2>&1")	
	#Response
	if response == 0:
		results = 'up'
	else:
		results = 'down'
	return results

#pull dhcp.leases file from router
#p = subprocess.Popen(["scp", "root@10.0.1.1:/tmp/dhcp.leases", "dhcp.leases"])
#sts = os.waitpid(p.pid, 0)

#Query API for dhcp.leases, do some stuff and populate arrays
data = {'id': 1, 'method': 'readfile', 'params': ['/tmp/dhcp.leases']}
result = apicall("fs", data, authtoken)
result = result['result']
result = decode64(result)
result = result.splitlines()
ips = []
hostnames = []
for line in result:
	result = line.split()
	ips.append(result[2])
	hostnames.append(result[3])

#SSH-command function
def sshcommand(command):
	ssh = subprocess.Popen(["ssh", "%s" % "root@10.0.1.1", command],
		shell=False,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE)
	result = ssh.stdout.readlines()
	return result


#open dhcp.leases file and split out ip and hostname
#ips = []
#hostnames = []

#with open("dhcp.leases", "r") as dhcp_leases:
#	for line in dhcp_leases:
#		linedata = line.split()
#		ips.append(linedata[2])
#		hostnames.append(linedata[3])

#send remote ssh command and make some ifs for interface status
result = sshcommand("mwan3 interfaces")
if result == []:
	error = ssh.stderr.readlines()
	print >>sys.stderr, "ERROR: %s" % error
else:
	finalresultarr = result[1].split()
	finalresultarr2 = result[2].split()

if finalresultarr[3] == "online":
	interfacestatus = "#00ff00"
else:
	interfacestatus = "#ff0000"

if finalresultarr2[3] == "online":
        interfacestatus2 = "#00ff00"
else:
        interfacestatus2 = "#ff0000"


#vpn status
result = ping("10.0.1.226")
if result == "up":
	vpnstatus = "#00ff00"
else:
	vpnstatus = "#ff0000"

#Router status
result = ping("10.0.1.1")
if result == "up":
	routerstatus = "#00ff00"
else:
	routerstatus = "#ff0000"

#vpsstatus
result = ping("foderus.se")
if result == "up":
        vpsstatus = "#00ff00"
else:
        vpsstatus = "#ff0000"

#define graph
graph = Digraph(comment='Network')

#create nodes and static router entry
graph.node(finalresultarr[1].upper(), finalresultarr[1].upper(), style="filled", fillcolor=interfacestatus)
graph.node(finalresultarr2[1].upper(), finalresultarr2[1].upper(), style="filled", fillcolor=interfacestatus2)
graph.node('OpenWRT', 'OpenWRT', style="filled", fillcolor=routerstatus)
graph.node('Indra', 'Indra', style="filled", fillcolor=vpnstatus)
graph.node('VPS', 'VPS', style="filled", fillcolor=vpsstatus)
graph.node('Internet', 'Internet', style="filled", fillcolor="#ffffff")
graph.node('Indra Gateway', 'Indra Gateway', style="filled", fillcolor="#cccccc")

#populate nodes and edges also check for up or down status
i = 0
for host in ips:
	if ping(host) == 'up':
		graph.node(host, hostnames[i], style="filled", fillcolor="#00ff00")
		graph.edge(host, 'OpenWRT', constraint='false')
	else:
		graph.node(host, hostnames[i], style="filled", fillcolor="#ff0000")
                graph.edge(host, 'OpenWRT', constraint='false')
	i = i + 1

#custom edges for static router entry
graph.edge('OpenWRT', finalresultarr[1].upper(), constraint='false')
graph.edge('OpenWRT', finalresultarr2[1].upper(), constraint='false')
graph.edge('OpenWRT', 'Indra', constraint='false')
graph.edge('Indra', 'Indra Gateway', constraint='false')
graph.edge('Indra Gateway', 'Internet', constraint='false')
graph.edge('Indra', '10.0.1.3', constraint='false')
graph.edge('10.0.1.3', 'Indra Gateway', constraint='false')
graph.edge('VPS', '10.0.1.3', constraint='false')
graph.edge('VPS', 'Internet', constraint='false')
graph.edge('Internet', 'VPS', constraint='false')
graph.edge('10.0.1.3', 'VPS', constraint='false')
graph.edge('WAN', 'Internet', constraint='false')
graph.edge('WWAN', 'Internet', constraint='false')

#set format png and generate diagram, general graph settings
graph.format = 'png'
graph.node_attr['shape']='box'
graph.engine = 'circo'
graph.render('graph', view=False)

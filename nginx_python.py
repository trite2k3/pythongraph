#!/usr/bin/python

import os
from graphviz import Digraph
import subprocess

#Ping function
def ping(ip):
	response = os.system("ping -c 1 " + ip + " > /dev/null 2>&1")	
	#Response
	if response == 0:
		results = 'up'
		return results
	else:
		results = 'down'
		return results

#pull dhcp.leases file from router
p = subprocess.Popen(["scp", "root@10.0.1.1:/tmp/dhcp.leases", "dhcp.leases"])
sts = os.waitpid(p.pid, 0)

#SSH-command function
def sshcommand(command):
	ssh = subprocess.Popen(["ssh", "%s" % "root@10.0.1.1", command],
		shell=False,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE)
	result = ssh.stdout.readlines()
	return result


#open dhcp.leases file and split out ip and hostname
ips = []
hostnames = []

with open("dhcp.leases", "r") as dhcp_leases:
	for line in dhcp_leases:
		linedata = line.split()
		ips.append(linedata[2])
		hostnames.append(linedata[3])

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


#define graph
graph = Digraph(comment='Network')

#create nodes and static router entry
graph.node(finalresultarr[1], finalresultarr[1], style="filled", fillcolor=interfacestatus)
graph.node(finalresultarr2[1], finalresultarr2[1], style="filled", fillcolor=interfacestatus2)
graph.node('OpenWRT', 'OpenWRT', style="filled", fillcolor="#00ff00")

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
graph.edge('OpenWRT', finalresultarr[1], constraint='false')
graph.edge('OpenWRT', finalresultarr2[1], constraint='false')

#set format png and generate diagram, general graph settings
graph.format = 'png'
graph.node_attr['shape']='box'
graph.render('graph', view=False)

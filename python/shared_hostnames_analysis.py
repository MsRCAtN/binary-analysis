#!/usr/bin/python2.7

import argparse
import collections

import networkx
import os
import pefile
import pprint
import re
import sys

from networkx.algorithms import bipartite
from networkx.drawing.nx_agraph import write_dot
from os import popen


def find_hostnames(string):
    possible_hostnames = re.findall(
        r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}',
        string)
    valid_hostname = filter(
        lambda hostname: hostname.split(".")[-1].lower() in valid_hostname_suffixes,
        possible_hostnames)
    return valid_hostname


args = argparse.ArgumentParser(description="Visualize shared hostnames"
                                           " between a directory of malware samples")
args.add_argument("target_path", help="directory with malware samples")
args.add_argument("output_file", help="file to write DOT file to")
args.add_argument("malware_projection", help="file to write DOT file to")
args.add_argument("resource_projection", help="file to write DOT file to")
args.add_argument("graph_tool", help="tool to draw graphs to png", default="fdp", nargs='?')
args = args.parse_args()

network = networkx.Graph()

valid_hostname_suffixes = map(
    lambda string: string.strip(), open("domain_suffixes.txt")
)
valid_hostname_suffixes = set(valid_hostname_suffixes)

for root, dirs, files in os.walk(args.target_path):
    for path in files:
        try:
            per = pefile.PE(os.path.join(root, path))
        except pefile.PEFormatError:
            continue
        fullpath = os.path.join(root, path)
        strings = popen("strings '{0}'".format(fullpath)).read()

        hostnames = find_hostnames(strings)
        if len(hostnames):
            network.add_node(path, label=path[:32], color='black', penwidth=5, bipartite=0)
        for hostname in hostnames:
            network.add_node(hostname, label=hostname, color='blue', penwidth=10, bipartite=1)
            network.add_edge(hostname, path, penwidth=2)
        if hostnames:
            print "Extracted hostnames from: ", path
            pprint.pprint(hostnames)

write_dot(network, args.output_file)

malware = set(n for n,d in network.nodes(data=True) if d['bipartite'] == 0)
hostname = set(network) - malware

malware_network = bipartite.projected_graph(network, malware)
hostname_network = bipartite.projected_graph(network, hostname)

write_dot(malware_network, args.malware_projection)
write_dot(hostname_network, args.resource_projection)

toolname = args.graph_tool

popen("'{0}' '{1}' -Goverlap=false -Gsplines=true -T png -o '{1}'.png".format(
    toolname, args.output_file
))

popen("'{0}' '{1}' -Goverlap=false -Gsplines=true -T png -o '{1}'.png".format(
    toolname, args.malware_projection
))

popen("'{0}' '{1}' -Goverlap=false -Gsplines=true -T png -o '{1}'.png".format(
    toolname, args.resource_projection
))

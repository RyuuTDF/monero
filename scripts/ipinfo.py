#!/usr/bin/python3
import requests
import ipaddress
import os.path
import json
from log_filter import write_file


def update_tor_exit_nodes(tor_ip_file):
    """
    Update the list of known TOR exit nodes.

    The file is updated with new known TOR nodes but old nodes are not removed.
    :param tor_ip_file: Name of the file where the current list of Tor IPs are stored.
    :return: None
    """
    txt = requests.get("https://check.torproject.org/cgi-bin/TorBulkExitList.py?ip=1.1.1.1").text
    set = read_ip_list(txt.split("\n"))
    if not os.path.isfile(tor_ip_file):
        newset = set
        print("Tor nodes found: " + str(len(newset)))
    else:
        oldset = read_ip_list_from_file(tor_ip_file)
        newset = oldset.union(set)
        print("Tor nodes updated. New nodes: " + str((len(newset) - len(oldset))))

    write_file(tor_ip_file, "ip-address,", list(newset), True)


def read_ip_list(ip_list):
    """
    Parse list of strings and return set of valid unique IP-addresses.

    :param ip_list: List of Strings, containing IP-addresses.
    :return:       Set of valid unique IP-addresses.
    """
    ip_set = set()
    for line in ip_list:
        try:
            # check if ip address is valid
            # throws exception when ip is invalid
            if ":" in line:
                line = line.split(":")[0]
            line = line.replace(",\n", "")
            ipaddress.ip_address(line)
            ip_set.add(line)
        except Exception:
            if line != "\n" and line != "":
                print("Given IP is not valid: " + line)
            continue
    return ip_set


def read_ip_list_from_file(filename):
    """
    Read a list of IP-addresses from a CSV file and return set of valid unique IP-addresses.

    :param filename:    The name of the file to read the list of IP-addresses from.
    :return:            The set of valid unique IP-addresses.
    """
    with open(filename, "r") as file:
        contents = file.readlines()

    return read_ip_list(contents)


class IpCategories:
    """
    Does not cache results!
    """

    def __init__(self, monero_ip_file, tor_ip_file):
        """
        Initialize IpCategories object.

        :param monero_ip_file:  Filename of the known Monero IP-addresses.
        :param tor_ip_file:     Filename of the known Tor end node IP-addresses.
        """
        self.categories = self.get_ip_categories(monero_ip_file, tor_ip_file)

    def get_ip_categories(self, monero_ip_file, tor_ip_file):
        """
        Create IP category dictionary, containing a list of IP-addresses as a value for each key.
        :param monero_ip_file:  Filename of the known Monero IP-addresses.
        :param tor_ip_file:     Filename of the known Tor end node IP-addresses.
        :return:                Dictionary of categories as keys and lists of IP-addresses as values.
        """
        # Dict in the form of: {category : filename}
        # file with filename is read from
        files = {"monero": monero_ip_file, "TOR": tor_ip_file}
        categories = {}
        for key in files:
            categories[key] = read_ip_list_from_file(files[key])
        return categories

    def get_ip_info(self, ip):
        """
        Get the geographical and category information for the given IP-address.

        :param ip:  The IP-address for which information is requested.
        :return:    Information about the IP-address.
        """
        info = self.poll_ipinfo(ip)
        info["category"] = self.get_ip_category(ip)
        return info

    def poll_ipinfo(self, ip):
        """
        Retrieve geographical information of the given IP-address using IpInfo.io

        :param ip:  The IP-address for which information is requested.
        :return:    The geographical infrormation.
        """
        return requests.get('https://ipinfo.io/' + ip).json()

    def get_ip_category(self, ip):
        for category in self.categories:
            if ip in self.categories[category]:
                return category
        return None


def read_cache(filename):
    """
    Read the given JSON file.

    :param filename:    The JSON file to be read
    :return:            The read file in JSON format
    """
    with open(filename, "r") as file:
        return json.loads(file.read())


def write_cache(cache, filename):
    """
    Write the given JSON to the given file.

    :param cache:       The JSON to be written.
    :param filename:    The filename to be written to.
    :return:            None
    """
    with open(filename, "w+") as writer:
        writer.write(json.dumps(cache))
    print("writing to cache...")


def get_ip_info(ips, monero_ip_file, tor_ip_file, cache_file="ipinfo.json"):
    """
    Given a list of ip addresses, return the information about these ip addresses in a dict
    The results are written to cache.json to prevent duplicate querying

    :param ips:             The IP-addresses to be checked.
    :param monero_ip_file:  The file containing identified Monero IPs
    :param tor_ip_file:     The file containing identified Tor end nodes.
    :param cache_file:      The file containing previously gathered information.
    :return:                Dictionary of information with newly encountered IP-add9resses.
    """
    iplist = read_ip_list(ips)
    x = IpCategories(monero_ip_file, tor_ip_file)
    if os.path.isfile(cache_file):
        cache = read_cache(cache_file)
    else:
        cache = {}

    counter = 0

    ret = {}

    for ip in iplist:
        if ip not in cache:
            try:
                cache[ip] = x.get_ip_info(ip)
                counter += 1
            except:
                print("Getting ip info failed! Maybe the 1000 reqs/day limit is exceeded?")
                break
        ret[ip] = cache[ip]
    if counter != 0:
        write_cache(cache, cache_file)

    return ret

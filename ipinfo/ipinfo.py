import requests
import ipaddress
import os.path
import json

"""
Update the list of known TOR exit nodes
The file is updated with new known TOR nodes but old nodes are not removed
"""
def update_tor_exit_nodes():
    filename = IpCategories.files["TOR"]
    txt = requests.get("https://check.torproject.org/cgi-bin/TorBulkExitList.py?ip=1.1.1.1").text
    set = read_ip_list(txt.split("\n"))
    if not os.path.isfile(filename):
        newset = set
        print("Tor nodes found: " + str(len(newset)))
    else:
        oldset = read_ip_list_from_file(filename)
        newset = oldset.union(set)
        print("Tor nodes updated. New nodes: " + str((len(newset) - len(oldset))))
    with open(filename, "w+") as writer:
        writer.write("\n".join(newset))

"""
Given a list of strings with ip addresses
Returns a set of only valid ip addresses
"""
def read_ip_list(list):
    ip_set = set()
    for line in list:
        try:
            # check if ip address is valid
            # throws exception when ip is invalid
            ipaddress.ip_address(line)
            ip_set.add(line)
        except Exception:
            if (line != "\n" and line != ""):
                print("Given IP is not valid: " + line)
            continue
    return ip_set

"""
Read a list of ip addresses from a file
Return a set of only valid addresses
"""
def read_ip_list_from_file(filename):
    with open(filename, "r") as file:
        contents = file.read().split("\n")

    return read_ip_list(contents)

"""
Does not cache results!
"""
class IpCategories:
    # Dict in the form of: {category : filename}
    # file with filename is read from
    files = {"TOR": "torip", "monero": "moneroip"}

    def __init__(self):
        self.categories = self.get_ip_categories()

    def get_ip_categories(self):
        categories = {}
        for key in self.files:
            categories[key] = read_ip_list_from_file(self.files[key])
        return categories

    def get_ip_info(self, ip):
        info = self.poll_ipinfo(ip)
        info["category"] = self.get_ip_category(ip)
        return info

    def poll_ipinfo(self, ip):
        return requests.get('https://ipinfo.io/' + ip).json()

    def get_ip_category(self, ip):
        for category in self.categories:
            if ip in self.categories[category]:
                return category
        return None

def read_cache(filename):
    with open(filename, "r") as file:
        return json.loads(file.read())

def write_cache(cache, filename):
    with open(filename, "w+") as writer:
        writer.write(json.dumps(cache))
    print("writing to cache...")

"""
Given a list of ip addresses, return the information about these ip addresses in a dict
The results are written to cache.json to prevent duplicate querying
"""
def get_ip_info(ips):
    filename = "cache.json"
    iplist = read_ip_list(ips)
    x = IpCategories()
    if os.path.isfile(filename):
        cache = read_cache(filename)
    else:
        cache = {}

    counter = 0

    ret = {}

    for ip in iplist:
        if not ip in cache:
            cache[ip] = x.get_ip_info(ip)
            print(str(counter) + ": " + ip)
            counter += 1
            if (counter % 25 == 0):
                write_cache(cache, filename)
        ret[ip] = cache[ip]
    if counter != 0:
        write_cache(cache, filename)

    return ret

#update_tor_exit_nodes()
#print(get_ip_info(["212.83.172.162"]))

import requests
import ipaddress
import os.path

def get_tor_exit_nodes():
    filename = "torip.txt"
    if not os.path.isfile(filename):
        with open(filename, "w+") as writer:
            writer.write(requests.get("https://check.torproject.org/cgi-bin/TorBulkExitList.py?ip=1.1.1.1").text)
    with open(filename, "r") as file:
        return read_ip_list(file)

def get_ip_categories():
    return {"TOR": get_tor_exit_nodes()}

def get_ip_info(ip):
    info = poll_ipinfo(ip)
    info["category"] = get_ip_category(ip)
    return info

def poll_ipinfo(ip):
    return requests.get('https://ipinfo.io/' + ip).json()

# Expects a list of strings, with ip addresses
# Returns a set of only valid ip addresses
def read_ip_list(list):
    ip_set = set()
    for line in list:
        try:
            # check if ip address is valid
            # throws exception when ip is invalid
            ipaddress.ip_address(line)
            ip_set.add(line)
        except Exception:
            continue
    return ip_set

def get_ip_category(ip):
    categories = get_ip_categories()
    for category in categories:
        if ip in categories[category]:
            return category
    return None


#print(get_ip_info("103.3.61.114"))

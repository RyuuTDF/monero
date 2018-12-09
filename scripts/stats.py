import sys
import csv
import numpy as np
from ipinfo import get_ip_info, update_tor_exit_nodes
from datetime import datetime

def connection_types(connects, ipinfos):
    types = {}
    for (ip, _, _, _) in connects:
        type = ipinfos[ip.split(":")[0]]["category"]
        if type not in types:
            types[type] = 0
        types[type] += 1

    return types

def connection_length(connects):
    connection_lengths = {}
    for (ip, connection, disconnection, _) in connects:
        try:
            conn_time = datetime.strptime(connection, "%Y-%m-%d %H:%M:%S.%f")
            disc_time = datetime.strptime(disconnection, "%Y-%m-%d %H:%M:%S.%f")
            time_delta = disc_time - conn_time
            if ip not in connection_lengths:
                connection_lengths[ip] = []
            connection_lengths[ip].append(time_delta)
        except:
            print("The connection of " + ip + " does not have a proper connection/disconnection time")

    return connection_lengths


def read_log_filter(addresses_file, connect_file, notify_file):
    with open(addresses_file, "r") as file:
        csv_read = csv.reader(file)
        next(csv_read)
        addresses = []
        for row in csv_read:
            addresses.append(row[0])

    with open(connect_file, "r") as file:
        csv_read = csv.reader(file)
        ips = []
        connections = []
        disconnections = []
        reasons = []
        next(csv_read)
        for row in csv_read:
            ips.append(row[0])
            connections.append(row[1])
            disconnections.append(row[2])
            reasons.append(row[3])
        connects = list(zip(ips, connections, disconnections, reasons))

    # TODO: finish this
    with open(notify_file, "r") as file:
        csv_read = csv.reader(file)
        next(csv_read)
        notifies = file.readlines()

    return (addresses, connects, notifies)

def main():
    """
    Given the result files from log_filter, calculate useful statistics
    """
    addresses_file = sys.argv[1]
    connect_file = sys.argv[2]
    notify_file = sys.argv[3]
    monero_ip_file = sys.argv[4]
    tor_ip_file = sys.argv[5]

    update_tor_exit_nodes(tor_ip_file)

    (addresses, connects, notifies) = read_log_filter(addresses_file, connect_file, notify_file)

    ipinfos = get_ip_info(addresses, monero_ip_file, tor_ip_file)

    conn_types = connection_types(connects, ipinfos)
    print("Connection types: ")
    print(conn_types)

    connection_lengths = connection_length(connects)
    print("Connection lengths: ")
    print(connection_lengths)

    print("Average connection length: ")
    all_connection_lengths = np.array(sum([x for x in connection_lengths.values()], []))
    avg_conn_length = np.mean(all_connection_lengths)
    print(avg_conn_length)

main()

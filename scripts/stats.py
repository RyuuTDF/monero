import csv
import math
import sys
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
from ipinfo import get_ip_info, update_tor_exit_nodes


def connection_types(connects, ipinfos):
    types = {}
    for (ip, _, _, _) in connects:
        typ = ipinfos[ip.split(":")[0]]["category"]
        if typ not in types:
            types[typ] = 0
        types[typ] += 1

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


def plot_connection_length(connects):
    connection_lengths = connection_length(connects)
    connection_lengths = [0 if connection.total_seconds() == 0 else math.log(connection.total_seconds(), 10) for
                          connections in connection_lengths.values() for connection in connections]
    plt.hist(connection_lengths, bins=100)
    plt.xlabel("Connection duration (log(s, 10))")
    plt.ylabel("Number of connections")
    plt.title("Histogram of connection duration")
    plt.savefig("conn_dur_hist.png")
    plt.close()


def plot_notification(notifies):
    notifications = {}
    for (ip) in notifies:
        if ":" in ip:
            ip = ip.split(":")[0]
        if ip not in notifications:
            notifications[ip] = 0
        notifications[ip] += 1
    plt.hist([math.log(notification, 10) for notification in notifications.values()], bins=100)
    plt.xlabel("Number of notifications (log_10)")
    plt.ylabel("Number of ip addresses")
    plt.title("Histogram of amount of notifications per ip address")
    plt.savefig("notif_hist.png")
    plt.close()


def plot_connection_timeline(connects):
    start_date = datetime.max
    end_date = datetime.min
    for (_, connection, disconnection, _) in connects:
        try:
            conn_time = datetime.strptime(connection, "%Y-%m-%d %H:%M:%S.%f")
            disc_time = datetime.strptime(disconnection, "%Y-%m-%d %H:%M:%S.%f")
            start_date = conn_time if start_date > conn_time else start_date
            end_date = disc_time if end_date < disc_time else end_date
        except:
            pass

    timestamps = pd.date_range(start_date, end_date, freq="H")
    counter = {}
    for (_, con, dc, _) in connects:
        for timestamp in timestamps:
            if timestamp not in counter:
                counter[timestamp] = 0
            try:
                conn_time = datetime.strptime(con, "%Y-%m-%d %H:%M:%S.%f")
                disc_time = datetime.strptime(dc, "%Y-%m-%d %H:%M:%S.%f")
                if conn_time < timestamp < disc_time:
                    counter[timestamp] += 1
            except:
                pass

    plt.plot(counter.keys(), counter.values())
    plt.xlabel("Date")
    plt.ylabel("Number of connections")
    plt.title("Connections over time")
    plt.savefig("conn_time.png")
    plt.close()


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

    with open(notify_file, "r") as file:
        csv_read = csv.reader(file)
        next(csv_read)
        notifies = []
        for row in csv_read:
            notifies.append(row[0])

    return addresses, connects, notifies


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

    plot_connection_length(connects)
    plot_notification(notifies)
    plot_connection_timeline(connects)


main()

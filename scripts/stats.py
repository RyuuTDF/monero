import csv
import sys

import matplotlib.pyplot as plt
import numpy as np
import folium
import json
import pycountry
import branca

from datetime import datetime
from ipinfo import get_ip_info, update_tor_exit_nodes


def connection_types(connects, ipinfos):
    """
    Splits connections made into three categories and calculates amount of connections per category.

    :param connects     List containing connect and disconnect notifications.
    :param ipinfos      Information about the IP addresses, including their category.
    :return Hash map that maps the types of connections to the amount of their occurrences.
    """
    ips = set()

    types = {}
    for (ip, _, _, _) in connects:
        ipsplit = ip.split(":")[0]
        if ipsplit not in ips:
            typ = ipinfos[ipsplit]["category"]
            if typ not in types:
                types[typ] = 0
            types[typ] += 1
            ips.add(ipsplit)

    return types


def connection_length(connects):
    """
    Calculates the duration of all connections made.

    :param connects     List containing connect and disconnect notifications.
    :return: Hash map of IP addresses mapped to the list of their connection lengths.
    """
    connection_lengths = {}
    for (ip, connection, disconnection, reason) in connects:
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
    """
    Creates and saves the Connection Duration plot.

    :param connects     List containing connect and disconnect notifications.
    :return: None
    """
    connection_lengths = connection_length(connects)
    connection_lengths = [0 if connection.total_seconds() <= 0 else connection.total_seconds() for
                          connections in connection_lengths.values() for connection in connections]
    plt.hist(connection_lengths, bins=np.logspace(np.log10(0.01), np.log10(max(connection_lengths)), 100))
    plt.xscale('log')
    plt.xlabel("Connection duration (s)")
    plt.ylabel("Number of connections")
    plt.title("Histogram of connection duration")
    plt.savefig("conn_dur_hist.png")
    plt.close()


def plot_notification(notifies):
    """
    Creates and saves the Notifications per IP plot.

    :param notifies  List containing the notifications.
    :return: None
    """
    notifications = {}
    for (ip) in notifies:
        if ":" in ip:
            ip = ip.split(":")[0]
        if ip not in notifications:
            notifications[ip] = 0
        notifications[ip] += 1
    to_plot = [notification for notification in notifications.values()]
    plt.hist(to_plot, bins=np.logspace(np.log10(1), np.log10(max(to_plot)), 100))
    plt.xscale('log')
    plt.xlabel("Number of notifications (log_10)")
    plt.ylabel("Number of ip addresses")
    plt.title("Histogram of amount of notifications per ip address")
    plt.savefig("notif_hist.png")
    plt.close()


def plot_connection_timeline(connects):
    """
    Creates and saves the Connections over Time plot.

    :param connects         List containing connect and disconnect notifications.
    :return: None
    """

    start_date = datetime.max
    end_date = datetime.min

    events = []

    for (_, connection, disconnection, reason) in connects:
        try:
            conn_time = datetime.strptime(connection, "%Y-%m-%d %H:%M:%S.%f")
            events.append([conn_time, 1])
            start_date = conn_time if start_date > conn_time else start_date
        except:
            pass

        try:
            disc_time = datetime.strptime(disconnection, "%Y-%m-%d %H:%M:%S.%f")
            events.append([disc_time, -1])
            end_date = disc_time if end_date < disc_time else end_date
        except:
            pass

    events.sort(key=lambda e: e[0])

    times = []
    values = [0]

    while events:
        e = events[0]
        times.append(e[0])
        values.append(values[-1] + e[1])
        del events[0]

    plt.figure(figsize=(15, 10))
    plt.plot(times, values[1:])
    plt.xlabel("Date")
    plt.ylabel("Number of connections")
    plt.title("Connections over time")
    plt.savefig("conn_time.png")
    plt.close()


def read_log_filter(addresses_file, connect_file, notify_file, block_file):
    """
    Turns the files from log_filter.py into usable lists.

    :param addresses_file   Name of the ip adresses file.
    :param connect_file     Name of the connections file.
    :param notify_file      Name of the notifications file.
    :param block_file       Name of the blocks notification file.
    :return: Lists created from the files.
    """
    addresses = read_addresses(addresses_file)
    connects = read_connect(connect_file)
    notifies = read_notify(notify_file)
    blocks = read_blocks(block_file)

    return addresses, connects, notifies, blocks


def read_addresses(addresses_file):
    """
    Turns the adresses files from log_filter.py into usable list.

    :param addresses_file   Name of the ip adresses file.
    :return: List created from the file.
    """
    with open(addresses_file, "r") as file:
        csv_read = csv.reader(file)
        next(csv_read)
        addresses = []
        for row in csv_read:
            addresses.append(row[0])
        return addresses


def read_connect(connect_file):
    """
    Turns the connection file from log_filter.py into usable list.

    :param connect_file     Name of the connections file.
    :return: List created from the file.
    """
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
        return list(zip(ips, connections, disconnections, reasons))


def read_notify(notify_file):
    """
    Turns the notification file from log_filter.py into usable list.

    :param notify_file      Name of the notifications file.
    :return: List created from the file.
    """
    with open(notify_file, "r") as file:
        csv_read = csv.reader(file)
        next(csv_read)
        notifies = []
        for row in csv_read:
            notifies.append(row[0])
        return notifies


def read_blocks(block_file):
    """
    Turns the block notification file from log_filter.py into usable list.

    :param block_file       Name of the blocks notification file.
    :return: List created from the file.
    """
    with open(block_file, "r") as file:
        csv_read = csv.reader(file)
        ips = []
        timestamps = []
        block_heights = []
        next(csv_read)
        for row in csv_read:
            ips.append(row[0])
            timestamps.append(row[1])
            block_heights.append(row[2])
        return list(zip(ips, timestamps, block_heights))


def plot_location_data(addresses, ipinfos, worldmap):
    """
    Creates and saves the World Map

    :param addresses    List containing the IP Adresses
    :param ipinfos      Information about the IP addresses, including their geolocation
    :param worldmap     Location of the World Map file.
    :return: None
    """
    locs = {}

    m = folium.Map(location=[20, 0], tiles="Mapbox Bright", zoom_start=2)
    circles = []

    for address in addresses:
        info = ipinfos[address.split(":")[0]]
        if "country" in info and "loc" in info and info["category"] is None:
            loc = info["country"]
            if loc not in locs:
                locs[loc] = 0

            t = info["loc"].split(",")
            circles.append(folium.Circle(
                location=[float(t[0]), float(t[1])],
                radius=500
            ))
            locs[loc] += 1

    world_data = json.load(open(worldmap))

    colormap = branca.colormap.linear.YlGn_09.scale(0, 2500)

    def get_proper_colormap(feature):
        land = pycountry.countries.get(alpha_3=feature["id"])
        try:
            alpha2 = land.alpha_2
        except:
            print("Alpha 3 not recognized!: " + feature["id"])
            return colormap(0)

        if alpha2 in locs:
            return colormap(locs[alpha2])
        else:
            return colormap(0)

    folium.GeoJson(world_data, style_function=lambda feature: {
        'fillColor': get_proper_colormap(feature),
        'color': 'black',
        'weight': 1,
        'dashArray': '5, 5',
        'fillOpacity': 0.9,
    }).add_to(m)

    for circle in circles:
        circle.add_to(m)

    m.save("conn_origins.html")

    n = np.arange(len(locs.keys()))
    plt.figure(figsize=(30, 5))
    plt.bar(n, locs.values())
    plt.xticks(n, locs.keys())
    plt.xlabel("Country")
    plt.ylabel("Number of connections")
    plt.title("Origins of connections")
    plt.savefig("conn_origins.png")


def plot_blocks_redundancy(blocks):
    """
    Creates and saves the Block Redundancy plot.

    :param blocks   List containing the block notifications.
    :return: None
    """
    block_heights = {}
    for block in blocks:
        if block[2] not in block_heights:
            block_heights[block[2]] = 0
        block_heights[block[2]] += 1

    plt.figure(figsize=(15, 10))
    plt.hist(list(block_heights.values()), bins=np.arange(0, 1 + max(list(block_heights.values()))))
    plt.xlabel("Redundancy")
    plt.ylabel("Frequency")
    plt.title("Block redundancy")
    plt.savefig("block_redundancy.png")
    plt.close()


def main():
    """
    Given the result files from log_filter, calculate useful statistics and create useful plots.

    Usage: python3 stats.py input_file1.csv input_file2.csv ...
    """
    addresses_file = sys.argv[1]
    connect_file = sys.argv[2]
    notify_file = sys.argv[3]
    block_file = sys.argv[4]
    monero_ip_file = sys.argv[5]
    tor_ip_file = sys.argv[6]
    ip_info_file = sys.argv[7]
    worldmap = "worldmap.json"
    if len(sys.argv) > 8:
        worldmap = sys.argv[8]
    update_tor_exit_nodes(tor_ip_file)

    (addresses, connects, notifies, blocks) = read_log_filter(addresses_file, connect_file, notify_file, block_file)
    ipinfos = get_ip_info(addresses, monero_ip_file, tor_ip_file, ip_info_file)

    conn_types = connection_types(connects, ipinfos)
    print("Connection types: ")
    print(conn_types)

    with open("conn_types.txt", "w+") as file:
        file.write(str(conn_types) + "\n")

    plot_connection_length(connects)
    plot_notification(notifies)
    plot_connection_timeline(connects)
    plot_blocks_redundancy(blocks)
    plot_location_data(addresses, ipinfos, worldmap)


main()

#!/usr/bin/python3
import sys
import re

IP_REGEX = "\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{1,5}"
GUID_REGEX = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
BLOCK_REGEX = "NOTIFY_NEW_FLUFFY_BLOCK"
BLOCK_HEIGHT_REGEX = "[0-9]{6,9}"
CONNECT_REGEX = "NEW CONNECTION"
DISCONNECT_REGEX = "CLOSE CONNECTION"
REASON_REGEX = "tud.reason"
NOTIFY_REGEX = "NOTIFY_NEW_TRANSACTIONS"
TIMESTAMP_REGEX = "201[8-9]-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{3}"


def parse_file(input_file="", filter_lines="no_filter"):
    """
    Parse the given log file on both notifications and connections.

    The ip addresses set is formatted as follows:
        {   IP_ADDRESS_1,
            IP_ADDRESS_2,
             ...
        }

    The connection list is formatted as follows:
        [   (IP_ADDRESS 1, CONNECT_TIMESTAMP_1, DISCONNECT_TIMESTAMP_1, REASON_1),
            (IP_ADDRESS_1, CONNECT_TIMESTAMP_2, DISCONNECT_TIMESTAMP_2, REASON_2),
            ...,
            (IP_ADDRESS_2, CONNECT_TIMESTAMP_3, DISCONNECT_TIMESTAMP_3, REASON_3),
            ...
        ]

    The notification list is formatted as follows:
        [   (IP_ADDRESS_1, TIMESTAMP_1),
            (IP_ADDRESS_1, TIMESTAMP_2),
            ...,
            (IP_ADDRESS_2, TIMESTAMP_3),
            ...
        ]
    :param input_file:  The file path where the log file is located. (default "")
    :return:            A tuple, containing the ip addresses set, the connection and the notification list
    """
    connect = dict()
    addresses = set()
    notify = list()
    blocks = list()
    with open(input_file, "r") as log_file:
        for line in log_file:
            if (filter_lines != "no_filter" and filter_lines not in line):
                continue;
            # Match to check which type of log message the given line is.
            notify_match = re.search(NOTIFY_REGEX, line, re.S)
            block_match = re.search(BLOCK_REGEX, line, re.S)
            connect_match = re.search(CONNECT_REGEX, line, re.S)
            disconnect_match = re.search(DISCONNECT_REGEX, line, re.S)
            reason_match = re.search(REASON_REGEX, line, re.S)

            if not(block_match or connect_match or disconnect_match or notify_match or reason_match):
                continue

            # Retrieve the timestamp from the given line.
            timestamp_match = re.search(TIMESTAMP_REGEX, line, re.S)
            timestamp = "N/A"
            if timestamp_match:
                timestamp = timestamp_match.group(0)

            # Retrieve the ip address from the given line.
            ip_address_match = re.search(IP_REGEX, line, re.S)
            ip_address = "N/A"
            if ip_address_match:
                ip_address = ip_address_match.group(0)[1:]
                addresses.add(ip_address)

            # Retrieve the GUID from the given line.
            guid_match = re.search(GUID_REGEX, line, re.S)
            guid = "N/A"
            if guid_match:
                guid = guid_match.group(0)

            # Retrieve past connections for the ip address or instantiate empty if there are none found yet.
            guid_pair = ("-", "-", "-")
            ip_connections = {guid: guid_pair}
            if ip_address in connect:
                ip_connections = connect[ip_address]
                if guid in ip_connections:
                    guid_pair = ip_connections[guid]
            else:
                connect[ip_address] = ip_connections

            # When the current line is corresponding to a connection, add it to the respective list.
            if block_match:
                block_height_match = re.search(BLOCK_HEIGHT_REGEX, line, re.S)
                block_height = block_height_match.group(0)
                blocks.append((ip_address, timestamp, block_height))
            elif connect_match:
                ip_connections[guid] = (timestamp, guid_pair[1], guid_pair[2])
            elif disconnect_match:
                ip_connections[guid] = (guid_pair[0], timestamp, guid_pair[2])
            elif reason_match:
                ip_connections[guid] = (guid_pair[0], guid_pair[1], line.split("] ")[1].strip('\n'))
            
            # When the current line is corresponding to a notification, add it to the notification list.
            elif notify_match:
                notify.append((ip_address, timestamp))

    log_file.close()
    connect = [(ip, connection_pair[0], connection_pair[1], connection_pair[2])
               for ip, connection_dict in connect.items() for connection_pair in connection_dict.values()
               if connection_pair[0] != "-" and connection_pair[1] != "-"]

    return addresses, connect, notify, blocks


def write_file(output_file="", csv_description="", elements=None, is_int=False):
    """
    Write the specified tuples in CSV format to the specified output file, using an optional tuple description

    :param output_file:     The file path to which the CSV has to be output. (default "")
    :param csv_description: The description what values are in the tuples, as the first line of the CSV. (default "")
    :param elements:        The values which have to be written to the CSV (default None)
    :param is_int:          Indicate whether the elements are integer or pair
    :return:                None
    """
    if not elements:
        elements = list()
    with open(output_file, "w+") as file:
        if csv_description:
            file.write(csv_description + "\n")
        for element in elements:
            if is_int:
                file.write(element + ",")
            else:
                for value in element:
                    file.write(value + ",")
            file.write("\n")
    file.close()


def main():
    """
    Parse a given Monero log file, retrieving all notifications as well as all connections made.

    Usage: python3 log_filter.py input_path addresses_path connect_path notify_path block_path
    - input_path:       The path to the log file to be parsed.
    - addresses_path:   The path to the file to which the addresses CSV is output.
    - connect_path:     The path to the file to which the connection CSV is output.
    - notify_path:      The path to the file to which the notification CSV is output.
    - block_path:       The path to the file to which the block_height CSV is output.

    The addresses csv is formatted as follows:
    ip-address,

    The connection csv is formatted as follows:
    ip-address,connection-timestamp,disconnection-timestamp,reason,

    The notification csv is formatted as follows:
    timestamp,ip-address,
    :return: None
    """
    input_file = sys.argv[1]
    addresses_file = sys.argv[2]
    connect_file = sys.argv[3]
    notify_file = sys.argv[4]
    block_file = sys.argv[5]
    filter_lines = "no_filter"
    if len(sys.argv) > 6:
        filter_lines = sys.argv[6]
    (addresses, connect, notify, block) = parse_file(input_file, filter_lines)
    write_file(addresses_file, "ip-address,", addresses, True)
    write_file(notify_file, "ip-address,timestamp,", notify, False)
    write_file(connect_file, "ip-address,connection-timestamp,disconnection-timestamp,reason,", connect, False)
    write_file(block_file, "ip-address,timestamp,block-height,", block, False)


if __name__ == "__main__":
    main()

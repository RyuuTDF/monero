#!/usr/bin/python3
import sys
import re

IP_REGEX = "[0-9]{2,3}.[0-9]{2,3}.[0-9]{2,3}.[0-9]{2,3}"
CONNECT_REGEX = "\\bCONNECT-BEP " + IP_REGEX
DISCONNECT_REGEX = "\\bDISCONNECT-BEP " + IP_REGEX
NOTIFY_REGEX = "\\bNOTIFY-BEP " + IP_REGEX
REASON_REGEX = "" + IP_REGEX
TIMESTAMP_REGEX = "201[8-9]-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{3}"


def parse_file(input_file=""):
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
    with open(input_file, "r") as log_file:
        for line in log_file:
            # Match to check which type of log message the given line is.
            connect_match = re.search(CONNECT_REGEX, line, re.S)
            disconnect_match = re.search(DISCONNECT_REGEX, line, re.S)
            notify_match = re.search(NOTIFY_REGEX, line, re.S)
            reason_match = re.search(REASON_REGEX, line, re.S)

            # Retrieve the timestamp from the given line.
            timestamp_match = re.search(TIMESTAMP_REGEX, line, re.S)
            timestamp = "N/A"
            if timestamp_match:
                timestamp = timestamp_match.group(0)

            # Retrieve the ip address from the given line.
            ip_address_match = re.search(IP_REGEX, line, re.s)
            ip_address = "N/A"
            if ip_address_match:
                ip_address = ip_address_match.group(0)
                addresses.add(ip_address)

            # Retrieve past connections for the ip address or instantiate empty if there are none found yet.
            ip_connections = {"connect": list(), "disconnect": list(), "reason": list()}
            try:
                ip_connections = connect[ip_address]
            except KeyError:
                connect[ip_address] = ip_connections

            # When the current line is corresponding to a connection, add it to the respective list.
            if connect_match:
                ip_connections["connect"].append(timestamp)
            elif disconnect_match:
                ip_connections["disconnect"].append(timestamp)
            elif reason_match:
                reason = "TODO"
                ip_connections["reason"].append(reason)

            # When the current line is corresponding to a notification, add it to the notification list.
            elif notify_match:
                ip_address = notify_match.group(0).split(" ")[1]
                notify.append((ip_address, timestamp))

    log_file.close()
    connect = [(value[0], connection) for value in connect.items() for connection in _map_connect(value[1])]
    return addresses, connect, notify


def _map_connect(connections):
    """
    Map a dictionary of connections, disconnections and reason to a list of pairs of connection, disconnection and
    reason.

    The connections list should look as follows:
        {   "connect":  [   TIMESTAMP_1,
                            TIMESTAMP_2,
                            ...
                        ],
            "disconnect":   [   TIMESTAMP_3,
                                TIMESTAMP_4,
                                ...
                            ],
            "reason":   [   REASON_1,
                            REASON_2,
                            ...
                        ]
        }

    The output list will be formatted as follows:
        [   (TIMESTAMP_1, TIMESTAMP_3, REASON_1),
            (TIMESTAMP_2, TIMESTAMP_4, REASON_2)
        ]

    Note that if the list sizes of the input are not of equal length, that incomplete pairs get inserted into the
    output, with "-" as placeholder for the missing input.

    :param connections: dictionary in the format described above
    :return:            output list in the format described above
    """
    connect = connections["connect"]
    disconnect = connections["disconnect"]
    reason = connections["reason"]
    resulting_list = list()
    for index in range(max(len(connect), len(disconnect), len(reason))):
        con = dis = reas = "-"
        if index < len(connect):
            con = connect[index]
        if index < len(disconnect):
            dis = disconnect[index]
        if index < len(reason):
            reas = reason[index]
        resulting_list.append((con, dis, reas))
    return resulting_list


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
                    file.write(value[1] + ",")
            file.write("\n")
    file.close()


def main():
    """
    Parse a given Monero log file, retrieving all notifications as well as all connections made.

    Usage: python3 log_filter.py input_path addresses_path connect_path notify_path
    - input_path:       The path to the log file to be parsed.
    - addresses_path:   The path to the file to which the addresses CSV is output.
    - connect_path:     The path to the file to which the connection CSV is output.
    - notify_path:      The path to the file to which the notification CSV is output.

    The addresses csv is formatted as follows:
    ip-address,

    The connection csv is formatted as follows:
    ip-address,connection-timestamp,disconnection-timestamp,reason

    The notification csv is formatted as follows:
    timestamp,ip-address
    :return: None
    """
    input_file = sys.argv[1]
    addresses_file = sys.argv[2]
    connect_file = sys.argv[3]
    notify_file = sys.argv[4]
    (addresses, connect, notify) = parse_file(input_file)
    write_file(addresses_file, "ip-address,", addresses, True)
    write_file(notify_file, "ip-address,timestamp,", notify, False)
    write_file(connect_file, "ip-address,connection-timestamp,disconnection-timestamp,reason,", connect, False)


main()

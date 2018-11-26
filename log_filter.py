#!/usr/bin/python3
import sys
import re

IP_REGEX = "[0-9]{2,3}.[0-9]{2,3}.[0-9]{2,3}.[0-9]{2,3}"
CONNECT_REGEX = "\\bCONNECT-BEP " + IP_REGEX
DISCONNECT_REGEX = "\\bDISCONNECT-BEP " + IP_REGEX
NOTIFY_REGEX = "\\bNOTIFY-BEP " + IP_REGEX
TIMESTAMP_REGEX = "201[8-9]-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{3}"


def parse_file(input_file=""):
    """
    Parse the given log file on both notifications and connections.

    :param input_file:  The file path where the log file is located. (default "")
    :return:            A tuple, containing a dictionary of connections and a list of notificiations.
    """
    connect = {}
    disconnect = []
    notify = []
    with open(input_file, "r") as log_file:
        for line in log_file:
            connect_match = re.search(CONNECT_REGEX, line, re.S)
            disconnect_match = re.search(DISCONNECT_REGEX, line, re.S)
            notify_match = re.search(NOTIFY_REGEX, line, re.S)
            timestamp_match = re.search(TIMESTAMP_REGEX, line, re.S)
            timestamp = "N/A"
            if timestamp_match:
                timestamp = timestamp_match.group(0)

            if connect_match:
                connect[connect_match.group(0).split(" ")[1]] = (timestamp, "-")
            elif disconnect_match:
                disconnect.append((timestamp, disconnect_match.group(0).split(" ")[1]))
                connection = connect[disconnect_match.group(0).split(" ")[1]]
                connect[disconnect_match.group(0).split(" ")[1]] = (connection[0], timestamp)
            elif notify_match:
                notify.append((timestamp, notify_match.group(0).split(" ")[1]))
    log_file.close()
    return connect, notify


def write_file(output_file="", csv_description="", tuples=None):
    """
    Write the specified tuples in CSV format to the specified output file, using an optional tuple description

    :param output_file:         The file path to which the CSV has to be output. (default "")
    :param csv_description:     The description what values are in the tuples, as the first line of the CSV.
                                (default "")
    :param tuples:              The values which have to be written to the CSV (default None)
    :return:                    None
    """
    if not tuples:
        tuples = []
    with open(output_file, "w+") as file:
        if csv_description:
            file.write(csv_description + "\n")
        for tuple in tuples:
            for value in enumerate(tuple):
                file.write(value[1] + ",")
            file.write("\n")
    file.close()


def main():
    """
    Parse a given Monero log file, retrieving all notifications as well as all connections made.

    Usage: python3 log_filter.py input_path connect_path notify_path
    - input_path:   The path to the log file to be parsed.
    - connect_path: The path to the file to which the connection CSV is output.
    - notify_path:  The path to the file to which the notification CSV is output.

    The connection csv is formatted as follows:
    ip-address,connection-timestamp,disconnection-timestamp

    The notification csv is formatted as follows:
    timestamp,ip-address
    :return: None
    """
    input_file = sys.argv[1]
    connect_file = sys.argv[2]
    notify_file = sys.argv[3]
    (connect, notify) = parse_file(input_file)
    connect = [(connection[0], connection[1][0], connection[1][1]) for connection in connect.items()]
    write_file(notify_file, "timestamp,ip-address,", notify)
    write_file(connect_file, "ip-address,connection-timestamp,disconnection-timestamp,", connect)


main()

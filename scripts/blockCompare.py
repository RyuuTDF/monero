import sys
import csv
import pandas as pd
import numpy as np
from _datetime import datetime


def parse_file(input_normal="",input_tor="", input_b=""):
    #Read in the CSV files of the three nodes.
    #input_normal & input_tor are Ruben's nodes, input_b is Jens' node.
    andf = pd.read_csv(input_normal, parse_dates=['timestamp'], usecols=[1, 2])
    atdf = pd.read_csv(input_tor, parse_dates=['timestamp'], usecols=[1, 2])
    bdf = pd.read_csv(input_b, parse_dates=['timestamp'], usecols=[1, 2])

    #Rename columns for easier referencing after merging.
    andf = andf.rename(columns={'timestamp': 't_anorm'})
    atdf = atdf.rename(columns={'timestamp': 't_ator'})
    bdf = bdf.rename(columns={'timestamp': 't_b'})

    #Group by block-height and only take the lowest timestamp.
    anmin = andf.groupby('block-height').min()
    atmin = atdf.groupby('block-height').min()
    bmin = bdf.groupby('block-height').min()

    #Merge the dataframes into one big dataframe based on intersecting blocks.
    merged = pd.merge(bmin, pd.merge(anmin, atmin, on="block-height"), on="block-height")

    #Calculate the arrival differences.
    merged['at_an'] = merged.t_ator - merged.t_anorm
    merged['at_b'] = merged.t_ator - merged.t_b
    merged['an_b'] = merged.t_anorm - merged.t_b

    print_delta(merged, "at_an")
    print("")
    print_delta(merged, "at_b")
    print("")
    print_delta(merged, "an_b")
    print("")

    return merged


def print_delta(df, c):
    print(c)
    print("Min: {}, Max: {}, Avg: {}".format(df[c].min().total_seconds(), df[c].max().total_seconds(), df[c].mean().total_seconds()))


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

    Usage: python3 log_filter.py input_path addresses_path connect_path notify_path
    - input_path:       The path to the log file to be parsed.
    - addresses_path:   The path to the file to which the addresses CSV is output.
    - connect_path:     The path to the file to which the connection CSV is output.
    - notify_path:      The path to the file to which the notification CSV is output.
    - block_path:      The path to the file to which the block_height CSV is output.

    The addresses csv is formatted as follows:
    ip-address,

    The connection csv is formatted as follows:
    ip-address,connection-timestamp,disconnection-timestamp,reason

    The notification csv is formatted as follows:
    timestamp,ip-address
    :return: None
    """
    input_normal = sys.argv[1]
    input_tor = sys.argv[2]
    input_b = sys.argv[3]
    result_file = "blocktimes.csv"
    results = parse_file(input_normal, input_tor, input_b)
    #write_file(result_file, "block-height,timestamp-normal,timestamp-tor,difference,", results, False)


if __name__ == "__main__":
    main()

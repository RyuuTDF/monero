import sys
import pandas as pd
from log_filter import write_file
from itertools import combinations


def calculate_block_deltas(input_first, input_second):
    """
    Calculate the differences between block arrival times from two input CSVs.

    The CSVs are of the following form:
           ip-address,timestamp,block-height

    For each block height, the timestamps of the earliest block receptions are compared.

    :param input_first:    CSV file describing the block receptions of the first node
    :param input_second:   CSV file describing the block receptions of the second node
    :return:
    """
    df_first = pd.read_csv(input_first, parse_dates=['timestamp'], usecols=[1, 2])
    df_first = df_first.rename(columns={'timestamp': 'timestamp_first'})
    df_first = df_first.groupby('block-height').min()

    df_second = pd.read_csv(input_second, parse_dates=['timestamp'], usecols=[1, 2])
    df_second = df_second.rename(columns={'timestamp': 'timestamp_second'})
    df_second = df_second.groupby('block-height').min()

    merged = pd.merge(df_first, df_second, on="block-height")
    merged["difference"] = merged.timestamp_first - merged.timestamp_second
    return zip(merged.index, merged.timestamp_first - merged.timestamp_second)


def main():
    """
    Create block height difference CSVs for all pairs of given input files.

    Usage: python3 block_compare.py input_file1.csv input_file2.csv ...

    Where input_fileX.csv are all CSV files in the form of:
        ip-address,timestamp,block-height

    For each pair of input_files, a CSV file is created using the following naming scheme:
        input_fileX.csv, input_fileY.csv => XvsY.csv
    """
    output_file = sys.argv[1]
    input_files = []
    for index in range(2, len(sys.argv)):
        input_files.append(sys.argv[index])

    for pair in combinations(input_files, 2):
        results = calculate_block_deltas(pair[0], pair[1])
        write_file(pair[0] + pair[1] + "_.csv", "block-height,difference,", results, False)


if __name__ == "__main__":
    main()

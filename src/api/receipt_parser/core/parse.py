# coding: utf-8

# Copyright 2015-2018
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import time

from terminaltables import SingleTable

from .receipt import Receipt
from .config import read_config
from .parse import *
from os.path import join, dirname
import logging

LOGGER = logging.getLogger("parser_core.parser")
BASE_PATH = join(dirname(__file__))
ORANGE = '\033[33m'
RESET = '\033[0m'

STATS_OUTPUT_FORMAT = "{0:10.0f},{1:d},{2:d},{3:d},{4:d},\n"


def run():
    config = read_config(join(
        dirname(__file__), '../config/config.yml'))

    receipt_files = get_files_in_folder(config.receipts_path)
    return ocr_receipts(config, receipt_files)


def get_files_in_folder(folder, include_hidden=False):
    """
    :param folder: str
        Path to folder to list
    :param include_hidden: bool
        True iff you want also hidden files
    :return: [] of str
        List of full path of files in folder
    """

    files = os.listdir(os.path.join(BASE_PATH, folder)
                       )  # list content of folder
    if not include_hidden:  # avoid files starting with "."
        files = [
            f for f in files if not f.startswith(".")
        ]  #

    files = [
        join(dirname(dirname(__file__)), "data/txt", f) for f in files
    ]  # complete path
    return [
        f for f in files if os.path.isfile(f)
    ]  # just files


def output_statistics(stats, write_file="data/stats.csv"):
    """
    :param stats: {}
        Statistics details
    :param write_file: obj
        str iff you want output file (or else None)
    :return: void
        Prints stats (and eventually writes them)
    """

    stats_str = STATS_OUTPUT_FORMAT.format(
        time.time(), stats["total"], stats["merchant_name"], stats["date"],
        stats["sum"]
    )
    LOGGER.info("Statistics details: " + stats_str)

    if write_file:
        with open(join(dirname(dirname(__file__)), write_file), "a") as stats_file:
            stats_file.write(stats_str)


def percent(numerator, denominator):
    """
    :param numerator: float
        Numerator of fraction
    :param denominator: float
        Denominator of fraction
    :return: str
        Fraction as percentage
    """

    if denominator == 0:
        out = "0"
    else:
        out = str(int(numerator / float(denominator) * 100))

    return out + "%"


def ocr_receipts(config, receipt_files):
    """
    :param config: ObjectView
        Parsed config file
    :param receipt_files: [] of str
        List of files to parse
    :return: {}
        Stats about files
    """

    # stats = defaultdict(int)

    table_data = [
        ['merchant_name', "merchant_phone", "ABN",
            "date", "time", "total", "payment_method"],
    ]

    if config.results_as_json:
        results_to_json(config, receipt_files)

    receipts = []
    for receipt_path in receipt_files:
        with open(receipt_path, encoding="utf8", errors='ignore') as receipt:
            receipt = Receipt(config, receipt.readlines())

            item_list = ""
            for item in receipt.items:
                if not item:
                    continue

                item_list += ' '.join(item) + "\n"

            table_data.append(
                [receipt.merchant_name, receipt.merchant_phone, receipt.merchant_company_reg_no,
                    receipt.date, receipt.time, receipt.total, receipt.payment_method]
            )

        receipts.append({"merchant_name": receipt.merchant_name, "merchant_phone": receipt.merchant_phone, "ABN": receipt.merchant_company_reg_no,
                         "date": receipt.date, "time": receipt.time, "total": receipt.total, "payment_method": receipt.payment_method})

        # stats["total"] += 1
        # if receipt.market:
        #     stats["market"] += 1
        # if receipt.date:
        #     stats["date"] += 1
        # if receipt.sum:
        #     stats["sum"] += 1

    table = SingleTable(table_data)
    LOGGER.info("Parser output:")
    print(table.table)

    return receipts


def results_to_json(config, receipt_files):
    for receipt_path in receipt_files:
        with open(receipt_path, encoding="utf8", errors='ignore') as receipt:
            receipt = Receipt(config, receipt.readlines())
            out = open(receipt_path + ".json", "w")
            out.write(receipt.to_json())
            out.close()

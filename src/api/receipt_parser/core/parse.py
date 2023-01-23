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

TEMP_FOLDER = 'data/txt'


def run(files_name):
    config_path = join(dirname(BASE_PATH), 'config/config.yml')
    config = read_config(config_path)

    receipt_files = []
    for file_name in files_name:
        receipt_files.append(
            join(dirname(BASE_PATH), TEMP_FOLDER, file_name + '.txt'))

    return ocr_receipts(config, receipt_files)


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

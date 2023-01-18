# !/usr/bin/python3
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
import fnmatch
import json
import re
from collections import namedtuple
from difflib import get_close_matches

import dateutil.parser
import requests

ABN_API_BASE_URL = 'http://127.0.0.1:5000/external/abn/search'


def get_name_by_abn(abn):
    response = requests.get('{0}?id={1}'.format(
        ABN_API_BASE_URL, abn)).json()

    return response['merchant_name']


class Receipt(object):
    """ Market receipt to be parsed """

    def __init__(self, config, raw):
        """
        :param config: ObjectView
            Config object
        :param raw: [] of str
            Lines in file
        """

        self.config = config
        self.merchant_name = ""
        self.merchant_address = ""  # complex process, implement later
        self.merchant_phone = ""
        self.merchant_company_reg_no = ""
        self.country = "AU"  # Only support AU at the moment
        self.receipt_no = ""
        self.date = ""
        self.time = ""
        self.items = []
        self.currency = ""
        self.total = ""
        self.subtotal = ""
        self.tax = ""
        self.payment_method = ""
        self.payment_details = ""
        self.credit_card_type = ""
        self.credit_card_number = ""
        self.lines = raw
        self.ocr_confidence = ""
        self.normalize()
        self.parse()

    def normalize(self):
        """
        :return: void
            1) strip empty lines
            2) convert to lowercase
            3) encoding?

        """

        self.lines = [
            line.lower() for line in self.lines if line.strip()
        ]

    def parse(self):
        """
        :return: void
            Parses obj data
        """

        self.merchant_company_reg_no = self.parse_abn()
        if self.merchant_company_reg_no != "":
            self.merchant_name = get_name_by_abn(self.merchant_company_reg_no)

        if self.merchant_name == "":
            self.merchant_name = self.parse_marchant_name()
            if self.merchant_name == "":
                # find "pty. ltd." patten
                # return the line
                pass

        self.merchant_phone = self.parse_phone()

        self.receipt_no = ""  # implement later, kind of complicated
        self.date = self.parse_date()

        if self.time == "":
            self.time = self.parse_time()

        self.items = []  # implement later, kind of complicated
        self.currency = ""  # implement later, not necessary
        self.total = self.parse_total()
        self.subtotal = ""  # implement later, not necessary
        self.tax = ""  # implement later, not necessary
        self.payment_method = self.parse_payment_method()
        self.payment_details = ""  # implement later, not necessary
        self.credit_card_type = ""  # implement later, not necessary
        self.credit_card_number = ""  # implement later, not necessary
        self.ocr_confidence = ""  # implement later, need algorithm

    def fuzzy_find(self, keyword, accuracy=0.6):
        """
        :param keyword: str
            The keyword string to look for
        :param accuracy: float
            Required accuracy for a match of a string with the keyword
        :return: str
            Returns the first line in lines that contains a keyword.
            It runs a fuzzy match if 0 < accuracy < 1.0
        """

        for line in self.lines:
            words = line.split()
            # Get the single best match in line
            matches = get_close_matches(keyword, words, 1, accuracy)
            if matches:
                return line

    def parse_abn(self):
        for abn_key in self.config.merchant_company_reg_no_keys:
            abn_line = self.fuzzy_find(abn_key)
            if abn_line:
                # abn_line = abn_line.replace(' ', '').replace('\n', '')
                abn_line = re.sub('[ \n]', '', abn_line)
                abn_number = re.search(self.config.abn_format, abn_line)

                # TODO
                # useABN checksum algorithm.

                if abn_number:
                    return abn_number.group(0)
        return ""

    def parse_phone(self):
        for phone_key in self.config.phone_keys:
            phone_line = self.fuzzy_find(phone_key)
            if phone_line:
                # phone_line = phone_line.replace('\n', '')
                phone_line = re.sub('[\n]', '', phone_line)

                phone_number = re.search(self.config.phone_format, phone_line)
                if phone_number:
                    return phone_number.group(0)
        return ""

    def parse_time(self):
        for line in self.lines:
            line = re.sub('[!\n ]', '', line)
            match = re.search(self.config.time_format, line)

            if match:
                return match.group(0)

    def parse_date(self):
        """
        :return: date
            Parses data
        """

        for line in self.lines:
            line = re.sub('[!\n]', '', line.upper())
            match = re.search(self.config.numeric_date_format, line) or re.search(
                self.config.string_date_format, line)

            if match:
                # it usually containe time in the same line
                if self.time == "":
                    self.time = re.search(self.config.time_format, line)
                    if self.time == None:
                        self.time = ""
                    else:
                        self.time = self.time.group(0)

                # validate date using the dateutil library (see: https://dateutil.readthedocs.io/)
                date_str = match.group(0)
                date_str = re.sub('[ ]', '', date_str)
                try:
                    date_str = dateutil.parser.parse(
                        date_str, ignoretz=True).date().strftime("%d/%m/%Y")
                except ValueError:
                    return ""

                return date_str

    def parse_payment_method(self):
        for payment_method_key in self.config.payment_method_keys:
            payment_method_line = self.fuzzy_find(payment_method_key)
        return "CASH" if payment_method_line else "CARD"

    def parse_items(self):
        items = []
        item = namedtuple("item", ("article", "sum"))

        ignored_words = self.config.get_config(
            "ignore_keys", self.merchant_name)
        stop_words = self.config.get_config("sum_keys", self.merchant_name)
        item_format = self.config.get_config("item_format", self.merchant_name)

        for line in self.lines:
            parse_stop = None
            for ignore_word in ignored_words:
                parse_stop = fnmatch.fnmatch(line, f"*{ignore_word}*")
                if parse_stop:
                    break

            if parse_stop:
                continue

            if self.merchant_name != "Metro":
                for stop_word in stop_words:
                    if fnmatch.fnmatch(line, f"*{stop_word}*"):
                        return items

            match = re.search(item_format, line)
            if hasattr(match, 'group'):
                article_name = match.group(1)

                if match.group(2) == "-":
                    article_sum = "-" + match.group(3).replace(",", ".")
                else:
                    article_sum = match.group(3).replace(",", ".")
            else:
                continue

            items.append(item(article_name, article_sum))

        return items

    def parse_marchant_name(self):
        """
        :return: str
            Parses market data
        """

        for int_accuracy in range(10, 6, -1):
            accuracy = int_accuracy / 10.0

            min_accuracy, market_match = -1, ""
            for merchant_name, spellings in self.config.merchant_name.items():
                for spelling in spellings:
                    line = self.fuzzy_find(spelling, accuracy)
                    if line and (accuracy < min_accuracy or min_accuracy == -1):
                        min_accuracy = accuracy
                        merchant_name_match = merchant_name
                        return merchant_name_match

        # not found
        return market_match

    def parse_total(self):
        """
        :return: str
            Parses sum data
        """

        for sum_key in self.config.sum_keys:
            sum_line = self.fuzzy_find(sum_key)
            if sum_line:
                # Replace all commas with a dot to make
                # finding and parsing the sum easier
                sum_line = sum_line.replace(",", ".")
                # Parse the sum
                sum_float = re.search(self.config.sum_format, sum_line)
                if sum_float:
                    return sum_float.group(0)

    def to_json(self):
        """
        :return: json
            Convert Receipt object to json
        """
        object_data = {
            "merchant_name": self.merchant_name,
            "abn": self.merchant_company_reg_no,
            "date": self.date,
            "sum": self.sum,
            "items": self.items,
            "lines": self.lines
        }

        return json.dumps(object_data)

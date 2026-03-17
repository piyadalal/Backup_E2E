# encoding: utf-8

from abc import ABC, abstractmethod
import json
import logging
from datetime import datetime
import jsonpath_ng
from jsonpath_ng.exceptions import JsonPathParserError, JsonPathLexerError
import pyperclip
from tableutil import Table, HEADING


def sort_dicts(unsorted,
               hints=None):
    if isinstance(unsorted, list):
        new_object = []
        for item in unsorted:
            if isinstance(item, dict):
                new_object.append(sort_dicts(item,
                                             hints))
            else:
                new_object.append(item)
        return new_object
    elif isinstance(unsorted, dict):
        new_object = {}
        if hints:
            for key, value in unsorted.items():
                if key in hints:
                    new_object[key] = sort_dicts(value,
                                                 hints)
        for key in sorted(unsorted.keys(),
                          key=lambda x: x.lower()):
            if key not in new_object.keys():
                new_object[key] = sort_dicts(unsorted[key],
                                             hints)
        return new_object
    else:
        return unsorted


"""
{
    "eventLog": [
        {
            "action": {
                "id": "01400",
                "dest": {
                    "focusDepth": "1",
                    "interimDetailPageFlag": "false",
                    "path": "guide://qms/sections/SHOWPAGE-SERIES",
                    "screenname": "SP-Funny Woman",
                    "tilePositionX": "10",
                    "tilePositionY": "1"
                },
                "orig": {
                    "focusDepth": "0",
                    "interimDetailPageFlag": "false",
                    "menuPath": "homemenu",
                    "path": "guide://qms/sections/HOME_TILES",
                    "screenname": "Home"
                }
            },
            "details": {
                "version": "1.0"
            },
            "timems": "1676491418100",
            "trigger": {
                "id": "userInput",
                "input": "KeyEvent:Key_SelectKeyReleased",
                "remote": {
                    "batterylevel": 80,
                    "conntype": "",
                    "deviceid": 71,
                    "hwrev": "103.1.0.0",
                    "make": "Remote Solution",
                    "model": "LC103",
                    "name": "P215 SkyQ LC103",
                    "swrev": "5103.2.4"
                }
            }
        }
    ],
    "source": {
        "clientDetails": {
            "device": "TV",
            "hardware": "LT043-f1-ant",
            "platform": "Llama",
            "proposition": "SKYQ",
            "provider": "SKY"
        },
        "customerID": "",
        "locationInHome": "Living Room",
        "msgNumber": 8,
        "region": "UK",
        "serialNumber": "LT01SK02052001704",
        "softwareVersion": "QS015.003.00U",
        "territory": "GBR",
        "trial": "D12",
        "trialSegments": "D12",
        "UIVersion": "20.255.015.02"
    }
}
"""


class BaseAction(ABC):

    PROPERTY = "Property"

    BASE_CHECKS = {}
    ACTION_CHECKS = {}  # Add to subclass

    # Add or override headings and conversions in subclass
    BASE_HEADINGS = []
    HEADINGS = []
    BASE_CONVERSIONS = {}
    CONVERSIONS = {}

    def __init__(self,
                 payload,
                 sort_hints=None,
                 device_name=None,
                 ):
        self.payload = sort_dicts(payload, sort_hints)
        self.extract_payload()
        self._device_name = device_name
        self.headings = []
        self.add_headings(self.BASE_HEADINGS)
        self.add_headings(self.HEADINGS)
        self.conversions = {}
        self.conversions.update(self.BASE_CONVERSIONS)
        self.conversions.update(self.CONVERSIONS)
        self.add_headings(self.BASE_HEADINGS)
        self.add_headings(self.HEADINGS)
        self.table = Table(headings=self.headings,
                           row_numbers=False,
                           conversions=self.conversions,
                           show_column_headings=True)
        self.table.add_row(self._row())

    def extract_payload(self):
        """
        Override this if the event/action
        needs to be extracted from the payload."
        """
        pass

    def copy_to_clipboard(self):
        pyperclip.copy(json.dumps(self.payload,
                                  indent=4))

    @property
    def formatted_payload(self):
        return json.dumps(self.payload,
                          indent=4)

    def log(self,
            log_path):
        log_path.mkdir(parents=True,
                       exist_ok=True)
        filepath = log_path / f"{self.signature}.json"
        with filepath.open(mode='w', encoding='utf-8') as f:
            f.write(self.formatted_payload)

    def add_headings(self,
                     headings):
        for heading in headings:
            try:
                position = [h[HEADING] for h in self.headings].index(heading[HEADING])
            except ValueError:
                self.headings.append(heading)
            else:
                self.headings[position] = heading
        # TODO: Add some checks here for duplicates/missing properties

    @property
    def datetime(self):
        return datetime.fromtimestamp(self.timestamp)

    def _row(self):
        row = {}
        for heading in self.headings:
            property_name = heading.get(self.PROPERTY, heading[HEADING]).lower().replace(" ", "_")
            row[heading[HEADING]] = str(getattr(self, property_name))

        return row
        # return {"device": self.source.get('serialNumber'),
        #         "action": self.event_description,
        #         "trigger": self.trigger_description}

    @property
    def summary(self):
        return self.table.text()

    @property
    def vertical_summary(self):
        # TODO: Make this a Rich Table?
        summary = []
        fields = self._row()
        fields[self.TIMESTAMP] = self.datetime.strftime(u'%Y-%m-%d\n%H:%M:%S')
        print(fields)
        key_width = max([len(k) for k in fields.keys()])

        value_width = max([len(v)
                           if len(v.splitlines()) == 1
                           else max([len(vl)
                                     for vl in v.splitlines()])
                           for v in fields.values()])
        for k, v in fields.items():
            if len(v.splitlines()) == 1:
                summary.append(f'{k:>{key_width}}: {v:<{value_width}}')
            else:
                for index, line in enumerate(v.splitlines()):
                    summary.append(f'{k if index == 0 else " ":>{key_width}}{":" if index == 0 else " "} {line:<{value_width}}')
            summary.append('')
        return '\n'.join(summary)

    def verify_field(self,
                     field,
                     expected):
        """

        :param field: property name or jsonpath string for the field
        :param expected: a value or Checker method
        :return: bool
        """
        try:
            # try and get the value from a property
            actual_value = getattr(self, field)
        except AttributeError:
            try:
                # Currently only handles first match
                actual_value = jsonpath_ng.parse(field).find(self.payload)[0].value
            except (JsonPathLexerError, JsonPathParserError) as e:
                logging.warning(e)
                return False
            except IndexError:
                # Not found
                return False
        try:
            if callable(expected):
                return expected(actual_value)
            elif isinstance(expected, (list, tuple, set)):
                return actual_value in expected
            else:
                return actual_value == expected
        except Exception as e:
            logging.error(e)

    # mirrors verify_request from mock_gcp_server
    def verify_request(self,
                       checks):
        """
        Return true if all checks are positive
        :param checks: a dict of properties to expected values
        :return: bool
        """
        # Base checks are common to all actions
        base_checks = [self.verify_field(field,
                                         value)
                       for field, value in self.BASE_CHECKS.items()]

        # Action checks are specific to individual action id events
        action_checks = [self.verify_field(field,
                                           value)
                         for field, value in self.ACTION_CHECKS.items()]

        # Test case checks are specific to a test case/scenario/workflow/journey
        test_case_checks = [self.verify_field(field,
                                              value)
                            for field, value in checks.items()]

        return all(base_checks) and all(action_checks) and all(test_case_checks)

    # ------------------------------------------------------------------------
    # Abstract methods ...

    @classmethod
    @abstractmethod
    def payload_event_id(cls,
                         payload: dict) -> bool:
        """
        Determine whether the payload can be handled.
        e.g. RDK vs Cherry vs RIFT payloads

        :param payload: dict containing a single action/event
        :return:
        """
        pass

    @property
    @abstractmethod
    def signature(self):
        # Should return a unique action event signature
        pass

    @property
    @abstractmethod
    def device_name(self):
        pass

    @property
    @abstractmethod
    def timestamp(self):
        # Should return a timestamp extracted from the message
        pass
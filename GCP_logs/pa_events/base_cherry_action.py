# encoding: utf-8

from tableutil import Table
from conversionutil import get_datetime_conversion

from .base_action import BaseAction, HEADING


SAMPLE = {
    "experience": "VC",
    "fwVersion": "CH000.022.0U",
    "version": "1.5",
    "eventData": {
        "degree": 0
    },
    "event": "device_tilt",
    "timestampUtc": "1673269184363",
    "pairedSerialNo": "LT02SK721150005BH",
    "serialNo": "VC09SK022210034FN",
    "region": "GBR",
    "packageName": "android.uid.system:1000",
}

INFO_FIELDS = ("experience",
               "fwVersion",
               # "packageName",
               "pairedSerialNo",
               "region",
               "serialNo",
               "version"
               )


class BaseCherryAction(BaseAction):

    PROPERTY = BaseAction.PROPERTY

    TIMESTAMP = "Timestamp"
    DEVICE = "Device"
    ACTION = "Action"
    EVENT_DATA = 'Event Data'

    BASE_HEADINGS = [{HEADING: TIMESTAMP},
                     {HEADING: DEVICE},
                     {HEADING: ACTION, PROPERTY: "event_description"},
                     {HEADING: EVENT_DATA, PROPERTY: "event_data_table"},
                     ]

    HEADINGS = []  # Add or override headings here

    BASE_CONVERSIONS = {TIMESTAMP: get_datetime_conversion(u'%Y-%m-%d\n%H:%M:%S')}
    CONVERSIONS = {}

    # ------------------------------------------------------------------------
    # Overriding abstract methods...

    @classmethod
    def payload_event_id(cls,
                         payload: dict) -> bool:
        try:
            # This identifies the payload as appropriate for this class
            return payload['event']
        except (KeyError, IndexError):
            return False

    @property
    def device_name(self):
        # Implements abstract class method
        return f'{self.platform}_{self.serial_number}' if self._device_name is None else self._device_name

    @property
    def signature(self):
        return f"{self.datetime.strftime(u'%Y%m%d_%H%M%S')}_{self.timestamp_utc}_{self.event}"

    @property
    def timestamp(self):
        return int(self.timestamp_utc) / 1000

    # End of methods overriding abstract methods
    # ------------------------------------------------------------------------

    @property
    def experience(self):
        return self.payload.get('experience')

    @property
    def firmware_version(self):
        return self.payload.get('fwVersion')

    @property
    def version(self):
        return self.payload.get('version')

    @property
    def event(self):
        return self.payload.get('event')

    @property
    def paired_serial_number(self):
        return self.payload.get('pairedSerialNo')

    @property
    def region(self):
        return self.payload.get('region')

    @property
    def package_name(self):
        return self.payload.get('packageName')

    @property
    def timestamp_utc(self):
        return self.payload.get('timestampUtc')

    @property
    def event_data(self):
        return self.payload.get('eventData')

    # ------------------------------------------------------------------------
    # Properties that map to headings...

    @property
    def device(self):
        # return self.source.get('serialNumber')
        return self.device_name

    @property
    def event_description(self):
        return self.event

    @property
    def trigger_description(self):
        return "TBD"

    @property
    def event_data_table(self):
        return Table.init_from_tree(self.event_data)

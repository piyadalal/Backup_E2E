# encoding: utf-8

from tableutil import Table, HEADING
from conversionutil import get_datetime_conversion
from .base_action import BaseAction
from pa_clients._checkers import AnyValue, AnyInteger, Contains
from pa_clients.pa_events import UI_VERSION


class BaseStbAction(BaseAction):

    PROPERTY = BaseAction.PROPERTY

    BASE_CHECKS = {
        # EventLog
        '$.eventLog.[*].action.id': AnyValue(),
        '$.eventLog.[*].timems': AnyValue(),
        # '$.eventLog.[*].details.version': AnyValue(), #TODO: Not in DTH? CHeck against SOIP

        # Source
        '$.source.msgNumber': AnyInteger(),
        '$.source.region': Contains('UK',
                                    'DE',
                                    'IT'),
        '$.source.serialNumber': AnyValue(),     # [expected_sn, expected_sn[:-1]],
        '$.source.softwareVersion': AnyValue(),  # [self.sys_info['modelNumber']],
        UI_VERSION: AnyValue(),
        '$.source.clientDetails.device': Contains('GATEWAYSTB',
                                                  'MULTIROOMSTB',
                                                  'IPSETTOPBOX',
                                                  'HIPSETTOPBOX',
                                                  'TV'),
         # 'clientDetails.hardware': None,  # TODO: re-enable when NGDEV-183829 is fixed
        '$.source.clientDetails.platform': AnyValue(),
        '$.source.clientDetails.proposition': 'SKYQ',
        '$.source.clientDetails.provider': 'SKY',
    }

    TIMESTAMP = "Timestamp"
    DEVICE = "Device"
    ACTION = "Action"
    MESSAGE_NUMBER = "MSG"
    TRIGGER = "Trigger"

    BASE_HEADINGS = [{HEADING: TIMESTAMP},
                     {HEADING: DEVICE},
                     {HEADING: MESSAGE_NUMBER, PROPERTY: "message_number"},
                     {HEADING: ACTION, PROPERTY: "event_description"},
                     {HEADING: TRIGGER, PROPERTY: "trigger_description"},
                     ]

    HEADINGS = []  # Add or override headings here

    BASE_CONVERSIONS = {TIMESTAMP: get_datetime_conversion(u'%Y-%m-%d\n%H:%M:%S')}
    CONVERSIONS = {}

    ACTION_DESCRIPTIONS = {
        "00000": "System Information",
        "00001": "Tune to Linear Channel",
        "00002": "Enter Active Standby",
        "00003": "Exit Active Standby",
        "00004": "Reboot",
        "00005": "Exit Deep Sleep",
        "00020": "Reset",
        "00100": "Exit to Fullscreen Video",
        "00300": "Prompt Notification",
        "00301": "Setting Action",
        "00302": "User Confirmation",
        "00303": "Cherry PiP controls",
        "00310": "Volume",
        "00500": "Mode Entry",
        "00501": "Mode Exit",
        "01000": "Open Mini Guide",
        "01001": "Dismiss Mini Guide",
        "01002": "Browse To Channel",
        "01003": "Filter Browse",
        "01004": "Autoplay Prompt",
        "01010": "Tune Mini TV",
        "01020": "Invoke Channel Category Overlay",
        "01021": "Dismiss Channel Category Overlay",
        "01025": "Invoking Day Selection Overlay",
        "01026": "Dismiss Day Selection Overlay",
        "01030": "Channel Up / Down",
        "01050": "Live TV Review Buffer",
        "01100": "Open Quick Access Menu",
        "01101": "Close Quick Access Menu",
        "01102": "Open PIP Control",
        "01103": "Close PIP Control",
        "01400": "Global Navigation",
        "01403": "Tile Interaction",
        "01404": "Show Page",
        "01410": "Glance Enter",
        "01411": "Glance Exit",
        "01501": "Set-up Favourites Auto Suggest",
        "01502": "Browse to Manage Favourites",
        "01503": "Saving Favourites",
        "01504": "Response to Suggested Channels",
        "01600": "Focus on Text Ribbon",
        "01605": "Text or Voice Search Input",
        "01606": "Voice Search: Action Button",
        "01607": "Voice Action Duration",
        "01608": "Voice Speed Bump Visible",
        "01700": "PIN Protection",
        "01800": "Begin Viewing HDMI",
        "01801": "End Viewing HDMI",
        "01802": "Hot Plug arcDevice",
        "01803": "Unplug arcDevice",
        "01804": "Blocked HDMI",
        "01805": "Hot Plug to USB Port",
        "01806": "Unplug from USB Port",
        "01810": "Connected Bluetooth Audio Devices",
        "01900": "Add to playlist",
        "01901": "Remove from playlist",
        "02000": "Make PVR Booking",
        "02001": "Cancel PVR Booking",
        "02002": "Make “Hot” Recording",
        "02003": "Cancel “Hot” Recording",
        "02004": "Clash Notification",
        "02006": "Cancel “Hot” Series Recording",
        "02010": "Make Series Recording",
        "02011": "Cancel Series Recording",
        "02300": "Keep",
        "02301": "Unkeep",
        "02302": "Delete",
        "02303": "Undelete",
        "02304": "Permanent Delete",
        "02305": "Lock",
        "02306": "Unlock",
        "02400": "Add to Download Queue",
        "02401": "Cancel Download",
        "02410": "Pause Download Queue",
        "02411": "Resume Download Queue",
        "02420": "Move To Top of Download Queue",
        "02450": "Ready To Watch",
        "02500": "Auto Standby Notification",
        "02501": "Auto Standby Notification Ignored",
        "03000": "Playback Start",
        "03001": "Playback Stop",
        "03002": "Playback Blocked",
        "03100": "Persistent PIN",
        "04002": "App Launch",
        "04003": "App Exit",
        "04004": "App Launch Fail",
        "05300": "Rental Confirmation",
        "05348": "Assets Available to Purchase",
        "05349": "Asset Selected to Purchase",
        "05350": "Purchase Confirmed",
        "05355": "Remove Offer Code",
        "06000": "Journey System Navigation",
        "07000": "Promo Notification",
        "09000": "Soundbox Settings",
    }

    # ------------------------------------------------------------------------
    # Overriding concrete methods...

    def extract_payload(self):
        self.payload = self.payload.get('event', self.payload)
        self.source = self.payload.get('source')
        self.event = self.payload.get('eventLog', [{}])[0]

    # ------------------------------------------------------------------------
    # Overriding abstract methods...

    @classmethod
    def payload_event_id(cls,
                         payload: dict) -> bool:
        try:
            return payload.get('event', payload)['eventLog'][0]["action"]["id"]
        except (KeyError, IndexError, TypeError):
            return False

    @property
    def device_name(self):
        # Implements abstract class method
        return '\n'.join([self.platform, self.serial_number]) if self._device_name is None else self._device_name

    @property
    def signature(self):
        return f"{self.datetime.strftime(u'%Y%m%d_%H%M%S')}_{int(self.message_number)}_{self.action_id}"

    @property
    def timestamp(self):
        return self.timestamp_ms / 1000

    # End of methods overriding abstract methods
    # ------------------------------------------------------------------------

    @property
    def action(self):
        return self.event.get("action", {})

    @property
    def action_id(self):
        return self.action.get("id", '?')

    @property
    def action_name(self):
        try:
            return self.ACTION_DESCRIPTIONS[self.action_id]
        except (KeyError, AttributeError):
            return 'Unknown Action'

    @property
    def trigger(self):
        return self.event.get('trigger', {})

    @property
    def trigger_id(self):
        return self.trigger.get('id', '?')

    @property
    def trigger_input(self):
        return self.trigger.get('input')

    @property
    def timestamp_ms(self):
        return int(self.event.get('timems'))

    @property
    def client_details(self):
        return self.source.get('clientDetails', {})

    @property
    def platform(self):
        return self.client_details.get('platform', '')

    @property
    def serial_number(self):
        return self.source.get('serialNumber', '')

    # ------------------------------------------------------------------------
    # Properties that map to headings...

    @property
    def device(self):
        # return self.source.get('serialNumber')
        return self.device_name

    @property
    def message_number(self):
        return self.source.get('msgNumber', '?')

    @property
    def event_description(self):
        return "{action}\n{action_name}".format(action_name=self.action_name,
                                                action=self.action_id)

    @property
    def trigger_description(self):
        if self.trigger_input:
            return "{trigger_id}\n{input}".format(trigger_id=self.trigger_id,
                                                  input=self.trigger_input)
        else:
            return "{trigger_id}".format(trigger_id=self.trigger_id)

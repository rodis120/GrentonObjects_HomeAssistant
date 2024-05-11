import requests
import logging
import voluptuous as vol
from homeassistant.components.switch import (
    SwitchEntity,
    PLATFORM_SCHEMA
)
from homeassistant.const import (STATE_ON, STATE_OFF)

from .const import (
    DOMAIN,
    CONF_API_ENDPOINT,
    CONF_GRENTON_ID,
    CONF_OBJECT_NAME
)
from .utils import get_feature, set_feature

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_ENDPOINT): str,
    vol.Required(CONF_GRENTON_ID): str,
    vol.Optional(CONF_OBJECT_NAME, default='Grenton Switch'): str
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    api_endpoint = config.get(CONF_API_ENDPOINT)
    grenton_id = config.get(CONF_GRENTON_ID)
    object_name = config.get(CONF_OBJECT_NAME)

    add_entities([GrentonSwitch(api_endpoint, grenton_id, object_name)], True)

class GrentonSwitch(SwitchEntity):
    def __init__(self, api_endpoint, grenton_id, object_name):
        self._api_endpoint = api_endpoint
        self._grenton_id = grenton_id
        self._object_name = object_name
        self._state = None
        self._unique_id = f"grenton_{grenton_id.split('->')[1]}"

    @property
    def name(self):
        return self._object_name

    @property
    def is_on(self):
        return self._state == STATE_ON

    @property
    def unique_id(self):
        return self._unique_id

    def turn_on(self, **kwargs):
        try:
            set_feature(self._api_endpoint, self._grenton_id, 0, 1)
            self._state = STATE_ON
        except requests.RequestException as ex:
            _LOGGER.error(f"Failed to turn on the switch: {ex}")

    def turn_off(self, **kwargs):
        try:
            set_feature(self._api_endpoint, self._grenton_id, 0, 0)
            self._state = STATE_OFF
        except requests.RequestException as ex:
            _LOGGER.error(f"Failed to turn off the switch: {ex}")

    def update(self):
        try:
            response = get_feature(self._api_endpoint, self._grenton_id, 0)
            self._state = STATE_OFF if response == 0 else STATE_ON
        except requests.RequestException as ex:
            _LOGGER.error(f"Failed to update the switch state: {ex}")
            self._state = None

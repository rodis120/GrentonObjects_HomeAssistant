import requests
import logging
import voluptuous as vol
from homeassistant.components.cover import (
    CoverEntity,
    PLATFORM_SCHEMA,
    CoverDeviceClass
)
from homeassistant.const import (
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING
)

from .const import (
    DOMAIN,
    CONF_API_ENDPOINT,
    CONF_GRENTON_ID,
    CONF_OBJECT_NAME,
    CONF_REVERSED
)
from .utils import get_features, execute

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_ENDPOINT): str,
    vol.Required(CONF_GRENTON_ID): str,
    vol.Required(CONF_REVERSED, default=False): bool,
    vol.Optional(CONF_OBJECT_NAME, default='Grenton Cover'): str
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    api_endpoint = config.get(CONF_API_ENDPOINT)
    grenton_id = config.get(CONF_GRENTON_ID)
    reversed = config.get(CONF_REVERSED)
    object_name = config.get(CONF_OBJECT_NAME)

    add_entities([GrentonCover(api_endpoint, grenton_id, reversed, object_name)], True)

class GrentonCover(CoverEntity):
    def __init__(self, api_endpoint, grenton_id, reversed, object_name):
        self._device_class = CoverDeviceClass.BLIND
        self._api_endpoint = api_endpoint
        self._grenton_id = grenton_id
        self._reversed = reversed
        self._object_name = object_name
        self._state = None
        self._current_cover_position = None
        self._current_cover_tilt_position = None
        self._unique_id = f"grenton_{grenton_id.split('->')[1]}"
        self._is_zwave = grenton_id.split('->')[1].startswith('ZWA')

    @property
    def name(self):
        return self._object_name

    @property
    def is_closed(self):
        return self._state == STATE_CLOSED

    @property
    def is_opening(self):
        return self._state == STATE_OPENING

    @property
    def is_closing(self):
        return self._state == STATE_CLOSING

    @property
    def current_cover_position(self):
        return self._current_cover_position
    
    @property
    def current_cover_tilt_position(self):
        return self._current_cover_tilt_position

    @property
    def unique_id(self):
        return self._unique_id

    def open_cover(self, **kwargs):
        try:
            execute(self._api_endpoint, self._grenton_id, 0, 0)
            
            self._state = STATE_OPENING
        except requests.RequestException as ex:
            _LOGGER.error(f"Failed to open the cover: {ex}")

    def close_cover(self, **kwargs):
        try:
            execute(self._api_endpoint, self._grenton_id, 1, 0)
            
            self._state = STATE_CLOSING
        except requests.RequestException as ex:
            _LOGGER.error(f"Failed to close the cover: {ex}")

    def stop_cover(self, **kwargs):
        try:
            execute(self._api_endpoint, self._grenton_id, 3, 0)
            
            self._state = STATE_OPEN
        except requests.RequestException as ex:
            _LOGGER.error(f"Failed to stop the cover: {ex}")

    def set_cover_position(self, **kwargs):
        try:
            position = kwargs.get("position", 100)
            self._current_cover_position = position
            if self._reversed == True:
                position = 100 - position
            command = {"command": f"{self._grenton_id.split('->')[0]}:execute(0, '{self._grenton_id.split('->')[1]}:execute(10, {position})')"}
            if self._grenton_id.split('->')[1].startswith("ZWA"):
                command = {"command": f"{self._grenton_id.split('->')[0]}:execute(0, '{self._grenton_id.split('->')[1]}:execute(7, {position})')"}
            response = requests.post(
                f"{self._api_endpoint}",
                json = command
            )
            response.raise_for_status()
            if (position > self._current_cover_position):
                if self._reversed == True:
                    self._state = STATE_CLOSING
                else:
                    self._state = STATE_OPENING
            else:
                if self._reversed == True:
                    self._state = STATE_OPENING
                else:
                    self._state = STATE_CLOSING
        except requests.RequestException as ex:
            _LOGGER.error(f"Failed to set the cover position: {ex}")

    def set_cover_tilt_position(self, **kwargs):
        try:
            tilt_position = kwargs.get("tilt_position", 90)
            self._current_cover_tilt_position = tilt_position
            tilt_position = tilt_position * 90 / 100
            execute(self._api_endpoint, self._grenton_id, 9, tilt_position)
        except requests.RequestException as ex:
            _LOGGER.error(f"Failed to set the cover tilt position: {ex}")

    def open_cover_tilt(self, **kwargs):
        try:
            execute(self._api_endpoint, self._grenton_id, 9, 90)
        except requests.RequestException as ex:
            _LOGGER.error(f"Failed to open the cover tilt: {ex}")

    def close_cover_tilt(self, **kwargs):
        try:
            execute(self._api_endpoint, self._grenton_id, 9, 0)
        except requests.RequestException as ex:
            _LOGGER.error(f"Failed to close the cover tilt: {ex}")

    def update(self):
        try:    
            response = get_features(self._api_endpoint, self._grenton_id, [2, 4, 6] if self._is_zwave else [0, 7, 8])
            
            self._state = STATE_CLOSED if response[1] == 0 else STATE_OPEN
            if response[0] == 1:
                if self._reversed == True:
                    self._state = STATE_CLOSING
                else:
                    self._state = STATE_OPENING
            elif response[0] == 2:
                if self._reversed == True:
                    self._state = STATE_OPENING
                else:
                    self._state = STATE_CLOSING
            temp_position = response[1]
            if self._reversed == True:
                temp_position = 100 - temp_position
            self._current_cover_position = temp_position
            self._current_cover_tilt_position = response[2] * 100 / 90
        except requests.RequestException as ex:
            _LOGGER.error(f"Failed to update the cover state: {ex}")
            self._state = None

import requests
import logging
import voluptuous as vol
from homeassistant.components.climate import (
    ClimateEntity,
    PLATFORM_SCHEMA,
    HVACMode,
    ClimateEntityFeature
)
from homeassistant.const import UnitOfTemperature

from .const import (
    DOMAIN,
    CONF_API_ENDPOINT,
    CONF_GRENTON_ID,
    CONF_OBJECT_NAME
)
from .utils import get_features, send_batch_requests, execute

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_ENDPOINT): str,
    vol.Required(CONF_GRENTON_ID): str,
    vol.Optional(CONF_OBJECT_NAME, default='Grenton Thermostat'): str
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    api_endpoint = config.get(CONF_API_ENDPOINT)
    grenton_id = config.get(CONF_GRENTON_ID)
    object_name = config.get(CONF_OBJECT_NAME)

    add_entities([GrentonClimate(api_endpoint, grenton_id, object_name)], True)

class GrentonClimate(ClimateEntity):
    _enable_turn_on_off_backwards_compatibility = False
    
    def __init__(self, api_endpoint, grenton_id, object_name):
        self._api_endpoint = api_endpoint
        self._grenton_id = grenton_id
        self._name = object_name
        self._current_temperature = None
        self._target_temperature = None
        self._hvac_mode = HVACMode.OFF
        self._hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
        self._unique_id = f"grenton_{grenton_id.split('->')[1]}"
        self._temperature_unit = UnitOfTemperature.CELSIUS
        self._supported_features = (
            ClimateEntityFeature.TURN_ON |
            ClimateEntityFeature.TURN_OFF |
            ClimateEntityFeature.TARGET_TEMPERATURE
        )

    @property
    def name(self):
        return self._name

    @property
    def should_poll(self):
        return True

    @property
    def temperature_unit(self):
        return self._temperature_unit

    @property
    def current_temperature(self):
        return self._current_temperature

    @property
    def target_temperature(self):
        return self._target_temperature

    @property
    def hvac_mode(self):
        return self._hvac_mode

    @property
    def hvac_modes(self):
        return self._hvac_modes

    @property
    def unique_id(self):
        return self._unique_id
    
    @property
    def supported_features(self):
        return self._supported_features

    def set_temperature(self, **kwargs):
        try:
            temperature = kwargs.get("temperature", 20)
            self._target_temperature = temperature
            
            splt = self._grenton_id.split('->')
            commands = [
                f"{splt[0]}:execute(0, '{splt[1]}:set(8, 0)')",
                f"{splt[0]}:execute(0, '{splt[1]}:set(3, {temperature})')"
            ]
            
            send_batch_requests(self._api_endpoint, commands)
            
        except requests.RequestException as ex:
            _LOGGER.error(f"Failed to set the climate temperature: {ex}")

    def set_hvac_mode(self, hvac_mode):
        try:
            self._hvac_mode = hvac_mode
            
            splt = self._grenton_id.split('->')
            if hvac_mode == HVACMode.HEAT:
                commands = [
                    f"{splt[0]}:execute(0, '{splt[1]}:execute(0, 0)')",
                    f"{splt[0]}:execute(0, '{splt[1]}:set(7, 0)')"
                ]
                
                send_batch_requests(self._api_endpoint, commands)
            elif hvac_mode == HVACMode.COOL:
                commands = [
                    f"{splt[0]}:execute(0, '{splt[1]}:execute(0, 0)')",
                    f"{splt[0]}:execute(0, '{splt[1]}:set(7, 1)')"
                ]
                
                send_batch_requests(self._api_endpoint, commands)
            else:
                execute(self._api_endpoint, self._grenton_id, 1, 0)
                
        except requests.RequestException as ex:
            _LOGGER.error(f"Failed to set the climate hvac_mode: {ex}")
        

    def update(self):
        try:
            response = get_features(self._api_endpoint, self._grenton_id, [6, 7, 12, 14])
            
            self._hvac_mode = HVACMode.OFF if response[0] == 0 else (HVACMode.COOL if response[1] == 1 else HVACMode.HEAT)
            self._target_temperature = response[2]
            self._current_temperature = response[3]
        except requests.RequestException as ex:
            _LOGGER.error(f"Failed to update the climate state: {ex}")
            self._state = None

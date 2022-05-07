"""ASUS Router sensors"""

from __future__ import annotations

import logging
_LOGGER = logging.getLogger(__name__)
from numbers import Real
from typing import Any


from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    CONF_INTERFACES,
    DATA_ASUSROUTER,
    DOMAIN,
)

from .dataclass import AsusRouterSensorDescription, AsusRouterAttributeDescription

from .router import KEY_COORDINATOR, KEY_SENSORS_CPU, KEY_SENSORS_MISC, KEY_SENSORS_RAM, KEY_SENSORS_NETWORK_STAT, KEY_SENSORS_DEVICES, AsusRouterObj
from .compilers import list_sensors_network


DEFAULT_PREFIX = "AsusRouter"


SENSORS = {
    ("devices", "number"): AsusRouterSensorDescription(
        key = "number",
        key_group = KEY_SENSORS_DEVICES,
        name = "Connected Devices",
        icon = "mdi:router-network",
        state_class = SensorStateClass.MEASUREMENT,
        entity_category = EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default = True,
    ),
    ("misc", "boottime"): AsusRouterSensorDescription(
        key = "boottime",
        key_group = KEY_SENSORS_MISC,
        name = "Boot Time",
        icon = "mdi:restart",
        device_class = SensorDeviceClass.TIMESTAMP,
        entity_category = EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default = False,
    ),
    ("cpu", "total"): AsusRouterSensorDescription(
        key = "total",
        key_group = KEY_SENSORS_CPU,
        name = "CPU",
        icon = "mdi:cpu-32-bit",
        state_class = SensorStateClass.MEASUREMENT,
        native_unit_of_measurement = PERCENTAGE,
        entity_category = EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default = False,
        extra_state_attributes = {
            "core_1": "Core 1",
            "core_2": "Core 2",
            "core_3": "Core 3",
            "core_4": "Core 4",
            "core_5": "Core 5",
            "core_6": "Core 6",
            "core_7": "Core 7",
            "core_8": "Core 8",
        },
    ),
    ("ram", "usage"): AsusRouterSensorDescription(
        key = "usage",
        key_group = KEY_SENSORS_RAM,
        name = "RAM",
        icon = "mdi:memory",
        state_class = SensorStateClass.MEASUREMENT,
        native_unit_of_measurement = PERCENTAGE,
        entity_category = EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default = False,
        precision = 2,
        extra_state_attributes = {
            "total": "Total",
            "free": "Free",
            "used": "Used",
        },
    ),
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Setup sensors"""

    router: AsusRouterObj = hass.data[DOMAIN][entry.entry_id][DATA_ASUSROUTER]
    entities = []

    SENSORS.update(list_sensors_network(entry.options[CONF_INTERFACES]))

    for sensor_data in router._sensors_coordinator.values():
        coordinator = sensor_data[KEY_COORDINATOR]
        for sensor_description in SENSORS:
            try:
                if sensor_description[0] in sensor_data:
                    if SENSORS[sensor_description].key in sensor_data[sensor_description[0]]:
                        entities.append(AsusRouterSensor(coordinator, router, SENSORS[sensor_description]))
            except Exception as ex:
                _LOGGER.warning(ex)

    async_add_entities(entities, True)


class AsusRouterSensor(CoordinatorEntity, SensorEntity):
    """AsusRouter sensor"""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: AsusRouterObj,
        description: AsusRouterSensorDescription,
    ) -> None:
        """Initialize AsusRouter sensor"""

        super().__init__(coordinator)
        self.entity_description: AsusRouterSensorDescription = description
        self.router = router
        self.coordinator = coordinator

        self._attr_name = "{} {}".format(router._name, description.name)
        self._attr_unique_id = "{} {}".format(DOMAIN, self.name)
        self._attr_device_info = router.device_info
        self._attr_extra_state_attributes = description.extra_state_attributes


    @property
    def native_value(self) -> float | str | None:
        """Return current state"""

        description = self.entity_description
        state = self.coordinator.data.get(description.key)
        if (
            state is not None
            and description.factor
            and isinstance(state, Real)
        ):
            return round(state / description.factor, description.precision)
        return state


    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """"""

        description = self.entity_description
        _extra_state_attributes = description.extra_state_attributes
        if _extra_state_attributes is None:
            return {}

        attrs = {}

        for attr in _extra_state_attributes:
            if attr in self.coordinator.data:
                attrs[_extra_state_attributes[attr]] = self.coordinator.data[attr]

        return attrs


class AsusRouterAttribute(CoordinatorEntity, SensorEntity):
    """AsusRouter attribute"""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        router: AsusRouterObj,
        description: AsusRouterAttributeDescription,
    ) -> None:
        """Initialize AsusRouter attribute"""

        super().__init__(coordinator)
        self.entity_description: AsusRouterSensorDescription = description
        _LOGGER.debug(self.entity_description)

        self._attr_name = "{}".format(self.entity_description.name)
        self._attr_unique_id = "{} {}".format(DOMAIN, self.name)


    @property
    def native_value(self) -> float | str | None:
        """Return current state"""

        description = self.entity_description
        state = self.coordinator.data.get(description.key)
        if (
            state is not None
            and description.factor
            and isinstance(state, Real)
        ):
            return round(state / description.factor, description.precision)
        return state



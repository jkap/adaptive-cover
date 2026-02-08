"""Number platform for the Adaptive Cover integration."""

from __future__ import annotations

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DISTANCE, CONF_SENSOR_TYPE, DOMAIN, SensorType
from .coordinator import AdaptiveDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Adaptive Cover number platform."""
    coordinator: AdaptiveDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    sensor_type = config_entry.data.get(CONF_SENSOR_TYPE)

    # Only create entity for BLIND and AWNING, not TILT
    if sensor_type != SensorType.TILT:
        async_add_entities(
            [AdaptiveCoverNumber(config_entry, config_entry.entry_id, coordinator)]
        )


class AdaptiveCoverNumber(
    CoordinatorEntity[AdaptiveDataUpdateCoordinator], RestoreNumber
):
    """Representation of an Adaptive Cover number entity."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_native_min_value = 0.1
    _attr_native_max_value = 2.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = UnitOfLength.METERS
    _attr_mode = NumberMode.SLIDER
    _attr_translation_key = CONF_DISTANCE
    _attr_icon = "mdi:ruler-square-compass"

    def __init__(
        self,
        config_entry: ConfigEntry,
        unique_id: str,
        coordinator: AdaptiveDataUpdateCoordinator,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = f"{unique_id}_distance_shaded_area"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
        )

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.coordinator.distance_override is not None:
            return self.coordinator.distance_override
        return self._config_entry.options.get(CONF_DISTANCE, 0.5)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self.coordinator.distance_override = value
        await self.coordinator.async_refresh()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Call when entity about to be added to hass."""
        await super().async_added_to_hass()

        last_number_data = await self.async_get_last_number_data()
        if last_number_data and last_number_data.native_value is not None:
            self.coordinator.distance_override = last_number_data.native_value
        else:
            self.coordinator.distance_override = self._config_entry.options.get(
                CONF_DISTANCE, 0.5
            )

        await self.coordinator.async_refresh()

# HomeWizard Vacuum Cleaner for Home Assistant
This integration is based on reverse engineering of the HomeWizard Cleaner app.
It makes the HomeWizard Vacuum Cleaner available in Home Assistant as a device with multiple entities.

The HomeWizard Vacuum Cleaner is a Princess 339000 Robot Vacuum Deluxe which is a simple vacuum robot with support for setting the fan speed, spot cleaning and various extra programs.

## Configuration
1. Add this custom repository to HACS, or manually download the files into your custom_components directory
2. Restart Home Assistant
3. Navigate to integrations and add the HomeWizard Vacuum Cleaner integration through the user interface 
4. Provide HomeWizard username and password

## Entities
This integration exposes the HomeWizard Vacuum Cleaner API through various entities:
- A vacuum entity with battery, clean spot, fan speed, return home, send command, start, state and stop features.
- Sensors for the brush type, raw device status and faults that the device returns.
- A switch to (de)activate the (beeps) sound.
- Entity services for the custom programs (deep clean, edge and random)
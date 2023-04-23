
# Clever API

Home Assistant custom component for Clever EV charger



First flow screen is your Clever email

Second flow screen is is the conformation URL.



Unofficial Clever API

I take no responsibility in using this custom component



This is a beta release - a lot of work is still to be done!

### TODO:


- &#9745; Reauth



Expect breaking changes




### Entities

Entity | Type | Description
-- | -- | --
`sensor.clever_energitillaeg` | Sensor | Energitillæg for this month fetched from Clevers server.
`sensor.clever_energy_this_month` | Sensor | Accumulated kWh this month. Be aware that it counts from when charger is plugged in, not precise when charging over night at shift in month.
`sensor.clever_estimated_total_price_this_month` | Sensor | Estimated price for energitillæg this month (energitillæg * total consumption this month).


### Entities with home charger
Entity | Type | Description
-- | -- | --
`sensor.clever_energitillaeg` | Sensor | Energitillæg for this month fetched from Clevers server.
`sensor.clever_energy_this_month` | Sensor | Accumulated kWh this month. Be aware that it counts from when charger is plugged in, not precise when charging over night at shift in month.
`sensor.clever_estimated_total_price_this_month` | Sensor | Estimated price for energitillæg this month (energitillæg * total consumption this month).
`sensor.clever_energy_this_month_on_box` | Sensor | Accumulated kWh this month from home charger. Be aware that it counts from when charger is plugged in, not precise when charging over night at shift in month.
`sensor.clever_energy_this_charging_session` | Sensor | Amount of charged kWh since car was connect. Update approximately every 5 minutes. Is 0 when unplugged.
`sensor.clever_state_of_charger` | Sensor | Current state of the charger.
`binary_sensor.clever_intelligent_opladning` | Binary sensor | Intelligent opladning turned on or off.
`switch.clever_preheat` | Switch | Allow preheat when Intelligent opladning is turned on.
`switch.clever_skip_intelligent_opladning` | Switch | Skip Intelligent opladning for this session or until turned off.

### Services with home charger
Service| Data| Description
-- | -- | --
`clever_api.enable_flex` | depature_time: format "hh:mm", desired_range: integer in kWh, phase_count: integer in available phases | Setup Intelligent opladning.
`clever_api.disable_flex` | None| Disable Intelligent opladning.

Login flow:



1) Insert your Clever email

![Login picture 1](https://github.com/fars-fede-fire/clever_api/blob/main/cleverfoto/login1.PNG)

Press 'send'



2) You will now recieve a email from Clever asking you to confirm login. Open this email and press the 'bekræft' button

![Login picture 2](https://github.com/fars-fede-fire/clever_api/blob/main/cleverfoto/clevermail.PNG)



3) Copy the URL

![Login picture 3](https://github.com/fars-fede-fire/clever_api/blob/main/cleverfoto/cleverurl.PNG)



4) Insert your Clever mail again and paste the URL

![Login picture 4](https://github.com/fars-fede-fire/clever_api/blob/main/cleverfoto/login2.PNG)


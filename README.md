# Clever API
Home Assistant custom component for Clever EV charger

First flow screen is your Clever email
Second flow screen is your Clever email and second line is the conformation URL.

Unofficial Clever API
I take no responsibility in using this custom component

This is a pre-alpha release - a lot of work is still to be done!
Expect breaking changes

When the custom component is loaded you will have:
 - sensor.clever_consumption_this_month: How many kWh you have charged at home and at public chargers  

 If you check "Add Clever home charger", you will have access to:
 - sensor.clever_current_session_consumption: How many kWh your home charger has charged since car was connect. This is only updated every 15 minutes from Clever  

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
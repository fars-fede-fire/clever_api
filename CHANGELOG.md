# Changelog

## 0.2.4.2 (2023-05-13)
---
 - Deleted a couple of unused fields in the UserInfoData model because of validation errors for some users. These fields were not at use in the integration.

## 0.2.4 (2023-04-22)
---
 - Reauth using options flow.

## 0.2.3 (2023-04-14)
---
 - Fixed bug where integration was out of function when Intelligent Opladning was disabled (unconfirmed if fixed as I can not reproduce)

## 0.2.2 (2023-04-07)
---
 - Now possible to add integration with intelligent opladning disabled

## 0.2.1 (2023-03-24)
---
 - Now possible to add integration without a homecharger
 - `sensor.clever_estimated_total_price_this_month` is no a combination of subscription fee and energitillæg. The energitillæg price without subscription fee is a attribute

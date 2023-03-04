"""Async client for Clever API"""

from __future__ import annotations
from typing import Any, Optional, List
from datetime import date

from pydantic import BaseModel, Field, Extra


class CleverBase(BaseModel):
    """Base object for all Clever backend requests"""

    status: bool
    status_message: str = Field(..., alias="statusMessage")
    timestamp: str


class SendEmail(CleverBase):
    """Object holding send_email data"""


class VerifyLink(CleverBase):
    """Object holding verify_email data"""

    data: Any = None
    secret_code: str


class ObtainUserSecret(CleverBase):
    """Object holding obtain_user_secret data"""

    data: Any = None


class ObtainApiToken(CleverBase):
    """Object holding obtain_api_token data"""

    data: Any = None


class UserInfoData(BaseModel):
    """Object holding data of user info"""

    firstname: str
    lastname: str
    email: str
    id: str
    ch_ade_mo: bool = Field(..., alias="chAdeMO")
    ccs: bool
    type2_slow: bool = Field(..., alias="type2Slow")
    type2_fast: bool = Field(..., alias="type2Fast")
    customer_id: str = Field(..., alias="customerId")
    app_push_token: str = Field(..., alias="appPushToken")
    car_model: str = Field(..., alias="carModel")
    car_make: str = Field(..., alias="carMake")
    car_type_id: str = Field(..., alias="carTypeId")


class UserInfo(CleverBase):
    """Object holding user info."""

    data: UserInfoData


class TransactionsDataRecords(BaseModel, extra=Extra.ignore):
    """Object holding data of transactions"""

    id: str
    charge_point_id: str = Field(..., alias="chargePointId")
    transaction_id: int = Field(..., alias="transactionId")
    start_time_local: int = Field(..., alias="startTimeLocal")
    stop_time_local: int = Field(..., alias="stopTimeLocal")
    start_time_utc: int = Field(..., alias="startTimeUtc")
    stop_time_utc: int = Field(..., alias="stopTimeUtc")
    k_wh: float = Field(..., alias="kWh")


class TransactionsData(BaseModel, extra=Extra.ignore):
    """Object holding data of transactions"""

    is_delta: bool = Field(..., alias="isDelta")
    consumption_records: List[TransactionsDataRecords] = Field(
        ..., alias="consumptionRecords"
    )


class Transactions(CleverBase):
    """Object holding transactions"""

    data: TransactionsData


class EvseInfoDataSmartChargeUserConfig(BaseModel, extra=Extra.ignore):
    """Object holding user configuration of smart charge"""

    status: Any
    car_category: str = Field(..., alias="carCategory")
    departure_time: Any = Field(..., alias="departureTime")
    desired_range: Any = Field(..., alias="desiredRange")
    configured_effect: Any = Field(..., alias="configuredEffect")
    preheat_in_minutes: int = Field(..., alias="preheatInMinutes")
    rules: List


class EvseInfoDataSmartCharge(BaseModel, extra=Extra.ignore):
    """Object holding user configuration of smart charge"""

    user_configuration: EvseInfoDataSmartChargeUserConfig = Field(
        ..., alias="userConfiguration"
    )


class EvseInfoData(BaseModel, extra=Extra.ignore):
    """Object holding Evse data info"""

    installation_id: str = Field(..., alias="installationId")
    charge_box_id: str = Field(..., alias="chargeBoxId")
    connector_id: int = Field(..., alias="connectorId")
    smart_charging_is_enabled: bool = Field(..., alias="smartChargingIsEnabled")
    smart_charging_version: str = Field(..., alias="smartChargingVersion")
    smart_charging_data: Any = Field(..., alias="smartChargingData")
    smart_charging_configuration: EvseInfoDataSmartCharge = Field(
        ..., alias="smartChargingConfiguration"
    )


class EvseStateData(BaseModel, extra=Extra.ignore):
    """Object holding Evse data"""

    transaction_id: int = Field(..., alias="transactionId")
    timestamp: str
    status: str
    consumed_wh: float = Field(..., alias="consumedWh")
    started: str
    postponed_until: str = Field(..., alias="postponedUntil")
    so_c: int = Field(..., alias="soC")


class EvseState(CleverBase):
    """Object holding the state of EVSE state"""

    data: Optional[EvseStateData] = None


class EvseInfo(CleverBase):
    """Object holding Evse info"""

    data: List[EvseInfoData]


class EvseFlexActivate(CleverBase):
    """Object holding response when flex activated"""


class Energitillaeg(BaseModel):
    """Object holding energitillaeg object."""

    raw_energitillaeg: float
    last_day_included: date

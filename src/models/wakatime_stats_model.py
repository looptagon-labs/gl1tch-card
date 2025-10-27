from typing import List, Optional, Union
from pydantic import BaseModel


class GrandTotal(BaseModel):
    decimal: Optional[str]
    digital: Optional[str]
    hours: Optional[int]
    minutes: Optional[int]
    text: Optional[str]
    total_seconds: Optional[float]


class Range(BaseModel):
    start: Optional[str]
    start_date: Optional[str]
    start_text: Optional[str]
    end: Optional[str]
    end_date: Optional[str]
    end_text: Optional[str]
    timezone: Optional[str]


class Category(BaseModel):
    name: str
    total_seconds: float
    percent: Optional[float]
    text: Optional[str] = None


class Editor(BaseModel):
    name: str
    total_seconds: float
    percent: Optional[float]
    text: Optional[str] = None


class Language(BaseModel):
    name: str
    total_seconds: float
    percent: Optional[float]
    text: Optional[str] = None


class Machine(BaseModel):
    name: str
    total_seconds: float
    percent: Optional[float]
    text: Optional[str] = None


class OperatingSystem(BaseModel):
    name: str
    total_seconds: float
    percent: Optional[float]
    text: Optional[str] = None


class Project(BaseModel):
    name: str
    total_seconds: float
    percent: Optional[float]
    text: Optional[str] = None


class WakaDayData(BaseModel):
    # Core fields that exist in both APIs
    total_seconds: Optional[float] = None
    text: Optional[str] = None
    decimal: Optional[str] = None
    digital: Optional[str] = None
    daily_average: Optional[int] = None
    is_up_to_date: Optional[bool] = None
    percent_calculated: Optional[int] = None
    range: Optional[Union[Range, str]] = None 

    # Detailed stats fields (7-day API)
    grand_total: Optional[GrandTotal] = None
    categories: Optional[List[Category]] = []
    editors: Optional[List[Editor]] = []
    languages: Optional[List[Language]] = []
    machines: Optional[List[Machine]] = []
    operating_systems: Optional[List[OperatingSystem]] = []
    projects: Optional[List[Project]] = []
    best_day: Optional[dict] = None
    is_stuck: Optional[bool] = None
    days_minus_holidays: Optional[int] = None
    holidays: Optional[int] = None

    # User info
    user_id: Optional[str] = None
    timezone: Optional[str] = None
    status: Optional[str] = None

    # All-time specific fields
    timeout: Optional[int] = None


class AllTimeStats(BaseModel):
    total_seconds: Optional[float] = None
    text: Optional[str] = None
    decimal: Optional[str] = None
    digital: Optional[str] = None
    daily_average: Optional[int] = None
    is_up_to_date: Optional[bool] = None
    percent_calculated: Optional[int] = None
    range: Optional[Union[Range, str]] = None
    timeout: Optional[int] = None


class WakaStatsResponse(BaseModel):
    data: Union[WakaDayData, AllTimeStats]
    end: Optional[str] = None
    start: Optional[str] = None
    status: Optional[str] = None
    timezone: Optional[str] = None
    writes_only: Optional[bool] = None

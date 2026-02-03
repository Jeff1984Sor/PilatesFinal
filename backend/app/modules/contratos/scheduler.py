from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

SLOT_MINUTES = 50
SLOT_DURATION = timedelta(minutes=SLOT_MINUTES)
SLOT_STEP = timedelta(minutes=SLOT_MINUTES)

TZ = ZoneInfo("America/Sao_Paulo")

WORKING_HOURS = {
    0: (time(7, 0), time(21, 0)),
    1: (time(7, 0), time(21, 0)),
    2: (time(7, 0), time(21, 0)),
    3: (time(7, 0), time(21, 0)),
    4: (time(7, 0), time(12, 0)),
}

PREFERRED_WEEKDAYS = {
    1: [0],
    2: [0, 2],
    3: [0, 2, 4],
    4: [0, 1, 3, 4],
    5: [0, 1, 2, 3, 4],
}


def preferred_weekdays(aulas_por_semana: int) -> list[int]:
    if aulas_por_semana not in PREFERRED_WEEKDAYS:
        raise ValueError("aulas_por_semana deve estar entre 1 e 5")
    return PREFERRED_WEEKDAYS[aulas_por_semana]


def daily_slots(target_date: date, tz: ZoneInfo = TZ) -> list[datetime]:
    weekday = target_date.weekday()
    if weekday not in WORKING_HOURS:
        return []

    start_time, end_time = WORKING_HOURS[weekday]
    start_dt = datetime.combine(target_date, start_time, tzinfo=tz)
    end_dt = datetime.combine(target_date, end_time, tzinfo=tz)

    slots = []
    current = start_dt
    while current + SLOT_DURATION <= end_dt:
        slots.append(current)
        current += SLOT_STEP
    return slots


def week_start_for(target_date: date) -> date:
    return target_date - timedelta(days=target_date.weekday())


def iter_weeks(start_date: date, end_date: date) -> list[date]:
    current = week_start_for(start_date)
    weeks = []
    while current <= end_date:
        weeks.append(current)
        current += timedelta(days=7)
    return weeks

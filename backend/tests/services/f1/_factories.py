"""Helpers to build DataFrames mimicking FastF1 / Ergast return shapes.

Keeping these in one place so tests stay focused on behavior.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pandas as pd


def fastf1_schedule(events: list[dict]) -> pd.DataFrame:
    """Build a FastF1 ``get_event_schedule`` DataFrame.

    Each event dict may set: ``round``, ``name``, ``location``, ``country``,
    ``official_name``, ``event_format``, ``event_date``.
    """
    rows = []
    for i, e in enumerate(events, start=1):
        rows.append({
            "RoundNumber": e.get("round", i),
            "EventName": e.get("name", f"Race {i}"),
            "OfficialEventName": e.get("official_name", e.get("name", f"Race {i} Official")),
            "Location": e.get("location", "Monza"),
            "Country": e.get("country", "Italy"),
            "EventFormat": e.get("event_format", "conventional"),
            "EventDate": e.get("event_date", pd.Timestamp("2024-09-01")),
        })
    return pd.DataFrame(rows)


def fastf1_session_results(rows: list[dict]) -> pd.DataFrame:
    """Build a FastF1 ``session.results`` DataFrame.

    Each row dict may set: ``first_name``, ``last_name``, ``team``,
    ``country_code``, ``driver_number``, ``abbreviation``, ``position``,
    ``grid``, ``points``, ``laps``, ``time``, ``status``.
    """
    out = []
    for r in rows:
        out.append({
            "FirstName": r.get("first_name", "Max"),
            "LastName": r.get("last_name", "Verstappen"),
            "TeamName": r.get("team", "Red Bull Racing"),
            "CountryCode": r.get("country_code", "NED"),
            "DriverNumber": r.get("driver_number", "1"),
            "Abbreviation": r.get("abbreviation", "VER"),
            "Position": r.get("position", 1.0),
            "GridPosition": r.get("grid", 1.0),
            "Points": r.get("points", 25.0),
            "NumberOfLaps": r.get("laps", 50.0),
            "Time": r.get("time", "1:30:00"),
            "Status": r.get("status", "Finished"),
        })
    return pd.DataFrame(out)


def fastf1_session(results_df: pd.DataFrame) -> MagicMock:
    """Build a fake fastf1 session whose ``results`` is the given DataFrame."""
    session = MagicMock()
    session.load = MagicMock()
    session.results = results_df
    return session


def ergast_schedule(events: list[dict]) -> pd.DataFrame:
    """Build an Ergast ``get_race_schedule`` DataFrame.

    Returned empty if ``events`` is empty (mirrors Ergast's empty response).
    """
    if not events:
        return pd.DataFrame()

    rows = []
    for i, e in enumerate(events, start=1):
        rows.append({
            "round": e.get("round", i),
            "raceName": e.get("name", f"Race {i}"),
            "circuitId": e.get("circuit_id", "monza"),
            "circuitName": e.get("circuit_name", "Autodromo Nazionale Monza"),
            "country": e.get("country", "Italy"),
            "locality": e.get("locality", "Monza"),
            "raceDate": e.get("race_date", "1990-09-01"),
        })
    return pd.DataFrame(rows)


def ergast_results_wrapper(df: pd.DataFrame | None) -> MagicMock:
    """Wrap a DataFrame in the Ergast result shape (``.content`` is a list)."""
    wrapper = MagicMock()
    if df is None:
        wrapper.content = []
    else:
        wrapper.content = [df]
    return wrapper


def ergast_race_results(rows: list[dict]) -> pd.DataFrame:
    """Build an Ergast ``get_race_results`` content DataFrame."""
    if not rows:
        return pd.DataFrame()

    out = []
    for r in rows:
        out.append({
            "driverId": r.get("driver_id", "alain_prost"),
            "givenName": r.get("given_name", "Alain"),
            "familyName": r.get("family_name", "Prost"),
            "driverNationality": r.get("driver_nationality", "French"),
            "dateOfBirth": r.get("date_of_birth", "1955-02-24"),
            "constructorId": r.get("constructor_id", "ferrari"),
            "constructorName": r.get("constructor_name", "Ferrari"),
            "constructorNationality": r.get("constructor_nationality", "Italian"),
            "code": r.get("code", "PRO"),
            "number": r.get("number", 1),
            "position": r.get("position", 1),
            "positionText": r.get("position_text", "1"),
            "grid": r.get("grid", 1),
            "points": r.get("points", 9.0),
            "laps": r.get("laps", 70),
            "totalRaceTime": r.get("total_race_time", "1:30:00"),
            "status": r.get("status", "Finished"),
        })
    return pd.DataFrame(out)


def ergast_driver_standings(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    out = []
    for r in rows:
        out.append({
            "driverId": r.get("driver_id", "alain_prost"),
            "givenName": r.get("given_name", "Alain"),
            "familyName": r.get("family_name", "Prost"),
            "driverNationality": r.get("driver_nationality", "French"),
            "position": r.get("position", 1),
            "points": r.get("points", 100.0),
            "wins": r.get("wins", 5),
        })
    return pd.DataFrame(out)


def ergast_constructor_standings(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    out = []
    for r in rows:
        out.append({
            "constructorId": r.get("constructor_id", "ferrari"),
            "constructorName": r.get("constructor_name", "Ferrari"),
            "constructorNationality": r.get("constructor_nationality", "Italian"),
            "position": r.get("position", 1),
            "points": r.get("points", 200.0),
            "wins": r.get("wins", 8),
        })
    return pd.DataFrame(out)


# Convenience for NaN values in test rows
NAN = np.nan

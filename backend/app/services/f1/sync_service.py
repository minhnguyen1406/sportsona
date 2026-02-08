import fastf1
import pandas as pd
from datetime import date
from sqlalchemy.orm import Session
from app.models import (
    Season,
    Driver,
    Constructor,
    DriverEntry,
    Circuit,
    Race,
    RaceResult,
)


class F1DataService:
    def __init__(self, db: Session):
        self.db = db
        fastf1.Cache.enable_cache('/app/cache')

    def _ensure_season(self, year: int) -> Season:
        """Ensure season exists in database."""
        season = self.db.query(Season).filter(Season.year == year).first()
        if not season:
            season = Season(year=year)
            self.db.add(season)
            self.db.flush()
        return season

    def _ensure_circuit(self, circuit_id: str, name: str, country: str = None) -> Circuit:
        """Ensure circuit exists in database."""
        circuit = self.db.query(Circuit).filter(Circuit.circuit_id == circuit_id).first()
        if not circuit:
            circuit = Circuit(
                circuit_id=circuit_id,
                name=name,
                country=country
            )
            self.db.add(circuit)
            self.db.flush()
        return circuit

    def sync_season(self, year: int) -> dict:
        """Sync all data for a season: schedule, drivers, constructors, circuits."""
        self._ensure_season(year)

        # Get schedule and sync circuits + races
        races = self._sync_schedule(year)

        # Get driver/constructor info from first race
        drivers, constructors, entries = self._sync_drivers_and_constructors(year)

        self.db.commit()

        return {
            "year": year,
            "races": len(races),
            "drivers": len(drivers),
            "constructors": len(constructors),
            "driver_entries": len(entries)
        }

    def _sync_schedule(self, year: int) -> list[Race]:
        """Sync race schedule for a given year."""
        schedule = fastf1.get_event_schedule(year)
        races = []

        for _, event in schedule.iterrows():
            # Skip testing events
            if event['EventFormat'] == 'testing':
                continue

            # Create circuit ID
            circuit_id = event['Location'].lower().replace(' ', '_').replace('-', '_')

            # Ensure circuit exists
            self._ensure_circuit(
                circuit_id=circuit_id,
                name=event['OfficialEventName'] if 'OfficialEventName' in event else event['EventName'],
                country=event['Country'] if 'Country' in event else None
            )

            # Check if race exists
            race = self.db.query(Race).filter(
                Race.season == year,
                Race.round == event['RoundNumber']
            ).first()

            event_date = event['EventDate']
            if hasattr(event_date, 'date'):
                event_date = event_date.date()

            if not race:
                race = Race(
                    season=year,
                    round=event['RoundNumber'],
                    name=event['EventName'],
                    circuit_id=circuit_id,
                    date=event_date,
                )
                self.db.add(race)
            else:
                race.name = event['EventName']
                race.circuit_id = circuit_id
                race.date = event_date

            races.append(race)

        self.db.flush()
        return races

    def _sync_drivers_and_constructors(self, year: int) -> tuple[list[Driver], list[Constructor], list[DriverEntry]]:
        """Sync drivers and constructors from the first race of the season."""
        schedule = fastf1.get_event_schedule(year)

        # Find first non-testing event
        first_round = None
        for _, event in schedule.iterrows():
            if event['EventFormat'] != 'testing':
                first_round = event['RoundNumber']
                break

        if first_round is None:
            return [], [], []

        session = fastf1.get_session(year, first_round, 'R')
        session.load()

        drivers = []
        constructors = []
        entries = []
        seen_constructors = set()
        seen_drivers = set()

        for _, result in session.results.iterrows():
            # Sync constructor
            constructor_id = result['TeamName'].lower().replace(' ', '_').replace('-', '_')

            if constructor_id not in seen_constructors:
                constructor = self.db.query(Constructor).filter(
                    Constructor.constructor_id == constructor_id
                ).first()

                if not constructor:
                    constructor = Constructor(
                        constructor_id=constructor_id,
                        name=result['TeamName'],
                    )
                    self.db.add(constructor)
                    constructors.append(constructor)

                seen_constructors.add(constructor_id)

            # Sync driver
            driver_id = f"{result['FirstName']}_{result['LastName']}".lower().replace(' ', '_')

            if driver_id not in seen_drivers:
                driver = self.db.query(Driver).filter(
                    Driver.driver_id == driver_id
                ).first()

                if not driver:
                    driver = Driver(
                        driver_id=driver_id,
                        given_name=result['FirstName'],
                        family_name=result['LastName'],
                        nationality=result.get('CountryCode', None),
                    )
                    self.db.add(driver)
                    drivers.append(driver)

                seen_drivers.add(driver_id)

            # Sync driver entry (driver-team-season relationship)
            self.db.flush()  # Ensure driver and constructor have IDs

            entry = self.db.query(DriverEntry).filter(
                DriverEntry.season == year,
                DriverEntry.driver_id == driver_id,
                DriverEntry.constructor_id == constructor_id
            ).first()

            if not entry:
                entry = DriverEntry(
                    season=year,
                    driver_id=driver_id,
                    constructor_id=constructor_id,
                    driver_number=int(result['DriverNumber']) if result['DriverNumber'] else None,
                    driver_code=result['Abbreviation']
                )
                self.db.add(entry)
                entries.append(entry)

        self.db.flush()
        return drivers, constructors, entries

    def sync_race_results(self, year: int, round_number: int) -> list[RaceResult]:
        """Sync race results for a specific race."""
        session = fastf1.get_session(year, round_number, 'R')
        session.load()

        race = self.db.query(Race).filter(
            Race.season == year,
            Race.round == round_number
        ).first()

        if not race:
            raise ValueError(f"Race not found: {year} round {round_number}")

        results = []

        for _, result in session.results.iterrows():
            driver_id = f"{result['FirstName']}_{result['LastName']}".lower().replace(' ', '_')
            constructor_id = result['TeamName'].lower().replace(' ', '_').replace('-', '_')

            race_result = self.db.query(RaceResult).filter(
                RaceResult.race_id == race.id,
                RaceResult.driver_id == driver_id
            ).first()

            position = result['Position']
            grid = result['GridPosition'] if 'GridPosition' in result else None

            if not race_result:
                race_result = RaceResult(
                    race_id=race.id,
                    driver_id=driver_id,
                    constructor_id=constructor_id,
                    grid_position=int(grid) if grid and not pd.isna(grid) else None,
                    position=int(position) if position and not pd.isna(position) else None,
                    position_text=str(int(position)) if position and not pd.isna(position) else 'R',
                    points=float(result['Points']) if result['Points'] else 0,
                    laps=int(result['NumberOfLaps']) if 'NumberOfLaps' in result and result['NumberOfLaps'] else None,
                    time=str(result['Time']) if pd.notna(result.get('Time')) else None,
                    status=result['Status']
                )
                self.db.add(race_result)

            results.append(race_result)

        self.db.commit()
        return results

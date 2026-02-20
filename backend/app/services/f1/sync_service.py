import fastf1
from fastf1.ergast import Ergast
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
    DriverStanding,
    ConstructorStanding,
)

# Detailed session data available from 2018+
MODERN_ERA_START = 2018


class F1DataService:
    def __init__(self, db: Session):
        self.db = db
        self.ergast = Ergast()
        fastf1.Cache.enable_cache('/app/cache')

    def _ensure_season(self, year: int) -> Season:
        """Ensure season exists in database."""
        season = self.db.query(Season).filter(Season.year == year).first()
        if not season:
            season = Season(year=year)
            self.db.add(season)
            self.db.flush()
        return season

    def _ensure_circuit(self, circuit_id: str, name: str, country: str = None, locality: str = None) -> Circuit:
        """Ensure circuit exists in database."""
        circuit = self.db.query(Circuit).filter(Circuit.circuit_id == circuit_id).first()
        if not circuit:
            circuit = Circuit(
                circuit_id=circuit_id,
                name=name,
                country=country,
                locality=locality
            )
            self.db.add(circuit)
            self.db.flush()
        return circuit

    def _ensure_driver(self, driver_id: str, given_name: str, family_name: str,
                       nationality: str = None, dob: date = None) -> Driver:
        """Ensure driver exists in database."""
        driver = self.db.query(Driver).filter(Driver.driver_id == driver_id).first()
        if not driver:
            driver = Driver(
                driver_id=driver_id,
                given_name=given_name,
                family_name=family_name,
                nationality=nationality,
                date_of_birth=dob
            )
            self.db.add(driver)
            self.db.flush()
        return driver

    def _ensure_constructor(self, constructor_id: str, name: str, nationality: str = None) -> Constructor:
        """Ensure constructor exists in database."""
        constructor = self.db.query(Constructor).filter(
            Constructor.constructor_id == constructor_id
        ).first()
        if not constructor:
            constructor = Constructor(
                constructor_id=constructor_id,
                name=name,
                nationality=nationality
            )
            self.db.add(constructor)
            self.db.flush()
        return constructor

    def sync_season(self, year: int) -> dict:
        """Sync all data for a season."""
        self._ensure_season(year)

        if year >= MODERN_ERA_START:
            return self._sync_modern_season(year)
        else:
            return self._sync_historical_season(year)

    def _sync_modern_season(self, year: int) -> dict:
        """Sync season using modern FastF1 API (2018+)."""
        races = self._sync_schedule_modern(year)
        drivers, constructors, entries = self._sync_drivers_modern(year)
        self.db.commit()

        return {
            "year": year,
            "races": len(races),
            "drivers": len(drivers),
            "constructors": len(constructors),
            "driver_entries": len(entries)
        }

    def _sync_historical_season(self, year: int) -> dict:
        """Sync season using Ergast API (pre-2018)."""
        races = self._sync_schedule_ergast(year)
        drivers, constructors, entries = self._sync_drivers_ergast(year)
        self.db.commit()

        return {
            "year": year,
            "races": len(races),
            "drivers": len(drivers),
            "constructors": len(constructors),
            "driver_entries": len(entries)
        }

    def _sync_schedule_modern(self, year: int) -> list[Race]:
        """Sync race schedule using FastF1 (2018+)."""
        schedule = fastf1.get_event_schedule(year)
        races = []

        for _, event in schedule.iterrows():
            if event['EventFormat'] == 'testing':
                continue

            circuit_id = event['Location'].lower().replace(' ', '_').replace('-', '_')

            self._ensure_circuit(
                circuit_id=circuit_id,
                name=event['OfficialEventName'] if 'OfficialEventName' in event else event['EventName'],
                country=event['Country'] if 'Country' in event else None
            )

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

            races.append(race)

        self.db.flush()
        return races

    def _sync_schedule_ergast(self, year: int) -> list[Race]:
        """Sync race schedule using Ergast API (historical)."""
        schedule = self.ergast.get_race_schedule(year)
        races = []

        if schedule.empty:
            return races

        for _, event in schedule.iterrows():
            circuit_id = event['circuitId']

            self._ensure_circuit(
                circuit_id=circuit_id,
                name=event['circuitName'],
                country=event['country'],
                locality=event['locality']
            )

            race = self.db.query(Race).filter(
                Race.season == year,
                Race.round == event['round']
            ).first()

            race_date = pd.to_datetime(event['raceDate']).date() if pd.notna(event.get('raceDate')) else None

            if not race:
                race = Race(
                    season=year,
                    round=int(event['round']),
                    name=event['raceName'],
                    circuit_id=circuit_id,
                    date=race_date,
                )
                self.db.add(race)

            races.append(race)

        self.db.flush()
        return races

    def _sync_drivers_modern(self, year: int) -> tuple[list[Driver], list[Constructor], list[DriverEntry]]:
        """Sync drivers using FastF1 session data (2018+)."""
        schedule = fastf1.get_event_schedule(year)

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
            constructor_id = result['TeamName'].lower().replace(' ', '_').replace('-', '_')

            if constructor_id not in seen_constructors:
                constructor = self._ensure_constructor(constructor_id, result['TeamName'])
                constructors.append(constructor)
                seen_constructors.add(constructor_id)

            driver_id = f"{result['FirstName']}_{result['LastName']}".lower().replace(' ', '_')

            if driver_id not in seen_drivers:
                driver = self._ensure_driver(
                    driver_id,
                    result['FirstName'],
                    result['LastName'],
                    result.get('CountryCode')
                )
                drivers.append(driver)
                seen_drivers.add(driver_id)

            self.db.flush()

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

    def _sync_drivers_ergast(self, year: int) -> tuple[list[Driver], list[Constructor], list[DriverEntry]]:
        """Sync drivers using Ergast API (historical)."""
        results = self.ergast.get_race_results(year, round=1)

        if not results.content or results.content[0].empty:
            return [], [], []

        drivers = []
        constructors = []
        entries = []
        seen_constructors = set()
        seen_drivers = set()

        for _, result in results.content[0].iterrows():
            constructor_id = result['constructorId']

            if constructor_id not in seen_constructors:
                constructor = self._ensure_constructor(
                    constructor_id,
                    result['constructorName'],
                    result.get('constructorNationality')
                )
                constructors.append(constructor)
                seen_constructors.add(constructor_id)

            driver_id = result['driverId']

            if driver_id not in seen_drivers:
                dob = None
                if pd.notna(result.get('dateOfBirth')):
                    dob = pd.to_datetime(result['dateOfBirth']).date()

                driver = self._ensure_driver(
                    driver_id,
                    result['givenName'],
                    result['familyName'],
                    result.get('driverNationality'),
                    dob
                )
                drivers.append(driver)
                seen_drivers.add(driver_id)

            self.db.flush()

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
                    driver_number=int(result['number']) if pd.notna(result.get('number')) else None,
                    driver_code=result.get('code')
                )
                self.db.add(entry)
                entries.append(entry)

        self.db.flush()
        return drivers, constructors, entries

    def sync_race_results(self, year: int, round_number: int) -> list[RaceResult]:
        """Sync race results for a specific race."""
        if year >= MODERN_ERA_START:
            return self._sync_race_results_modern(year, round_number)
        else:
            return self._sync_race_results_ergast(year, round_number)

    def _sync_race_results_modern(self, year: int, round_number: int) -> list[RaceResult]:
        """Sync race results using FastF1 (2018+)."""
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

    def _sync_race_results_ergast(self, year: int, round_number: int) -> list[RaceResult]:
        """Sync race results using Ergast API (historical)."""
        ergast_results = self.ergast.get_race_results(year, round=round_number)

        if not ergast_results.content or ergast_results.content[0].empty:
            return []

        race = self.db.query(Race).filter(
            Race.season == year,
            Race.round == round_number
        ).first()

        if not race:
            raise ValueError(f"Race not found: {year} round {round_number}")

        results = []

        for _, result in ergast_results.content[0].iterrows():
            driver_id = result['driverId']
            constructor_id = result['constructorId']

            # Ensure driver and constructor exist
            self._ensure_driver(
                driver_id,
                result['givenName'],
                result['familyName'],
                result.get('driverNationality')
            )
            self._ensure_constructor(
                constructor_id,
                result['constructorName'],
                result.get('constructorNationality')
            )

            race_result = self.db.query(RaceResult).filter(
                RaceResult.race_id == race.id,
                RaceResult.driver_id == driver_id
            ).first()

            if not race_result:
                position = result.get('position')
                race_result = RaceResult(
                    race_id=race.id,
                    driver_id=driver_id,
                    constructor_id=constructor_id,
                    grid_position=int(result['grid']) if pd.notna(result.get('grid')) else None,
                    position=int(position) if pd.notna(position) else None,
                    position_text=result.get('positionText', str(position) if pd.notna(position) else 'R'),
                    points=float(result['points']) if pd.notna(result.get('points')) else 0,
                    laps=int(result['laps']) if pd.notna(result.get('laps')) else None,
                    time=result.get('totalRaceTime'),
                    status=result.get('status')
                )
                self.db.add(race_result)

            results.append(race_result)

        self.db.commit()
        return results

    def sync_standings(self, year: int) -> dict:
        """Sync end-of-season driver and constructor standings via Ergast."""
        last_round = (
            self.db.query(Race.round)
            .filter(Race.season == year, Race.date <= date.today())
            .order_by(Race.round.desc())
            .first()
        )
        if not last_round:
            return {"driver_standings": 0, "constructor_standings": 0}

        round_num = last_round[0]

        driver_count = self._sync_driver_standings(year, round_num)
        constructor_count = self._sync_constructor_standings(year, round_num)
        self.db.commit()

        return {
            "round": round_num,
            "driver_standings": driver_count,
            "constructor_standings": constructor_count,
        }

    def _sync_driver_standings(self, year: int, round_num: int) -> int:
        """Sync driver standings for a specific season/round from Ergast."""
        standings_data = self.ergast.get_driver_standings(year, round=round_num)

        if not standings_data.content or standings_data.content[0].empty:
            return 0

        count = 0
        for _, row in standings_data.content[0].iterrows():
            if not pd.notna(row['position']):
                continue

            driver_id = row['driverId']

            self._ensure_driver(
                driver_id,
                row['givenName'],
                row['familyName'],
                row.get('driverNationality'),
            )

            existing = self.db.query(DriverStanding).filter(
                DriverStanding.season == year,
                DriverStanding.round == round_num,
                DriverStanding.driver_id == driver_id,
            ).first()

            if not existing:
                standing = DriverStanding(
                    season=year,
                    round=round_num,
                    driver_id=driver_id,
                    position=int(row['position']),
                    points=float(row['points']) if pd.notna(row['points']) else 0,
                    wins=int(row['wins']) if pd.notna(row['wins']) else 0,
                )
                self.db.add(standing)
                count += 1

        self.db.flush()
        return count

    def _sync_constructor_standings(self, year: int, round_num: int) -> int:
        """Sync constructor standings for a specific season/round from Ergast."""
        standings_data = self.ergast.get_constructor_standings(year, round=round_num)

        if not standings_data.content or standings_data.content[0].empty:
            return 0

        count = 0
        for _, row in standings_data.content[0].iterrows():
            if not pd.notna(row['position']):
                continue

            constructor_id = row['constructorId']

            self._ensure_constructor(
                constructor_id,
                row['constructorName'],
                row.get('constructorNationality'),
            )

            existing = self.db.query(ConstructorStanding).filter(
                ConstructorStanding.season == year,
                ConstructorStanding.round == round_num,
                ConstructorStanding.constructor_id == constructor_id,
            ).first()

            if not existing:
                standing = ConstructorStanding(
                    season=year,
                    round=round_num,
                    constructor_id=constructor_id,
                    position=int(row['position']),
                    points=float(row['points']) if pd.notna(row['points']) else 0,
                    wins=int(row['wins']) if pd.notna(row['wins']) else 0,
                )
                self.db.add(standing)
                count += 1

        self.db.flush()
        return count

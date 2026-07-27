"""Full data import script"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.nba_api_client.player_data import NBAPlayerClient


def import_players():
    """Import all players from NBA API"""
    print("Starting full data import...")
    print("=" * 60)

    client = NBAPlayerClient(delay=1.0)

    # Step 1: Import players
    print("\n[1/4] Importing players...")
    all_players = client.get_all_players()
    print(f"✓ Found {len(all_players)} players")

    # Step 2: Import teams
    print("\n[2/4] Importing teams...")
    from nba_api.stats.statics import teams
    all_teams = teams.get_teams()
    print(f"✓ Found {len(all_teams)} teams")

    # Step 3: Import seasons
    print("\n[3/4] Generating seasons list...")
    seasons = []
    for year in range(1946, 2025):
        season_id = f"{year}-{str(year + 1)[-2:]}"
        seasons.append(season_id)
    print(f"✓ Generated {len(seasons)} seasons (1946-2024)")

    # Step 4: Summary
    print("\n[4/4] Import summary...")
    print(f"  Players: {len(all_players)}")
    print(f"  Teams: {len(all_teams)}")
    print(f"  Seasons: {len(seasons)}")

    print("\n" + "=" * 60)
    print("✓ Data import completed!")
    print("\nNext steps:")
    print("1. Install PostgreSQL and create database 'nba_data'")
    print("2. Configure .env file")
    print("3. Run database migrations: alembic upgrade head")
    print("4. Import data into database (TODO: implement database insertion)")

    return {
        "players": all_players,
        "teams": all_teams,
        "seasons": seasons,
    }


if __name__ == "__main__":
    data = import_players()

    # Show sample data
    print("\n" + "=" * 60)
    print("Sample data:")
    print(f"\nFirst 5 players:")
    for player in data["players"][:5]:
        print(f"  - {player['full_name']} (ID: {player['id']})")

    print(f"\nFirst 5 teams:")
    for team in data["teams"][:5]:
        print(f"  - {team['full_name']} (ID: {team['id']})")

    print(f"\nFirst 5 seasons:")
    for season in data["seasons"][:5]:
        print(f"  - {season}")

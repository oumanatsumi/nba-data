"""NBA API client for fetching player data"""
import time
from typing import List, Dict, Optional
from nba_api.stats.statics import players
from nba_api.stats.endpoints import playercareerstats, playergamelog


class NBAPlayerClient:
    """NBA API client for player data"""

    def __init__(self, delay: float = 1.0):
        """
        Initialize NBA player client

        Args:
            delay: Delay between API requests (seconds) to respect rate limit
        """
        self.delay = delay

    def _rate_limit(self):
        """Apply rate limiting"""
        time.sleep(self.delay)

    def get_all_players(self) -> List[Dict]:
        """
        Get all NBA players

        Returns:
            List of player dictionaries with id, full_name, first_name, last_name, etc.
        """
        self._rate_limit()
        return players.get_players()

    def find_player_by_name(self, name: str) -> Optional[Dict]:
        """
        Find player by name

        Args:
            name: Player name (full or partial)

        Returns:
            Player dictionary or None if not found
        """
        self._rate_limit()
        all_players = players.get_players()
        matches = [p for p in all_players if name.lower() in p['full_name'].lower()]
        return matches[0] if matches else None

    def get_player_career_stats(self, player_id: int) -> Dict:
        """
        Get player career statistics

        Args:
            player_id: NBA player ID

        Returns:
            Career statistics dictionary
        """
        self._rate_limit()
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        return career.get_dict()

    def get_player_game_log(self, player_id: int, season: str) -> Dict:
        """
        Get player game log for a season

        Args:
            player_id: NBA player ID
            season: Season string (e.g., "2023-24")

        Returns:
            Game log dictionary
        """
        self._rate_limit()
        gamelog = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season
        )
        return gamelog.get_dict()


# Example usage
if __name__ == "__main__":
    client = NBAPlayerClient(delay=1.0)

    # Get all players
    all_players = client.get_all_players()
    print(f"Total players: {len(all_players)}")

    # Find LeBron James
    lebron = client.find_player_by_name("LeBron")
    if lebron:
        print(f"Found: {lebron['full_name']} (ID: {lebron['id']})")

        # Get career stats
        career = client.get_player_career_stats(lebron['id'])
        print(f"Career stats retrieved")

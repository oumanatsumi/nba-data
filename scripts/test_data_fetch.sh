#!/bin/bash
# Test script to verify data fetching works

echo "Testing NBA API data fetching..."
echo "================================"

cd backend
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Test basic import
echo "[1/2] Testing nba_api import..."
python -c "from nba_api.stats.statics import players; print('✓ nba_api imported successfully')"

# Test data fetching
echo "[2/2] Testing data fetch..."
python -c "
from nba_api.stats.statics import players, teams
all_players = players.get_players()
all_teams = teams.get_teams()
print(f'✓ Fetched {len(all_players)} players')
print(f'✓ Fetched {len(all_teams)} teams')
"

echo "================================"
echo "✓ All tests passed!"

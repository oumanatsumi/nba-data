export interface Player {
  player_id: number;
  first_name: string;
  last_name: string;
  full_name: string;
  birth_date?: string;
  height_cm?: number;
  weight_kg?: number;
  position?: string;
  country?: string;
  draft_year?: number;
  draft_round?: number;
  draft_number?: number;
  active: boolean;
}

export interface PlayerSeasonStats {
  season_id: string;
  team_id: number;
  games_played?: number;
  minutes_per_game?: number;
  points_per_game?: number;
  rebounds_per_game?: number;
  assists_per_game?: number;
  steals_per_game?: number;
  blocks_per_game?: number;
  field_goal_pct?: number;
  three_point_pct?: number;
  free_throw_pct?: number;
  player_efficiency_rating?: number;
  true_shooting_pct?: number;
  usage_rate?: number;
  win_shares?: number;
  box_plus_minus?: number;
  value_over_replacement_player?: number;
}

export interface Team {
  team_id: number;
  abbreviation: string;
  nickname: string;
  full_name: string;
  city?: string;
  conference?: string;
  division?: string;
  is_active: boolean;
}

export interface TeamSeasonStats {
  season_id: string;
  wins?: number;
  losses?: number;
  win_pct?: number;
  playoff_seed?: number;
}

export interface RosterPlayer {
  player_id: number;
  full_name: string;
  position?: string;
  points_per_game?: number;
  rebounds_per_game?: number;
  assists_per_game?: number;
}

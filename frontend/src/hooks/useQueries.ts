import { useQuery } from "@tanstack/react-query";
import type { Player, PlayerSeasonStats, Team, RosterPlayer, TeamSeasonStats } from "@/types";

const BASE = "/api/v1";

async function fetchJSON(url: string) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export function usePlayerSearch(search: string, page: number) {
  return useQuery({
    queryKey: ["players", search, page],
    queryFn: () =>
      fetchJSON(`${BASE}/players?search=${encodeURIComponent(search)}&limit=20&offset=${(page - 1) * 20}`),
    enabled: search.length >= 1,
  });
}

export function usePlayer(playerId: number) {
  return useQuery({
    queryKey: ["player", playerId],
    queryFn: () => fetchJSON(`${BASE}/players/${playerId}`),
    enabled: !!playerId,
  });
}

export function usePlayerStats(playerId: number) {
  return useQuery({
    queryKey: ["playerStats", playerId],
    queryFn: () => fetchJSON(`${BASE}/players/${playerId}/stats`) as Promise<PlayerSeasonStats[]>,
    enabled: !!playerId,
  });
}

export function useTeams() {
  return useQuery({
    queryKey: ["teams"],
    queryFn: () => fetchJSON(`${BASE}/teams`) as Promise<Team[]>,
  });
}

export function useTeam(teamId: number) {
  return useQuery({
    queryKey: ["team", teamId],
    queryFn: () => fetchJSON(`${BASE}/teams/${teamId}`),
    enabled: !!teamId,
  });
}

export function useTeamStats(teamId: number) {
  return useQuery({
    queryKey: ["teamStats", teamId],
    queryFn: () => fetchJSON(`${BASE}/teams/${teamId}/stats`) as Promise<TeamSeasonStats[]>,
    enabled: !!teamId,
  });
}

export function useTeamRoster(teamId: number, seasonId?: string) {
  return useQuery({
    queryKey: ["teamRoster", teamId, seasonId],
    queryFn: () => {
      const url = seasonId
        ? `${BASE}/teams/${teamId}/roster?season_id=${seasonId}`
        : `${BASE}/teams/${teamId}/roster`;
      return fetchJSON(url) as Promise<RosterPlayer[]>;
    },
    enabled: !!teamId,
  });
}

export function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

// Import useState/useEffect for useDebounce
import { useState, useEffect } from "react";

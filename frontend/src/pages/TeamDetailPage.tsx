import { useParams, useNavigate } from "react-router-dom";
import { useTeam, useTeamStats, useTeamRoster } from "@/hooks/useQueries";
import { ArrowLeft, Loader2 } from "lucide-react";
import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function TeamDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const teamId = Number(id);
  const { data: team, isLoading } = useTeam(teamId);
  const { data: stats } = useTeamStats(teamId);
  const [rosterSeason, setRosterSeason] = useState("2025-26");
  const { data: roster } = useTeamRoster(teamId, rosterSeason);

  if (isLoading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin" size={40} /></div>;
  if (!team) return <div className="text-center py-20 text-muted-foreground">球队不存在</div>;

  const validSeasons = (stats || []).filter(s => s.wins != null && s.wins > 0);
  const winData = validSeasons.map(s => ({ season: s.season_id, wins: s.wins, losses: s.losses }));

  return (
    <div className="max-w-5xl mx-auto">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft size={16} /> 返回
      </button>

      <div className="bg-card border rounded-xl p-6 mb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xl font-bold">🏀</div>
          <div>
            <h1 className="text-3xl font-bold">{team.full_name}</h1>
            <p className="text-muted-foreground">{team.conference || "?"} Conference | {team.division || "?"} | {team.city || ""}</p>
          </div>
        </div>
      </div>

      {winData.length > 0 && (
        <div className="bg-card border rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">历史战绩</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={winData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="season" fontSize={11} />
              <YAxis fontSize={12} />
              <Tooltip />
              <Line type="monotone" dataKey="wins" stroke="#2563eb" strokeWidth={2} dot={false} name="Wins" />
              <Line type="monotone" dataKey="losses" stroke="#dc2626" strokeWidth={2} dot={false} name="Losses" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="bg-card border rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">阵容</h2>
          <select value={rosterSeason} onChange={e => setRosterSeason(e.target.value)}
            className="border rounded px-3 py-1 bg-card text-sm">
            {validSeasons.map(s => <option key={s.season_id} value={s.season_id}>{s.season_id}</option>)}
          </select>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="py-2 pr-4">球员</th><th className="py-2 pr-4">位置</th>
                <th className="py-2 pr-4">PPG</th><th className="py-2 pr-4">RPG</th><th className="py-2 pr-4">APG</th>
              </tr>
            </thead>
            <tbody>
              {(roster || []).map(p => (
                <tr key={p.player_id} className="border-b hover:bg-muted/30 cursor-pointer"
                    onClick={() => navigate(`/players/${p.player_id}`)}>
                  <td className="py-2 pr-4 font-medium">{p.full_name}</td>
                  <td className="py-2 pr-4">{p.position || "-"}</td>
                  <td className="py-2 pr-4">{p.points_per_game != null ? Number(p.points_per_game).toFixed(1) : "-"}</td>
                  <td className="py-2 pr-4">{p.rebounds_per_game != null ? Number(p.rebounds_per_game).toFixed(1) : "-"}</td>
                  <td className="py-2 pr-4">{p.assists_per_game != null ? Number(p.assists_per_game).toFixed(1) : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

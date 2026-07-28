import { useParams, useNavigate } from "react-router-dom";
import { usePlayer, usePlayerStats } from "@/hooks/useQueries";
import { ArrowLeft, Loader2 } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

export default function PlayerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const playerId = Number(id);
  const { data: player, isLoading: pLoading } = usePlayer(playerId);
  const { data: stats, isLoading: sLoading } = usePlayerStats(playerId);

  if (pLoading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin" size={40} /></div>;
  if (!player) return <div className="text-center py-20 text-muted-foreground">球员不存在</div>;

  const chartData = (stats || [])
    .filter((s) => s.games_played && s.games_played > 0)
    .map((s) => ({
      season: s.season_id,
      PPG: s.points_per_game ? Number(s.points_per_game) : null,
      RPG: s.rebounds_per_game ? Number(s.rebounds_per_game) : null,
      APG: s.assists_per_game ? Number(s.assists_per_game) : null,
      PER: s.player_efficiency_rating ? Number(s.player_efficiency_rating) : null,
    }));

  const latest = stats?.[stats.length - 1];

  return (
    <div className="max-w-5xl mx-auto">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft size={16} /> 返回
      </button>

      {/* Profile */}
      <div className="bg-card border rounded-xl p-6 mb-6">
        <h1 className="text-3xl font-bold mb-1">{player.full_name}</h1>
        <p className="text-muted-foreground mb-4">{player.position || "N/A"} | {player.country || "N/A"}</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><span className="text-muted-foreground">身高</span><br />{player.height_cm ? `${player.height_cm} cm` : "-"}</div>
          <div><span className="text-muted-foreground">体重</span><br />{player.weight_kg ? `${player.weight_kg} kg` : "-"}</div>
          <div><span className="text-muted-foreground">选秀</span><br />{player.draft_year ? `${player.draft_year} R${player.draft_round}P${player.draft_number}` : "-"}</div>
          <div><span className="text-muted-foreground">状态</span><br />{player.active ? "🟢 现役" : "⚫ 退役"}</div>
        </div>
      </div>

      {/* Season Stats Table */}
      <div className="bg-card border rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">赛季数据</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="py-2 pr-4">赛季</th><th className="py-2 pr-4">场次</th><th className="py-2 pr-4">PPG</th>
                <th className="py-2 pr-4">RPG</th><th className="py-2 pr-4">APG</th><th className="py-2 pr-4">FG%</th>
                <th className="py-2 pr-4">3P%</th><th className="py-2 pr-4">PER</th><th className="py-2 pr-4">WS</th>
              </tr>
            </thead>
            <tbody>
              {(stats || []).slice().reverse().map((s) => (
                <tr key={s.season_id} className="border-b hover:bg-muted/30">
                  <td className="py-2 pr-4 font-medium">{s.season_id}</td>
                  <td className="py-2 pr-4">{s.games_played || "-"}</td>
                  <td className="py-2 pr-4">{s.points_per_game != null ? Number(s.points_per_game).toFixed(1) : "-"}</td>
                  <td className="py-2 pr-4">{s.rebounds_per_game != null ? Number(s.rebounds_per_game).toFixed(1) : "-"}</td>
                  <td className="py-2 pr-4">{s.assists_per_game != null ? Number(s.assists_per_game).toFixed(1) : "-"}</td>
                  <td className="py-2 pr-4">{s.field_goal_pct != null ? (Number(s.field_goal_pct) * 100).toFixed(1) + "%" : "-"}</td>
                  <td className="py-2 pr-4">{s.three_point_pct != null ? (Number(s.three_point_pct) * 100).toFixed(1) + "%" : "-"}</td>
                  <td className="py-2 pr-4">{s.player_efficiency_rating != null ? Number(s.player_efficiency_rating).toFixed(1) : "-"}</td>
                  <td className="py-2 pr-4">{s.win_shares != null ? Number(s.win_shares).toFixed(1) : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Career Trend Chart */}
      {chartData.length > 1 && (
        <div className="bg-card border rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">生涯趋势</h2>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="season" fontSize={12} />
              <YAxis fontSize={12} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="PPG" stroke="#2563eb" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="RPG" stroke="#16a34a" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="APG" stroke="#dc2626" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

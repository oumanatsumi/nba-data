import { useTeams } from "@/hooks/useQueries";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";

function ShieldIcon({ size, className }: { size: number; className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.06 1.06 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>
    </svg>
  );
}

export default function TeamListPage() {
  const { data: teams, isLoading } = useTeams();
  const navigate = useNavigate();
  if (isLoading) return <div className="flex justify-center py-20"><Loader2 className="animate-spin" size={40} /></div>;
  const east = (teams || []).filter(t => t.conference === "East");
  const west = (teams || []).filter(t => t.conference === "West");
  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">球队</h1>
      {["东部联盟", "西部联盟"].map((label, idx) => {
        const conf = idx === 0 ? east : west;
        return (
          <div key={label} className="mb-8">
            <h2 className="text-lg font-semibold mb-3 text-muted-foreground">{label} ({conf.length})</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {conf.map(t => (
                <div key={t.team_id} onClick={() => navigate(`/teams/${t.team_id}`)}
                  className="p-4 rounded-lg border bg-card hover:bg-muted/50 cursor-pointer transition-colors text-center">
                  <ShieldIcon size={24} className="mx-auto mb-2 text-primary" />
                  <div className="font-semibold text-sm">{t.abbreviation}</div>
                  <div className="text-xs text-muted-foreground">{t.nickname}</div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

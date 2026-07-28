import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useDebounce } from "@/hooks/useQueries";
import type { Player } from "@/types";
import { Search, Loader2, User } from "lucide-react";

const BASE = "/api/v1";

export default function PlayerSearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Player[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const debouncedQuery = useDebounce(query, 300);
  const navigate = useNavigate();

  useEffect(() => {
    if (!debouncedQuery) { setResults([]); setTotal(0); return; }
    let cancelled = false;
    setLoading(true);
    fetch(`${BASE}/players?search=${encodeURIComponent(debouncedQuery)}&limit=20&offset=${(page - 1) * 20}`)
      .then(r => r.json())
      .then(data => { if (!cancelled) { setResults(data.players || []); setTotal(data.total || 0); } })
      .catch(() => { if (!cancelled) setResults([]); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [debouncedQuery, page]);

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">球员搜索</h1>
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={20} />
        <input
          type="text" placeholder="输入球员姓名..."
          className="w-full pl-10 pr-4 py-3 rounded-lg border bg-card focus:outline-none focus:ring-2 focus:ring-primary"
          value={query} onChange={(e) => { setQuery(e.target.value); setPage(1); }}
        />
      </div>
      {loading && <div className="flex justify-center py-12"><Loader2 className="animate-spin" size={32} /></div>}
      {!loading && results.length === 0 && query && (
        <div className="text-center py-12 text-muted-foreground">未找到匹配的球员</div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {results.map(p => (
          <div key={p.player_id} onClick={() => navigate(`/players/${p.player_id}`)}
            className="flex items-center gap-4 p-4 rounded-lg border bg-card hover:bg-muted/50 cursor-pointer transition-colors">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center"><User size={20} className="text-primary" /></div>
            <div>
              <div className="font-semibold">{p.full_name}</div>
              <div className="text-sm text-muted-foreground">{p.first_name} {p.last_name}</div>
            </div>
          </div>
        ))}
      </div>
      {total > 20 && (
        <div className="flex justify-center gap-2 mt-6">
          {Array.from({ length: Math.min(Math.ceil(total / 20), 10) }, (_, i) => (
            <button key={i} onClick={() => setPage(i + 1)}
              className={`px-3 py-1 rounded ${page === i + 1 ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`}>
              {i + 1}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

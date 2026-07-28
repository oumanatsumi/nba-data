import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/layout/Layout";
import PlayerSearchPage from "./pages/PlayerSearchPage";
import PlayerDetailPage from "./pages/PlayerDetailPage";
import TeamListPage from "./pages/TeamListPage";
import TeamDetailPage from "./pages/TeamDetailPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/players" replace />} />
        <Route path="/players" element={<PlayerSearchPage />} />
        <Route path="/players/:id" element={<PlayerDetailPage />} />
        <Route path="/teams" element={<TeamListPage />} />
        <Route path="/teams/:id" element={<TeamDetailPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-96">
      <h1 className="text-4xl font-bold mb-4">404</h1>
      <p className="text-muted-foreground">Page not found</p>
    </div>
  );
}

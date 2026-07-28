import { NavLink } from "react-router-dom";
import { Users, Shield, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

export default function Sidebar() {
  const [dark, setDark] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("theme") === "dark" ||
        (!localStorage.getItem("theme") && window.matchMedia("(prefers-color-scheme: dark)").matches);
    }
    return false;
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
      isActive ? "bg-primary text-primary-foreground" : "hover:bg-muted"
    }`;

  return (
    <aside className="fixed left-0 top-0 h-full w-60 border-r bg-card flex flex-col z-10">
      <div className="p-5 border-b">
        <h1 className="text-xl font-bold flex items-center gap-2">
          🏀 NBA Data
        </h1>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        <NavLink to="/players" className={linkClass}>
          <Users size={18} /> 球员
        </NavLink>
        <NavLink to="/teams" className={linkClass}>
          <Shield size={18} /> 球队
        </NavLink>
      </nav>

      <div className="p-3 border-t">
        <button
          onClick={() => setDark(!dark)}
          className="flex items-center gap-3 px-4 py-2.5 rounded-lg w-full hover:bg-muted transition-colors"
        >
          {dark ? <Sun size={18} /> : <Moon size={18} />}
          {dark ? "亮色模式" : "暗色模式"}
        </button>
      </div>
    </aside>
  );
}

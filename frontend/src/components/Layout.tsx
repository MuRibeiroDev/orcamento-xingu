import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { LayoutDashboard, Users, Package, Settings, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { to: "/", label: "Início", icon: LayoutDashboard, end: true },
  { to: "/clientes", label: "Agências", icon: Users, end: false },
  { to: "/catalogo", label: "Catálogo", icon: Package, end: false },
  { to: "/configuracoes", label: "Configurações", icon: Settings, end: false },
];

export function Layout() {
  const navigate = useNavigate();

  function sair() {
    localStorage.removeItem("token");
    navigate("/login");
  }

  return (
    <div className="flex min-h-screen bg-muted/30">
      <aside className="flex w-60 flex-col border-r bg-background">
        <div className="flex items-center gap-3 border-b px-6 py-5">
          <img src="/assets/logo-xingu.png" alt="XINGU" className="h-10 w-10 object-contain" />
          <div>
            <div className="text-sm font-semibold leading-tight">XINGU</div>
            <div className="text-xs text-muted-foreground">Orçamentos</div>
          </div>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )
              }
            >
              <l.icon className="h-4 w-4" />
              {l.label}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={sair}
          className="flex items-center gap-3 border-t px-6 py-4 text-sm text-muted-foreground hover:text-foreground"
        >
          <LogOut className="h-4 w-4" />
          Sair
        </button>
      </aside>
      <main className="flex-1 overflow-x-hidden">
        <div className="mx-auto max-w-6xl p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

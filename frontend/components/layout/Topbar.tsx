import Link from "next/link";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/alunos", label: "Alunos" },
  { href: "/profissionais", label: "Profissionais" },
  { href: "/planos", label: "Planos" },
  { href: "/contratos", label: "Contratos" },
  { href: "/contratos/modelos", label: "Modelo de Contrato" },
  { href: "/agenda", label: "Agenda" },
  { href: "/financeiro", label: "Financeiro" },
  { href: "/configuracoes", label: "Configuracoes" }
];

export default function Topbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-black/5 bg-white/70 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-sky-400 to-coral" />
          <div>
            <p className="text-xs uppercase tracking-widest text-gray-500">Studio</p>
            <h2 className="text-xl font-display">Pilates</h2>
          </div>
        </div>
        <nav className="flex flex-1 items-center gap-2 overflow-x-auto px-2 text-sm">
          {links.map((link) => (
            <Link
              key={link.href}
              className="whitespace-nowrap rounded-full px-3 py-1 hover:bg-black/5"
              href={link.href}
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <div className="rounded-full bg-white/80 px-3 py-1 text-xs">Hoje: agenda ativa</div>
          <div className="text-right">
            <p className="text-sm font-medium">Admin</p>
            <p className="text-xs text-gray-500">studio@pilates.local</p>
          </div>
        </div>
      </div>
    </header>
  );
}

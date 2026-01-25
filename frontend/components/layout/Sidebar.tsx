import Link from "next/link";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/alunos", label: "Alunos" },
  { href: "/profissionais", label: "Profissionais" },
  { href: "/planos", label: "Planos" },
  { href: "/contratos", label: "Contratos" },
  { href: "/agenda", label: "Agenda" },
  { href: "/financeiro", label: "Financeiro" },
  { href: "/configuracoes", label: "Configuracoes" }
];

export default function Sidebar() {
  return (
    <aside className="p-6 bg-white/60 backdrop-blur border-r border-black/5">
      <div className="mb-8">
        <p className="text-xs uppercase tracking-widest text-gray-500">Studio</p>
        <h2 className="text-2xl font-display">Pilates</h2>
      </div>
      <nav className="space-y-2">
        {links.map((link) => (
          <Link key={link.href} className="block rounded-xl px-3 py-2 hover:bg-black/5" href={link.href}>
            {link.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}

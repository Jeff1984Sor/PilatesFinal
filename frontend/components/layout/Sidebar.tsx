import Link from "next/link";

const sections = [
  {
    title: "Principal",
    items: [
      { href: "/", label: "Dashboard" },
      { href: "/agenda", label: "Agenda" },
      { href: "/contratos", label: "Contratos" }
    ]
  },
  {
    title: "Pessoas",
    items: [
      { href: "/alunos", label: "Alunos" },
      { href: "/profissionais", label: "Profissionais" }
    ]
  },
  {
    title: "Cadastros",
    items: [
      { href: "/cadastros/unidades/", label: "Unidades" },
      { href: "/cadastros/planos/", label: "Planos" },
      { href: "/cadastros/tipos-servico/", label: "Tipos de Servico" },
      { href: "/cadastros/termos/", label: "Modelos de Termo" },
      { href: "/cadastros/categorias/", label: "Categorias" },
      { href: "/cadastros/subcategorias/", label: "Subcategorias" },
      { href: "/contratos/modelos/", label: "Modelos de Contrato" },
      { href: "/evolucoes/modelos/", label: "Modelos de Evolucao" }
    ]
  },
  {
    title: "Financeiro",
    items: [
      { href: "/financeiro", label: "Visao geral" },
      { href: "/financeiro/contas-receber/", label: "Contas a Receber" },
      { href: "/financeiro/contas-pagar/", label: "Contas a Pagar" },
      { href: "/financeiro/conta-bancaria/", label: "Conta Bancaria" },
      { href: "/financeiro/dre/", label: "DRE" }
    ]
  },
  {
    title: "Config",
    items: [
      { href: "/configuracoes", label: "Configuracoes" },
      { href: "/configuracoes/whatsapp/", label: "WhatsApp" },
      { href: "/configuracoes/email/", label: "Email" },
      { href: "/configuracoes/totalpass/", label: "TotalPass" }
    ]
  }
];

export default function Sidebar() {
  return (
    <aside className="p-6 bg-white/60 backdrop-blur border-r border-black/5">
      <div className="mb-8">
        <p className="text-xs uppercase tracking-widest text-gray-500">Studio</p>
        <h2 className="text-2xl font-display">Pilates</h2>
      </div>
      <nav className="space-y-6">
        {sections.map((section) => (
          <div key={section.title}>
            <div className="mb-2 text-[11px] uppercase tracking-[0.24em] text-gray-400">{section.title}</div>
            <div className="space-y-1">
              {section.items.map((link) => (
                <Link key={link.href} className="block rounded-xl px-3 py-2 hover:bg-black/5" href={link.href}>
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}

import AppShell from "@/components/layout/AppShell";
import Link from "next/link";

export default function Page() {
  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <p className="text-sm uppercase tracking-widest text-gray-500">Dashboard</p>
          <h1 className="text-4xl font-display">Studio overview</h1>
        </div>
        <div className="card-grid">
          <div className="rounded-2xl bg-white/70 p-4 shadow-sm">
            <p className="text-sm text-gray-500">Alunos ativos</p>
            <p className="text-3xl font-semibold">128</p>
          </div>
          <div className="rounded-2xl bg-white/70 p-4 shadow-sm">
            <p className="text-sm text-gray-500">Aulas hoje</p>
            <p className="text-3xl font-semibold">24</p>
          </div>
          <div className="rounded-2xl bg-white/70 p-4 shadow-sm">
            <p className="text-sm text-gray-500">Recebimentos</p>
            <p className="text-3xl font-semibold">R$ 6.540</p>
          </div>
        </div>
        <div className="flex gap-4">
          <Link className="rounded-full bg-black px-4 py-2 text-white" href="/agenda">
            Abrir agenda
          </Link>
          <Link className="rounded-full bg-white/70 px-4 py-2" href="/alunos">
            Ver alunos
          </Link>
        </div>
      </div>
    </AppShell>
  );
}

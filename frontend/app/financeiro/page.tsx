import AppShell from "@/components/layout/AppShell";

export default function Page() {
  return (
    <AppShell>
      <div className="space-y-4">
        <h1 className="text-3xl font-display">Financeiro</h1>
        <div className="rounded-2xl bg-white/70 p-6">
          <p className="text-sm text-gray-600">Conteudo inicial de financeiro</p>
        </div>
      </div>
    </AppShell>
  );
}

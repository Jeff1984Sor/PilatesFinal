"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import AppShell from "@/components/layout/AppShell";
import api from "@/lib/api";

type Usuario = {
  id: number;
  email: string;
  perfil_acesso_id: number;
  profissional_id: number | null;
  ativo: boolean;
};

type Perfil = { id: number; descricao: string };

type Comissao = {
  id: number;
  profissional_id: number;
  conta_receber_id: number | null;
  contrato_id: number | null;
  competencia: string;
  valor_base: number;
  percentual: number;
  valor: number;
  status: string;
  pago_em: string | null;
};

type ResumoItem = {
  profissional_id: number;
  profissional_nome: string;
  quantidade: number;
  valor_pendente: number;
  valor_pago: number;
  valor_total: number;
};

type Resumo = {
  competencia: string | null;
  itens: ResumoItem[];
  valor_total: number;
};

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

function competenciaAtual() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export default function Page() {
  const queryClient = useQueryClient();
  const [competencia, setCompetencia] = useState(competenciaAtual());

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: async () => (await api.get<Usuario>("/auth/me")).data
  });

  const perfisQuery = useQuery({
    queryKey: ["perfis"],
    queryFn: async () => (await api.get<Perfil[]>("/auth/perfis")).data
  });

  const isAdmin = useMemo(() => {
    const perfil = perfisQuery.data?.find((p) => p.id === meQuery.data?.perfil_acesso_id);
    return perfil?.descricao === "admin";
  }, [perfisQuery.data, meQuery.data]);

  const resumoQuery = useQuery({
    queryKey: ["comissoes-resumo", competencia],
    enabled: !!meQuery.data,
    queryFn: async () =>
      (await api.get<Resumo>("/comissoes/resumo", { params: { competencia } })).data
  });

  const comissoesQuery = useQuery({
    queryKey: ["comissoes", competencia],
    enabled: !!meQuery.data,
    queryFn: async () =>
      (await api.get<Comissao[]>("/comissoes", { params: { competencia } })).data
  });

  const gerarMutation = useMutation({
    mutationFn: async () => api.post("/comissoes/gerar", { competencia }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["comissoes-resumo"] });
      queryClient.invalidateQueries({ queryKey: ["comissoes"] });
    }
  });

  const pagarMutation = useMutation({
    mutationFn: async (id: number) => api.post(`/comissoes/${id}/pagar`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["comissoes-resumo"] });
      queryClient.invalidateQueries({ queryKey: ["comissoes"] });
    }
  });

  const resumo = resumoQuery.data;
  const comissoes = comissoesQuery.data ?? [];
  const nomePorProf = useMemo(() => {
    const map = new Map<number, string>();
    resumo?.itens.forEach((i) => map.set(i.profissional_id, i.profissional_nome));
    return map;
  }, [resumo]);

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-widest text-gray-500">Financeiro</p>
            <h1 className="text-3xl font-display">Valor a pagar — Profissionais</h1>
          </div>
          <div className="flex items-end gap-3">
            <label className="text-sm">
              Competencia
              <input
                type="month"
                className="mt-1 block rounded-xl border border-black/10 p-2"
                value={competencia}
                onChange={(e) => setCompetencia(e.target.value)}
              />
            </label>
            {isAdmin && (
              <button
                className="rounded-full bg-black px-4 py-2 text-white disabled:opacity-50"
                onClick={() => gerarMutation.mutate()}
                disabled={gerarMutation.isPending}
              >
                {gerarMutation.isPending ? "Gerando..." : "Gerar comissoes"}
              </button>
            )}
          </div>
        </div>

        {isAdmin && (
          <p className="text-sm text-gray-500">
            &quot;Gerar comissoes&quot; lanca as comissoes dos recebimentos pagos no mes selecionado.
          </p>
        )}

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl bg-white/70 p-4">
            <p className="text-sm text-gray-500">Total no periodo</p>
            <p className="text-2xl font-semibold">{brl(resumo?.valor_total ?? 0)}</p>
          </div>
          <div className="rounded-2xl bg-white/70 p-4">
            <p className="text-sm text-gray-500">Profissionais</p>
            <p className="text-2xl font-semibold">{resumo?.itens.length ?? 0}</p>
          </div>
          <div className="rounded-2xl bg-white/70 p-4">
            <p className="text-sm text-gray-500">Lancamentos</p>
            <p className="text-2xl font-semibold">{comissoes.length}</p>
          </div>
        </div>

        {/* Resumo por profissional */}
        <div className="rounded-2xl bg-white/70 p-4">
          <h2 className="mb-3 text-lg font-display">Resumo por profissional</h2>
          <div className="grid grid-cols-5 gap-4 border-b border-black/10 pb-3 text-xs uppercase tracking-widest text-gray-500">
            <span>Profissional</span>
            <span>Lancamentos</span>
            <span>Pendente</span>
            <span>Pago</span>
            <span>Total</span>
          </div>
          <div className="divide-y divide-black/5">
            {(resumoQuery.isLoading || meQuery.isLoading) && (
              <div className="py-6 text-sm text-gray-500">Carregando...</div>
            )}
            {!resumoQuery.isLoading && (resumo?.itens.length ?? 0) === 0 && (
              <div className="py-6 text-sm text-gray-500">
                Nenhuma comissao no periodo.
              </div>
            )}
            {resumo?.itens.map((i) => (
              <div key={i.profissional_id} className="grid grid-cols-5 gap-4 py-3 text-sm">
                <span className="font-medium">{i.profissional_nome}</span>
                <span>{i.quantidade}</span>
                <span className="text-amber-700">{brl(i.valor_pendente)}</span>
                <span className="text-emerald-700">{brl(i.valor_pago)}</span>
                <span className="font-semibold">{brl(i.valor_total)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Detalhamento dos lancamentos */}
        <div className="rounded-2xl bg-white/70 p-4">
          <h2 className="mb-3 text-lg font-display">Lancamentos</h2>
          <div
            className={`grid ${isAdmin ? "grid-cols-7" : "grid-cols-6"} gap-4 border-b border-black/10 pb-3 text-xs uppercase tracking-widest text-gray-500`}
          >
            <span>Profissional</span>
            <span>Recebimento</span>
            <span>Base</span>
            <span>%</span>
            <span>Comissao</span>
            <span>Status</span>
            {isAdmin && <span>Acoes</span>}
          </div>
          <div className="divide-y divide-black/5">
            {comissoesQuery.isLoading && (
              <div className="py-6 text-sm text-gray-500">Carregando...</div>
            )}
            {!comissoesQuery.isLoading && comissoes.length === 0 && (
              <div className="py-6 text-sm text-gray-500">Nenhum lancamento.</div>
            )}
            {comissoes.map((c) => (
              <div
                key={c.id}
                className={`grid ${isAdmin ? "grid-cols-7" : "grid-cols-6"} gap-4 py-3 text-sm`}
              >
                <span className="font-medium">
                  {nomePorProf.get(c.profissional_id) ?? `#${c.profissional_id}`}
                </span>
                <span>{c.conta_receber_id ? `#${c.conta_receber_id}` : "—"}</span>
                <span>{brl(c.valor_base)}</span>
                <span>{c.percentual}%</span>
                <span className="font-semibold">{brl(c.valor)}</span>
                <span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      c.status === "pago"
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-amber-100 text-amber-700"
                    }`}
                  >
                    {c.status}
                  </span>
                </span>
                {isAdmin && (
                  <div>
                    {c.status !== "pago" && (
                      <button
                        className="rounded-full bg-emerald-600 px-3 py-1 text-xs text-white disabled:opacity-50"
                        onClick={() => pagarMutation.mutate(c.id)}
                        disabled={pagarMutation.isPending}
                      >
                        Marcar pago
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}

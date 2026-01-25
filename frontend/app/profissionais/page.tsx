"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import AppShell from "@/components/layout/AppShell";
import api from "@/lib/api";

type Profissional = {
  id: number;
  nome: string;
  perfil_acesso_id: number;
  data_nascimento?: string | null;
  crefito?: string | null;
};

type Perfil = {
  id: number;
  descricao: string;
};

type PageResponse<T> = {
  items: T[];
  meta: { page: number; page_size: number; total: number };
};

export default function Page() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState({
    nome: "",
    perfil_acesso_id: "",
    data_nascimento: "",
    crefito: ""
  });

  const profissionaisQuery = useQuery({
    queryKey: ["profissionais", page, pageSize],
    queryFn: async () => {
      const resp = await api.get<PageResponse<Profissional>>("/profissionais", {
        params: { page, page_size: pageSize, order_by: "nome", order_dir: "asc" }
      });
      return resp.data;
    }
  });

  const perfisQuery = useQuery({
    queryKey: ["perfis"],
    queryFn: async () => {
      const resp = await api.get<Perfil[]>("/auth/perfis");
      return resp.data;
    }
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      return api.post("/profissionais", {
        nome: form.nome,
        perfil_acesso_id: Number(form.perfil_acesso_id),
        data_nascimento: form.data_nascimento || null,
        crefito: form.crefito || null
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profissionais"] });
      setForm({ nome: "", perfil_acesso_id: "", data_nascimento: "", crefito: "" });
      setShowModal(false);
      setEditingId(null);
    }
  });

  const updateMutation = useMutation({
    mutationFn: async () => {
      return api.put(`/profissionais/${editingId}`, {
        nome: form.nome || undefined,
        perfil_acesso_id: form.perfil_acesso_id ? Number(form.perfil_acesso_id) : undefined,
        data_nascimento: form.data_nascimento || null,
        crefito: form.crefito || null
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profissionais"] });
      setForm({ nome: "", perfil_acesso_id: "", data_nascimento: "", crefito: "" });
      setShowModal(false);
      setEditingId(null);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      return api.delete(`/profissionais/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profissionais"] });
    }
  });

  const filtered = useMemo(() => {
    const items = profissionaisQuery.data?.items ?? [];
    if (!search.trim()) return items;
    const term = search.toLowerCase();
    return items.filter((p) => p.nome.toLowerCase().includes(term));
  }, [profissionaisQuery.data, search]);

  const total = profissionaisQuery.data?.meta.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-widest text-gray-500">Equipe</p>
            <h1 className="text-3xl font-display">Profissionais</h1>
          </div>
          <button
            className="rounded-full bg-black px-4 py-2 text-white"
            onClick={() => {
              setEditingId(null);
              setForm({ nome: "", perfil_acesso_id: "", data_nascimento: "", crefito: "" });
              setShowModal(true);
            }}
          >
            Novo profissional
          </button>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl bg-white/70 p-4">
            <p className="text-sm text-gray-500">Total cadastrados</p>
            <p className="text-2xl font-semibold">{total}</p>
          </div>
          <div className="rounded-2xl bg-white/70 p-4">
            <p className="text-sm text-gray-500">Perfis</p>
            <p className="text-2xl font-semibold">{perfisQuery.data?.length ?? 0}</p>
          </div>
          <div className="rounded-2xl bg-white/70 p-4">
            <p className="text-sm text-gray-500">Pagina</p>
            <p className="text-2xl font-semibold">
              {page} / {totalPages}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <input
            className="w-full max-w-sm rounded-full border border-black/10 bg-white/80 px-4 py-2"
            placeholder="Buscar por nome..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <div className="ml-auto flex items-center gap-2">
            <button
              className="rounded-full bg-white/70 px-3 py-1 text-sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Anterior
            </button>
            <button
              className="rounded-full bg-white/70 px-3 py-1 text-sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              Proxima
            </button>
          </div>
        </div>

        <div className="rounded-2xl bg-white/70 p-4">
          <div className="grid grid-cols-5 gap-4 border-b border-black/10 pb-3 text-xs uppercase tracking-widest text-gray-500">
            <span>Nome</span>
            <span>Perfil</span>
            <span>Data Nascimento</span>
            <span>CREFITO</span>
            <span>Acoes</span>
          </div>
          <div className="divide-y divide-black/5">
            {profissionaisQuery.isLoading && (
              <div className="py-6 text-sm text-gray-500">Carregando...</div>
            )}
            {!profissionaisQuery.isLoading && filtered.length === 0 && (
              <div className="py-6 text-sm text-gray-500">Nenhum profissional encontrado.</div>
            )}
            {filtered.map((prof) => (
              <div key={prof.id} className="grid grid-cols-5 gap-4 py-3 text-sm">
                <span className="font-medium">{prof.nome}</span>
                <span>
                  {perfisQuery.data?.find((p) => p.id === prof.perfil_acesso_id)?.descricao ??
                    "—"}
                </span>
                <span>{prof.data_nascimento ? prof.data_nascimento : "—"}</span>
                <span>{prof.crefito || "—"}</span>
                <div className="flex items-center gap-2">
                  <button
                    className="rounded-full bg-white/70 px-3 py-1 text-xs"
                    onClick={() => {
                      setEditingId(prof.id);
                      setForm({
                        nome: prof.nome,
                        perfil_acesso_id: String(prof.perfil_acesso_id),
                        data_nascimento: prof.data_nascimento ?? "",
                        crefito: prof.crefito ?? ""
                      });
                      setShowModal(true);
                    }}
                  >
                    Editar
                  </button>
                  <button
                    className="rounded-full bg-red-500/90 px-3 py-1 text-xs text-white"
                    onClick={() => {
                      if (confirm("Excluir profissional?")) {
                        deleteMutation.mutate(prof.id);
                      }
                    }}
                  >
                    Excluir
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-6">
          <div className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-display">
                {editingId ? "Editar profissional" : "Novo profissional"}
              </h2>
              <button className="text-sm text-gray-500" onClick={() => setShowModal(false)}>
                Fechar
              </button>
            </div>

            <div className="mt-4 grid gap-3">
              <label className="text-sm">
                Nome
                <input
                  className="mt-1 w-full rounded-xl border border-black/10 p-3"
                  value={form.nome}
                  onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
                />
              </label>
              <label className="text-sm">
                Perfil de acesso
                <select
                  className="mt-1 w-full rounded-xl border border-black/10 p-3"
                  value={form.perfil_acesso_id}
                  onChange={(e) => setForm((f) => ({ ...f, perfil_acesso_id: e.target.value }))}
                >
                  <option value="">Selecione</option>
                  {(perfisQuery.data ?? []).map((perfil) => (
                    <option key={perfil.id} value={perfil.id}>
                      {perfil.descricao}
                    </option>
                  ))}
                </select>
              </label>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="text-sm">
                  Data nascimento
                  <input
                    type="date"
                    className="mt-1 w-full rounded-xl border border-black/10 p-3"
                    value={form.data_nascimento}
                    onChange={(e) => setForm((f) => ({ ...f, data_nascimento: e.target.value }))}
                  />
                </label>
                <label className="text-sm">
                  CREFITO
                  <input
                    className="mt-1 w-full rounded-xl border border-black/10 p-3"
                    value={form.crefito}
                    onChange={(e) => setForm((f) => ({ ...f, crefito: e.target.value }))}
                  />
                </label>
              </div>
              <button
                className="mt-2 rounded-full bg-black px-4 py-2 text-white"
                onClick={() =>
                  editingId ? updateMutation.mutate() : createMutation.mutate()
                }
                disabled={
                  !form.nome ||
                  !form.perfil_acesso_id ||
                  createMutation.isPending ||
                  updateMutation.isPending
                }
              >
                {createMutation.isPending || updateMutation.isPending ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

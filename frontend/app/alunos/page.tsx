"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import AppShell from "@/components/layout/AppShell";
import api from "@/lib/api";

type Endereco = {
  id: number;
  logradouro: string;
  numero: string;
  cep: string;
  cidade: string;
  bairro: string;
  principal: boolean;
};

type Aluno = {
  id: number;
  nome: string;
  cpf: string;
  rg?: string | null;
  unidade_id: number;
  termo_uso_id?: number | null;
  status: string;
  observacoes?: string | null;
  enderecos: Endereco[];
};

type Unidade = { id: number; nome: string };
type Termo = { id: number; versao: string; ativo: boolean };
type AlunoAnexo = {
  id: number;
  tipo: string;
  arquivo_nome: string;
  mime_type: string;
  criado_em: string;
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
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [showAlunoModal, setShowAlunoModal] = useState(false);
  const [showEnderecoModal, setShowEnderecoModal] = useState(false);
  const [showFichaModal, setShowFichaModal] = useState(false);
  const [selectedAlunoId, setSelectedAlunoId] = useState<number | null>(null);
  const [form, setForm] = useState({
    nome: "",
    cpf: "",
    rg: "",
    unidade_id: "",
    termo_uso_id: "",
    status: "ativo",
    observacoes: ""
  });
  const [enderecoForm, setEnderecoForm] = useState({
    logradouro: "",
    numero: "",
    cep: "",
    cidade: "",
    bairro: "",
    principal: false
  });

  const alunosQuery = useQuery({
    queryKey: ["alunos", page, pageSize, statusFilter],
    queryFn: async () => {
      const resp = await api.get<PageResponse<Aluno>>("/alunos", {
        params: {
          page,
          page_size: pageSize,
          order_by: "nome",
          order_dir: "asc",
          status: statusFilter || undefined
        }
      });
      return resp.data;
    }
  });

  const unidadesQuery = useQuery({
    queryKey: ["unidades"],
    queryFn: async () => {
      const resp = await api.get<PageResponse<Unidade>>("/unidades", {
        params: { page: 1, page_size: 100 }
      });
      return resp.data.items;
    }
  });

  const termosQuery = useQuery({
    queryKey: ["termos"],
    queryFn: async () => {
      const resp = await api.get<PageResponse<Termo>>("/termos", {
        params: { page: 1, page_size: 100 }
      });
      return resp.data.items.filter((t) => t.ativo);
    }
  });

  const alunoDetailQuery = useQuery({
    queryKey: ["aluno", selectedAlunoId],
    enabled: selectedAlunoId !== null,
    queryFn: async () => {
      const resp = await api.get<Aluno>(`/alunos/${selectedAlunoId}`);
      return resp.data;
    }
  });

  const anexosQuery = useQuery({
    queryKey: ["aluno-anexos", selectedAlunoId],
    enabled: selectedAlunoId !== null && showFichaModal,
    queryFn: async () => {
      const resp = await api.get<AlunoAnexo[]>(`/alunos/${selectedAlunoId}/anexos`);
      return resp.data;
    }
  });

  const createAlunoMutation = useMutation({
    mutationFn: async () => {
      return api.post("/alunos", {
        nome: form.nome,
        cpf: form.cpf,
        rg: form.rg || null,
        unidade_id: Number(form.unidade_id),
        termo_uso_id: form.termo_uso_id ? Number(form.termo_uso_id) : null,
        status: form.status,
        observacoes: form.observacoes || null
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alunos"] });
      setForm({
        nome: "",
        cpf: "",
        rg: "",
        unidade_id: "",
        termo_uso_id: "",
        status: "ativo",
        observacoes: ""
      });
      setShowAlunoModal(false);
    }
  });

  const addEnderecoMutation = useMutation({
    mutationFn: async () => {
      return api.post(`/alunos/${selectedAlunoId}/enderecos`, {
        ...enderecoForm
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["aluno", selectedAlunoId] });
      queryClient.invalidateQueries({ queryKey: ["alunos"] });
      setEnderecoForm({
        logradouro: "",
        numero: "",
        cep: "",
        cidade: "",
        bairro: "",
        principal: false
      });
      setShowEnderecoModal(false);
    }
  });

  const gerarTermoMutation = useMutation({
    mutationFn: async () => {
      return api.post(`/alunos/${selectedAlunoId}/termo-pdf`, {
        termo_id: alunoDetailQuery.data?.termo_uso_id ?? null,
        contrato_id: null
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["aluno-anexos", selectedAlunoId] });
    }
  });

  const filtered = useMemo(() => {
    const items = alunosQuery.data?.items ?? [];
    if (!search.trim()) return items;
    const term = search.toLowerCase();
    return items.filter((a) => a.nome.toLowerCase().includes(term));
  }, [alunosQuery.data, search]);

  const total = alunosQuery.data?.meta.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const downloadAnexo = async (anexo: AlunoAnexo) => {
    if (!selectedAlunoId) return;
    const resp = await api.get(`/alunos/${selectedAlunoId}/anexos/${anexo.id}`, {
      responseType: "blob"
    });
    const url = window.URL.createObjectURL(resp.data);
    const link = document.createElement("a");
    link.href = url;
    link.download = anexo.arquivo_nome;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-widest text-gray-500">Clientes</p>
            <h1 className="text-3xl font-display">Alunos</h1>
          </div>
          <button
            className="rounded-full bg-black px-4 py-2 text-white"
            onClick={() => {
              setShowAlunoModal(true);
            }}
          >
            Novo aluno
          </button>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl bg-white/70 p-4">
            <p className="text-sm text-gray-500">Total alunos</p>
            <p className="text-2xl font-semibold">{total}</p>
          </div>
          <div className="rounded-2xl bg-white/70 p-4">
            <p className="text-sm text-gray-500">Ativos</p>
            <p className="text-2xl font-semibold">
              {(alunosQuery.data?.items ?? []).filter((a) => a.status === "ativo").length}
            </p>
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
          <select
            className="rounded-full border border-black/10 bg-white/80 px-4 py-2 text-sm"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Todos</option>
            <option value="ativo">Ativo</option>
            <option value="inativo">Inativo</option>
          </select>
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
          <div className="grid grid-cols-6 gap-4 border-b border-black/10 pb-3 text-xs uppercase tracking-widest text-gray-500">
            <span>Nome</span>
            <span>CPF</span>
            <span>Status</span>
            <span>Unidade</span>
            <span>Enderecos</span>
            <span>Acoes</span>
          </div>
          <div className="divide-y divide-black/5">
            {alunosQuery.isLoading && (
              <div className="py-6 text-sm text-gray-500">Carregando...</div>
            )}
            {!alunosQuery.isLoading && filtered.length === 0 && (
              <div className="py-6 text-sm text-gray-500">Nenhum aluno encontrado.</div>
            )}
            {filtered.map((aluno) => (
              <div key={aluno.id} className="grid grid-cols-6 gap-4 py-3 text-sm">
                <span className="font-medium">{aluno.nome}</span>
                <span>{aluno.cpf}</span>
                <span className="capitalize">{aluno.status}</span>
                <span>
                  {unidadesQuery.data?.find((u) => u.id === aluno.unidade_id)?.nome ?? "—"}
                </span>
                <span>{aluno.enderecos?.length ?? 0}</span>
                <div className="flex items-center gap-2">
                  <button
                    className="rounded-full bg-white/70 px-3 py-1 text-xs"
                    onClick={() => {
                      setSelectedAlunoId(aluno.id);
                      setShowEnderecoModal(true);
                    }}
                  >
                    Enderecos
                  </button>
                  <button
                    className="rounded-full bg-white/70 px-3 py-1 text-xs"
                    onClick={() => {
                      setSelectedAlunoId(aluno.id);
                      setShowFichaModal(true);
                    }}
                  >
                    Ficha
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {showAlunoModal && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-6">
          <div className="w-full max-w-2xl rounded-3xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-display">Novo aluno</h2>
              <button className="text-sm text-gray-500" onClick={() => setShowAlunoModal(false)}>
                Fechar
              </button>
            </div>

            <div className="mt-4 grid gap-3">
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="text-sm">
                  Nome
                  <input
                    className="mt-1 w-full rounded-xl border border-black/10 p-3"
                    value={form.nome}
                    onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
                  />
                </label>
                <label className="text-sm">
                  CPF
                  <input
                    className="mt-1 w-full rounded-xl border border-black/10 p-3"
                    value={form.cpf}
                    onChange={(e) => setForm((f) => ({ ...f, cpf: e.target.value }))}
                  />
                </label>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="text-sm">
                  RG
                  <input
                    className="mt-1 w-full rounded-xl border border-black/10 p-3"
                    value={form.rg}
                    onChange={(e) => setForm((f) => ({ ...f, rg: e.target.value }))}
                  />
                </label>
                <label className="text-sm">
                  Unidade
                  <select
                    className="mt-1 w-full rounded-xl border border-black/10 p-3"
                    value={form.unidade_id}
                    onChange={(e) => setForm((f) => ({ ...f, unidade_id: e.target.value }))}
                  >
                    <option value="">Selecione</option>
                    {(unidadesQuery.data ?? []).map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.nome}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="text-sm">
                  Termo de uso
                  <select
                    className="mt-1 w-full rounded-xl border border-black/10 p-3"
                    value={form.termo_uso_id}
                    onChange={(e) => setForm((f) => ({ ...f, termo_uso_id: e.target.value }))}
                  >
                    <option value="">Nenhum</option>
                    {(termosQuery.data ?? []).map((t) => (
                      <option key={t.id} value={t.id}>
                        Versao {t.versao}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-sm">
                  Status
                  <select
                    className="mt-1 w-full rounded-xl border border-black/10 p-3"
                    value={form.status}
                    onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
                  >
                    <option value="ativo">Ativo</option>
                    <option value="inativo">Inativo</option>
                  </select>
                </label>
              </div>
              <label className="text-sm">
                Observacoes
                <textarea
                  className="mt-1 w-full rounded-xl border border-black/10 p-3"
                  rows={3}
                  value={form.observacoes}
                  onChange={(e) => setForm((f) => ({ ...f, observacoes: e.target.value }))}
                />
              </label>
              <button
                className="mt-2 rounded-full bg-black px-4 py-2 text-white"
                onClick={() => createAlunoMutation.mutate()}
                disabled={
                  !form.nome ||
                  !form.cpf ||
                  !form.unidade_id ||
                  createAlunoMutation.isPending
                }
              >
                {createAlunoMutation.isPending ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </div>
        </div>
      )}

      {showEnderecoModal && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-6">
          <div className="w-full max-w-2xl rounded-3xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-display">Enderecos</h2>
              <button
                className="text-sm text-gray-500"
                onClick={() => setShowEnderecoModal(false)}
              >
                Fechar
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div className="rounded-2xl bg-white/70 p-4">
                <p className="text-sm text-gray-500">Aluno</p>
                <p className="text-lg font-medium">{alunoDetailQuery.data?.nome ?? "—"}</p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <label className="text-sm">
                  Logradouro
                  <input
                    className="mt-1 w-full rounded-xl border border-black/10 p-3"
                    value={enderecoForm.logradouro}
                    onChange={(e) => setEnderecoForm((f) => ({ ...f, logradouro: e.target.value }))}
                  />
                </label>
                <label className="text-sm">
                  Numero
                  <input
                    className="mt-1 w-full rounded-xl border border-black/10 p-3"
                    value={enderecoForm.numero}
                    onChange={(e) => setEnderecoForm((f) => ({ ...f, numero: e.target.value }))}
                  />
                </label>
                <label className="text-sm">
                  CEP
                  <input
                    className="mt-1 w-full rounded-xl border border-black/10 p-3"
                    value={enderecoForm.cep}
                    onChange={(e) => setEnderecoForm((f) => ({ ...f, cep: e.target.value }))}
                  />
                </label>
                <label className="text-sm">
                  Cidade
                  <input
                    className="mt-1 w-full rounded-xl border border-black/10 p-3"
                    value={enderecoForm.cidade}
                    onChange={(e) => setEnderecoForm((f) => ({ ...f, cidade: e.target.value }))}
                  />
                </label>
                <label className="text-sm">
                  Bairro
                  <input
                    className="mt-1 w-full rounded-xl border border-black/10 p-3"
                    value={enderecoForm.bairro}
                    onChange={(e) => setEnderecoForm((f) => ({ ...f, bairro: e.target.value }))}
                  />
                </label>
                <label className="text-sm flex items-center gap-2 pt-6">
                  <input
                    type="checkbox"
                    checked={enderecoForm.principal}
                    onChange={(e) =>
                      setEnderecoForm((f) => ({ ...f, principal: e.target.checked }))
                    }
                  />
                  Principal
                </label>
              </div>

              <button
                className="rounded-full bg-black px-4 py-2 text-white"
                onClick={() => addEnderecoMutation.mutate()}
                disabled={
                  !enderecoForm.logradouro ||
                  !enderecoForm.numero ||
                  !enderecoForm.cep ||
                  !enderecoForm.cidade ||
                  !enderecoForm.bairro ||
                  addEnderecoMutation.isPending
                }
              >
                {addEnderecoMutation.isPending ? "Salvando..." : "Adicionar endereco"}
              </button>

              <div className="rounded-2xl bg-white/70 p-4">
                <p className="text-sm text-gray-500">Enderecos cadastrados</p>
                <div className="mt-3 space-y-2 text-sm">
                  {(alunoDetailQuery.data?.enderecos ?? []).map((end) => (
                    <div key={end.id} className="rounded-xl bg-white/80 p-3">
                      <p className="font-medium">
                        {end.logradouro}, {end.numero} - {end.bairro}
                      </p>
                      <p className="text-gray-500">
                        {end.cidade} - {end.cep} {end.principal ? "(Principal)" : ""}
                      </p>
                    </div>
                  ))}
                  {(alunoDetailQuery.data?.enderecos ?? []).length === 0 && (
                    <p className="text-gray-500">Nenhum endereco cadastrado.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {showFichaModal && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-6">
          <div className="w-full max-w-4xl rounded-3xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-display">Ficha do aluno</h2>
              <button className="text-sm text-gray-500" onClick={() => setShowFichaModal(false)}>
                Fechar
              </button>
            </div>

            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <div className="rounded-2xl bg-white/70 p-4">
                <p className="text-sm text-gray-500">Dados gerais</p>
                <div className="mt-3 space-y-2 text-sm">
                  <p>
                    <span className="text-gray-500">Nome:</span>{" "}
                    {alunoDetailQuery.data?.nome ?? "—"}
                  </p>
                  <p>
                    <span className="text-gray-500">CPF:</span> {alunoDetailQuery.data?.cpf ?? "—"}
                  </p>
                  <p>
                    <span className="text-gray-500">Status:</span>{" "}
                    {alunoDetailQuery.data?.status ?? "—"}
                  </p>
                  <p>
                    <span className="text-gray-500">Unidade:</span>{" "}
                    {unidadesQuery.data?.find((u) => u.id === alunoDetailQuery.data?.unidade_id)
                      ?.nome ?? "—"}
                  </p>
                  <p>
                    <span className="text-gray-500">Termo vinculado:</span>{" "}
                    {alunoDetailQuery.data?.termo_uso_id ? `#${alunoDetailQuery.data.termo_uso_id}` : "Nenhum"}
                  </p>
                </div>
              </div>

              <div className="rounded-2xl bg-white/70 p-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-500">Anexos</p>
                  <button
                    className="rounded-full bg-black px-3 py-1 text-xs text-white"
                    onClick={() => gerarTermoMutation.mutate()}
                    disabled={!alunoDetailQuery.data?.termo_uso_id || gerarTermoMutation.isPending}
                  >
                    {gerarTermoMutation.isPending ? "Gerando..." : "Gerar termo de uso"}
                  </button>
                </div>

                <div className="mt-3 space-y-2 text-sm">
                  {(anexosQuery.data ?? []).map((anexo) => (
                    <div key={anexo.id} className="flex items-center justify-between rounded-xl bg-white/80 p-3">
                      <div>
                        <p className="font-medium">{anexo.tipo}</p>
                        <p className="text-xs text-gray-500">{anexo.arquivo_nome}</p>
                      </div>
                      <button
                        className="rounded-full bg-white/70 px-3 py-1 text-xs"
                        onClick={() => downloadAnexo(anexo)}
                      >
                        Baixar PDF
                      </button>
                    </div>
                  ))}
                  {(anexosQuery.data ?? []).length === 0 && (
                    <p className="text-gray-500">Nenhum anexo ainda.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

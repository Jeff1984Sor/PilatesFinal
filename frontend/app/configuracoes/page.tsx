"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import AppShell from "@/components/layout/AppShell";
import api from "@/lib/api";

type PageResponse<T> = {
  items: T[];
  meta: { page: number; page_size: number; total: number };
};

type Unidade = { id: number; nome: string; ocupacao_max: number; ativo: boolean };
type Termo = { id: number; versao: string; descricao: string; ativo: boolean };
type Perfil = { id: number; descricao: string };
type Recorrencia = { id: number; descricao: string; intervalo_meses: number };
type TipoPlano = { id: number; descricao: string; recorrencia_id: number };
type TipoServico = { id: number; descricao: string };
type Fornecedor = { id: number; nome: string; documento?: string | null; whatsapp?: string | null };
type Categoria = { id: number; descricao: string };
type Subcategoria = { id: number; descricao: string; categoria_id: number };

type MenuKey =
  | "unidades"
  | "termos"
  | "perfis"
  | "recorrencias"
  | "tipo_plano"
  | "tipo_servico"
  | "fornecedores"
  | "categorias"
  | "subcategorias";

const menu: { key: MenuKey; label: string; group: string }[] = [
  { key: "unidades", label: "Unidades", group: "Configuracoes" },
  { key: "termos", label: "Termos de uso", group: "Configuracoes" },
  { key: "perfis", label: "Perfis de acesso", group: "Configuracoes" },
  { key: "recorrencias", label: "Recorrencias", group: "Planos" },
  { key: "tipo_plano", label: "Tipos de plano", group: "Planos" },
  { key: "tipo_servico", label: "Tipos de servico", group: "Planos" },
  { key: "fornecedores", label: "Fornecedores", group: "Financeiro" },
  { key: "categorias", label: "Categorias", group: "Financeiro" },
  { key: "subcategorias", label: "Subcategorias", group: "Financeiro" }
];

export default function Page() {
  const queryClient = useQueryClient();
  const [active, setActive] = useState<MenuKey>("unidades");

  const [unidadeForm, setUnidadeForm] = useState({ nome: "", ocupacao_max: "", ativo: true });
  const [termoForm, setTermoForm] = useState({ versao: "", descricao: "", ativo: true });
  const [perfilForm, setPerfilForm] = useState({ descricao: "" });
  const [recorrenciaForm, setRecorrenciaForm] = useState({ descricao: "", intervalo_meses: "" });
  const [tipoPlanoForm, setTipoPlanoForm] = useState({ descricao: "", recorrencia_id: "" });
  const [tipoServicoForm, setTipoServicoForm] = useState({ descricao: "" });
  const [fornecedorForm, setFornecedorForm] = useState({ nome: "", documento: "", whatsapp: "" });
  const [categoriaForm, setCategoriaForm] = useState({ descricao: "" });
  const [subcategoriaForm, setSubcategoriaForm] = useState({ descricao: "", categoria_id: "" });

  const unidadesQuery = useQuery({
    queryKey: ["unidades"],
    queryFn: async () => {
      const resp = await api.get<PageResponse<Unidade>>("/unidades", {
        params: { page: 1, page_size: 100, order_by: "nome", order_dir: "asc" }
      });
      return resp.data.items;
    }
  });

  const termosQuery = useQuery({
    queryKey: ["termos"],
    queryFn: async () => {
      const resp = await api.get<PageResponse<Termo>>("/termos", {
        params: { page: 1, page_size: 100, order_by: "versao", order_dir: "desc" }
      });
      return resp.data.items;
    }
  });

  const perfisQuery = useQuery({
    queryKey: ["perfis"],
    queryFn: async () => {
      const resp = await api.get<Perfil[]>("/auth/perfis");
      return resp.data;
    }
  });

  const recorrenciasQuery = useQuery({
    queryKey: ["recorrencias"],
    queryFn: async () => {
      const resp = await api.get<PageResponse<Recorrencia>>("/planos/recorrencias", {
        params: { page: 1, page_size: 100 }
      });
      return resp.data.items;
    }
  });

  const tiposPlanoQuery = useQuery({
    queryKey: ["tipo_plano"],
    queryFn: async () => {
      const resp = await api.get<PageResponse<TipoPlano>>("/planos/tipos", {
        params: { page: 1, page_size: 100 }
      });
      return resp.data.items;
    }
  });

  const tiposServicoQuery = useQuery({
    queryKey: ["tipo_servico"],
    queryFn: async () => {
      const resp = await api.get<PageResponse<TipoServico>>("/planos/servicos", {
        params: { page: 1, page_size: 100 }
      });
      return resp.data.items;
    }
  });

  const fornecedoresQuery = useQuery({
    queryKey: ["fornecedores"],
    queryFn: async () => {
      const resp = await api.get<PageResponse<Fornecedor>>("/financeiro/fornecedores", {
        params: { page: 1, page_size: 100 }
      });
      return resp.data.items;
    }
  });

  const categoriasQuery = useQuery({
    queryKey: ["categorias"],
    queryFn: async () => {
      const resp = await api.get<PageResponse<Categoria>>("/financeiro/categorias", {
        params: { page: 1, page_size: 100 }
      });
      return resp.data.items;
    }
  });

  const subcategoriasQuery = useQuery({
    queryKey: ["subcategorias"],
    queryFn: async () => {
      const resp = await api.get<PageResponse<Subcategoria>>("/financeiro/subcategorias", {
        params: { page: 1, page_size: 100 }
      });
      return resp.data.items;
    }
  });

  const createUnidade = useMutation({
    mutationFn: async () => {
      return api.post("/unidades", {
        nome: unidadeForm.nome,
        ocupacao_max: Number(unidadeForm.ocupacao_max),
        ativo: unidadeForm.ativo
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["unidades"] });
      setUnidadeForm({ nome: "", ocupacao_max: "", ativo: true });
    }
  });

  const createTermo = useMutation({
    mutationFn: async () => {
      return api.post("/termos", {
        versao: termoForm.versao,
        descricao: termoForm.descricao,
        ativo: termoForm.ativo
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["termos"] });
      setTermoForm({ versao: "", descricao: "", ativo: true });
    }
  });

  const createPerfil = useMutation({
    mutationFn: async () => {
      return api.post("/auth/perfis", { descricao: perfilForm.descricao });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["perfis"] });
      setPerfilForm({ descricao: "" });
    }
  });

  const createRecorrencia = useMutation({
    mutationFn: async () => {
      return api.post("/planos/recorrencias", {
        descricao: recorrenciaForm.descricao,
        intervalo_meses: Number(recorrenciaForm.intervalo_meses)
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recorrencias"] });
      setRecorrenciaForm({ descricao: "", intervalo_meses: "" });
    }
  });

  const createTipoPlano = useMutation({
    mutationFn: async () => {
      return api.post("/planos/tipos", {
        descricao: tipoPlanoForm.descricao,
        recorrencia_id: Number(tipoPlanoForm.recorrencia_id)
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tipo_plano"] });
      setTipoPlanoForm({ descricao: "", recorrencia_id: "" });
    }
  });

  const createTipoServico = useMutation({
    mutationFn: async () => {
      return api.post("/planos/servicos", { descricao: tipoServicoForm.descricao });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tipo_servico"] });
      setTipoServicoForm({ descricao: "" });
    }
  });

  const createFornecedor = useMutation({
    mutationFn: async () => {
      return api.post("/financeiro/fornecedores", {
        nome: fornecedorForm.nome,
        documento: fornecedorForm.documento || null,
        whatsapp: fornecedorForm.whatsapp || null
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fornecedores"] });
      setFornecedorForm({ nome: "", documento: "", whatsapp: "" });
    }
  });

  const createCategoria = useMutation({
    mutationFn: async () => {
      return api.post("/financeiro/categorias", { descricao: categoriaForm.descricao });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categorias"] });
      setCategoriaForm({ descricao: "" });
    }
  });

  const createSubcategoria = useMutation({
    mutationFn: async () => {
      return api.post("/financeiro/subcategorias", {
        descricao: subcategoriaForm.descricao,
        categoria_id: Number(subcategoriaForm.categoria_id)
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subcategorias"] });
      setSubcategoriaForm({ descricao: "", categoria_id: "" });
    }
  });

  const groupedMenu = useMemo(() => {
    return menu.reduce<Record<string, { key: MenuKey; label: string }[]>>((acc, item) => {
      acc[item.group] = acc[item.group] ?? [];
      acc[item.group].push({ key: item.key, label: item.label });
      return acc;
    }, {});
  }, []);

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <p className="text-xs uppercase tracking-widest text-gray-500">Configuracoes</p>
          <h1 className="text-3xl font-display">Cadastros auxiliares</h1>
        </div>

        <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
          <aside className="rounded-2xl bg-white/70 p-4">
            {Object.entries(groupedMenu).map(([group, items]) => (
              <div key={group} className="mb-4">
                <p className="text-xs uppercase tracking-widest text-gray-400">{group}</p>
                <div className="mt-2 space-y-1">
                  {items.map((item) => (
                    <button
                      key={item.key}
                      className={`w-full rounded-xl px-3 py-2 text-left text-sm ${
                        active === item.key ? "bg-black text-white" : "hover:bg-black/5"
                      }`}
                      onClick={() => setActive(item.key)}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </aside>

          <section className="space-y-4">
            {active === "unidades" && (
              <div className="rounded-2xl bg-white/70 p-6">
                <h2 className="text-2xl font-display">Unidades</h2>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  <input
                    className="rounded-xl border border-black/10 p-3"
                    placeholder="Nome da unidade"
                    value={unidadeForm.nome}
                    onChange={(e) => setUnidadeForm((f) => ({ ...f, nome: e.target.value }))}
                  />
                  <input
                    className="rounded-xl border border-black/10 p-3"
                    placeholder="Ocupacao maxima"
                    value={unidadeForm.ocupacao_max}
                    onChange={(e) =>
                      setUnidadeForm((f) => ({ ...f, ocupacao_max: e.target.value }))
                    }
                  />
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={unidadeForm.ativo}
                      onChange={(e) => setUnidadeForm((f) => ({ ...f, ativo: e.target.checked }))}
                    />
                    Ativo
                  </label>
                </div>
                <button
                  className="mt-3 rounded-full bg-black px-4 py-2 text-white"
                  onClick={() => createUnidade.mutate()}
                  disabled={!unidadeForm.nome || !unidadeForm.ocupacao_max || createUnidade.isPending}
                >
                  {createUnidade.isPending ? "Salvando..." : "Adicionar unidade"}
                </button>
                <div className="mt-6 space-y-2 text-sm">
                  {(unidadesQuery.data ?? []).map((u) => (
                    <div key={u.id} className="rounded-xl bg-white/80 p-3">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{u.nome}</span>
                        <span className="text-xs text-gray-500">
                          {u.ativo ? "Ativo" : "Inativo"}
                        </span>
                      </div>
                      <p className="text-gray-500">Ocupacao maxima: {u.ocupacao_max}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {active === "termos" && (
              <div className="rounded-2xl bg-white/70 p-6">
                <h2 className="text-2xl font-display">Termos de uso</h2>
                <div className="mt-4 grid gap-3">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <input
                      className="rounded-xl border border-black/10 p-3"
                      placeholder="Versao"
                      value={termoForm.versao}
                      onChange={(e) => setTermoForm((f) => ({ ...f, versao: e.target.value }))}
                    />
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={termoForm.ativo}
                        onChange={(e) => setTermoForm((f) => ({ ...f, ativo: e.target.checked }))}
                      />
                      Ativo
                    </label>
                  </div>
                  <textarea
                    className="rounded-xl border border-black/10 p-3"
                    rows={4}
                    placeholder="Descricao do termo"
                    value={termoForm.descricao}
                    onChange={(e) => setTermoForm((f) => ({ ...f, descricao: e.target.value }))}
                  />
                </div>
                <button
                  className="mt-3 rounded-full bg-black px-4 py-2 text-white"
                  onClick={() => createTermo.mutate()}
                  disabled={!termoForm.versao || !termoForm.descricao || createTermo.isPending}
                >
                  {createTermo.isPending ? "Salvando..." : "Adicionar termo"}
                </button>
                <div className="mt-6 space-y-2 text-sm">
                  {(termosQuery.data ?? []).map((t) => (
                    <div key={t.id} className="rounded-xl bg-white/80 p-3">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">Versao {t.versao}</span>
                        <span className="text-xs text-gray-500">{t.ativo ? "Ativo" : "Inativo"}</span>
                      </div>
                      <p className="text-gray-500 line-clamp-2">{t.descricao}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {active === "perfis" && (
              <div className="rounded-2xl bg-white/70 p-6">
                <h2 className="text-2xl font-display">Perfis de acesso</h2>
                <div className="mt-4 flex gap-3">
                  <input
                    className="flex-1 rounded-xl border border-black/10 p-3"
                    placeholder="Descricao"
                    value={perfilForm.descricao}
                    onChange={(e) => setPerfilForm({ descricao: e.target.value })}
                  />
                  <button
                    className="rounded-full bg-black px-4 py-2 text-white"
                    onClick={() => createPerfil.mutate()}
                    disabled={!perfilForm.descricao || createPerfil.isPending}
                  >
                    {createPerfil.isPending ? "Salvando..." : "Adicionar"}
                  </button>
                </div>
                <div className="mt-6 space-y-2 text-sm">
                  {(perfisQuery.data ?? []).map((p) => (
                    <div key={p.id} className="rounded-xl bg-white/80 p-3">
                      <span className="font-medium">{p.descricao}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {active === "recorrencias" && (
              <div className="rounded-2xl bg-white/70 p-6">
                <h2 className="text-2xl font-display">Recorrencias</h2>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <input
                    className="rounded-xl border border-black/10 p-3"
                    placeholder="Descricao"
                    value={recorrenciaForm.descricao}
                    onChange={(e) =>
                      setRecorrenciaForm((f) => ({ ...f, descricao: e.target.value }))
                    }
                  />
                  <input
                    className="rounded-xl border border-black/10 p-3"
                    placeholder="Intervalo em meses"
                    value={recorrenciaForm.intervalo_meses}
                    onChange={(e) =>
                      setRecorrenciaForm((f) => ({ ...f, intervalo_meses: e.target.value }))
                    }
                  />
                </div>
                <button
                  className="mt-3 rounded-full bg-black px-4 py-2 text-white"
                  onClick={() => createRecorrencia.mutate()}
                  disabled={
                    !recorrenciaForm.descricao ||
                    !recorrenciaForm.intervalo_meses ||
                    createRecorrencia.isPending
                  }
                >
                  {createRecorrencia.isPending ? "Salvando..." : "Adicionar recorrencia"}
                </button>
                <div className="mt-6 space-y-2 text-sm">
                  {(recorrenciasQuery.data ?? []).map((r) => (
                    <div key={r.id} className="rounded-xl bg-white/80 p-3">
                      <span className="font-medium">{r.descricao}</span>
                      <p className="text-gray-500">Intervalo: {r.intervalo_meses} meses</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {active === "tipo_plano" && (
              <div className="rounded-2xl bg-white/70 p-6">
                <h2 className="text-2xl font-display">Tipos de plano</h2>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <input
                    className="rounded-xl border border-black/10 p-3"
                    placeholder="Descricao"
                    value={tipoPlanoForm.descricao}
                    onChange={(e) => setTipoPlanoForm((f) => ({ ...f, descricao: e.target.value }))}
                  />
                  <select
                    className="rounded-xl border border-black/10 p-3"
                    value={tipoPlanoForm.recorrencia_id}
                    onChange={(e) =>
                      setTipoPlanoForm((f) => ({ ...f, recorrencia_id: e.target.value }))
                    }
                  >
                    <option value="">Selecione a recorrencia</option>
                    {(recorrenciasQuery.data ?? []).map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.descricao}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  className="mt-3 rounded-full bg-black px-4 py-2 text-white"
                  onClick={() => createTipoPlano.mutate()}
                  disabled={
                    !tipoPlanoForm.descricao ||
                    !tipoPlanoForm.recorrencia_id ||
                    createTipoPlano.isPending
                  }
                >
                  {createTipoPlano.isPending ? "Salvando..." : "Adicionar tipo de plano"}
                </button>
                <div className="mt-6 space-y-2 text-sm">
                  {(tiposPlanoQuery.data ?? []).map((t) => (
                    <div key={t.id} className="rounded-xl bg-white/80 p-3">
                      <span className="font-medium">{t.descricao}</span>
                      <p className="text-gray-500">
                        Recorrencia:{" "}
                        {recorrenciasQuery.data?.find((r) => r.id === t.recorrencia_id)?.descricao ??
                          "—"}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {active === "tipo_servico" && (
              <div className="rounded-2xl bg-white/70 p-6">
                <h2 className="text-2xl font-display">Tipos de servico</h2>
                <div className="mt-4 flex gap-3">
                  <input
                    className="flex-1 rounded-xl border border-black/10 p-3"
                    placeholder="Descricao"
                    value={tipoServicoForm.descricao}
                    onChange={(e) => setTipoServicoForm({ descricao: e.target.value })}
                  />
                  <button
                    className="rounded-full bg-black px-4 py-2 text-white"
                    onClick={() => createTipoServico.mutate()}
                    disabled={!tipoServicoForm.descricao || createTipoServico.isPending}
                  >
                    {createTipoServico.isPending ? "Salvando..." : "Adicionar"}
                  </button>
                </div>
                <div className="mt-6 space-y-2 text-sm">
                  {(tiposServicoQuery.data ?? []).map((t) => (
                    <div key={t.id} className="rounded-xl bg-white/80 p-3">
                      <span className="font-medium">{t.descricao}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {active === "fornecedores" && (
              <div className="rounded-2xl bg-white/70 p-6">
                <h2 className="text-2xl font-display">Fornecedores</h2>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  <input
                    className="rounded-xl border border-black/10 p-3"
                    placeholder="Nome"
                    value={fornecedorForm.nome}
                    onChange={(e) => setFornecedorForm((f) => ({ ...f, nome: e.target.value }))}
                  />
                  <input
                    className="rounded-xl border border-black/10 p-3"
                    placeholder="Documento"
                    value={fornecedorForm.documento}
                    onChange={(e) =>
                      setFornecedorForm((f) => ({ ...f, documento: e.target.value }))
                    }
                  />
                  <input
                    className="rounded-xl border border-black/10 p-3"
                    placeholder="Whatsapp"
                    value={fornecedorForm.whatsapp}
                    onChange={(e) =>
                      setFornecedorForm((f) => ({ ...f, whatsapp: e.target.value }))
                    }
                  />
                </div>
                <button
                  className="mt-3 rounded-full bg-black px-4 py-2 text-white"
                  onClick={() => createFornecedor.mutate()}
                  disabled={!fornecedorForm.nome || createFornecedor.isPending}
                >
                  {createFornecedor.isPending ? "Salvando..." : "Adicionar fornecedor"}
                </button>
                <div className="mt-6 space-y-2 text-sm">
                  {(fornecedoresQuery.data ?? []).map((f) => (
                    <div key={f.id} className="rounded-xl bg-white/80 p-3">
                      <span className="font-medium">{f.nome}</span>
                      <p className="text-gray-500">
                        {f.documento || "Sem documento"} | {f.whatsapp || "Sem whatsapp"}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {active === "categorias" && (
              <div className="rounded-2xl bg-white/70 p-6">
                <h2 className="text-2xl font-display">Categorias</h2>
                <div className="mt-4 flex gap-3">
                  <input
                    className="flex-1 rounded-xl border border-black/10 p-3"
                    placeholder="Descricao"
                    value={categoriaForm.descricao}
                    onChange={(e) => setCategoriaForm({ descricao: e.target.value })}
                  />
                  <button
                    className="rounded-full bg-black px-4 py-2 text-white"
                    onClick={() => createCategoria.mutate()}
                    disabled={!categoriaForm.descricao || createCategoria.isPending}
                  >
                    {createCategoria.isPending ? "Salvando..." : "Adicionar"}
                  </button>
                </div>
                <div className="mt-6 space-y-2 text-sm">
                  {(categoriasQuery.data ?? []).map((c) => (
                    <div key={c.id} className="rounded-xl bg-white/80 p-3">
                      <span className="font-medium">{c.descricao}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {active === "subcategorias" && (
              <div className="rounded-2xl bg-white/70 p-6">
                <h2 className="text-2xl font-display">Subcategorias</h2>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <input
                    className="rounded-xl border border-black/10 p-3"
                    placeholder="Descricao"
                    value={subcategoriaForm.descricao}
                    onChange={(e) =>
                      setSubcategoriaForm((f) => ({ ...f, descricao: e.target.value }))
                    }
                  />
                  <select
                    className="rounded-xl border border-black/10 p-3"
                    value={subcategoriaForm.categoria_id}
                    onChange={(e) =>
                      setSubcategoriaForm((f) => ({ ...f, categoria_id: e.target.value }))
                    }
                  >
                    <option value="">Selecione a categoria</option>
                    {(categoriasQuery.data ?? []).map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.descricao}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  className="mt-3 rounded-full bg-black px-4 py-2 text-white"
                  onClick={() => createSubcategoria.mutate()}
                  disabled={
                    !subcategoriaForm.descricao ||
                    !subcategoriaForm.categoria_id ||
                    createSubcategoria.isPending
                  }
                >
                  {createSubcategoria.isPending ? "Salvando..." : "Adicionar subcategoria"}
                </button>
                <div className="mt-6 space-y-2 text-sm">
                  {(subcategoriasQuery.data ?? []).map((s) => (
                    <div key={s.id} className="rounded-xl bg-white/80 p-3">
                      <span className="font-medium">{s.descricao}</span>
                      <p className="text-gray-500">
                        Categoria:{" "}
                        {categoriasQuery.data?.find((c) => c.id === s.categoria_id)?.descricao ??
                          "—"}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </AppShell>
  );
}

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import api from "@/lib/api";
import { cn } from "@/lib/utils";

type AulaOperacao = {
  id: number;
  aula_sessao_id: number;
  dt_inicio: string;
  dt_fim: string;
  unidade_id?: number | null;
  unidade?: string | null;
  sala?: string | null;
  profissional: { id?: number | null; nome?: string | null };
  aluno: { id: number; nome: string; telefone?: string | null; avatar_url?: string | null };
  plano: { id?: number | null; descricao?: string | null };
  status_aula: string;
  confirmacao: boolean;
  flags: { tem_preliminares: boolean; cobranca_pendente: boolean; observacao_importante: boolean };
  ultima_evolucao: { texto?: string | null; dt_evolucao?: string | null };
};

type OperacaoResponse = {
  data_inicio: string;
  data_fim: string;
  total: number;
  items: AulaOperacao[];
};

const STATUS_LABELS: Record<string, string> = {
  aguardando_chegar: "Aguardando chegar",
  em_aula: "Em aula",
  finalizada: "Finalizada",
  faltou: "Faltou",
  remarcada: "Remarcada"
};

const STATUS_STYLES: Record<string, string> = {
  aguardando_chegar: "bg-amber-100 text-amber-900",
  em_aula: "bg-emerald-100 text-emerald-900",
  finalizada: "bg-slate-200 text-slate-800",
  faltou: "bg-rose-100 text-rose-900",
  remarcada: "bg-indigo-100 text-indigo-900"
};

const QUICK_ACTIONS = [
  { id: "chegou", label: "Chegou", icon: "OK" },
  { id: "evolucao", label: "Evolucao", icon: "EV" },
  { id: "whatsapp", label: "WhatsApp", icon: "WA" }
];

const STATUS_MAP_FROM_ACTION: Record<string, string> = {
  chegou: "em_aula",
  iniciar: "em_aula",
  finalizar: "finalizada",
  faltou: "faltou",
  remarcar: "remarcada"
};

function formatTime(iso: string) {
  const date = new Date(iso);
  return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

function formatPhone(phone?: string | null) {
  if (!phone) return "";
  const digits = phone.replace(/\D/g, "");
  return digits.startsWith("55") ? digits : `55${digits}`;
}

function toISODate(date: Date) {
  return date.toISOString().slice(0, 10);
}

export default function Page() {
  const [mode, setMode] = useState<"agenda" | "operacao">("operacao");
  const [periodo, setPeriodo] = useState<"hoje" | "amanha" | "semana">("hoje");
  const [selectedDate, setSelectedDate] = useState<string>(toISODate(new Date()));
  const [items, setItems] = useState<AulaOperacao[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<AulaOperacao | null>(null);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState({
    unidade: "",
    profissional: "",
    status: ""
  });
  const [evolucaoText, setEvolucaoText] = useState("");
  const searchRef = useRef<HTMLInputElement | null>(null);

  const filteredItems = useMemo(() => items, [items]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "/") {
        event.preventDefault();
        searchRef.current?.focus();
      }
      if (event.key === "Enter" && !selected && filteredItems.length > 0) {
        setSelected(filteredItems[0]);
      }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s" && selected) {
        event.preventDefault();
        handleSalvarEvolucao(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selected, filteredItems]);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);
    api
      .get<OperacaoResponse>("/aulas/operacao", {
        params: {
          data: selectedDate,
          periodo,
          unidade_id: filters.unidade || undefined,
          profissional_id: filters.profissional || undefined,
          status_aula: filters.status || undefined,
          q: search || undefined
        }
      })
      .then((resp) => {
        if (!isMounted) return;
        setItems(resp.data.items);
      })
      .catch(() => {
        if (!isMounted) return;
        setError("Nao foi possivel carregar as aulas. Tente novamente.");
      })
      .finally(() => {
        if (!isMounted) return;
        setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [periodo, selectedDate, filters, search]);

  const groupedByTime = useMemo(() => {
    const map = new Map<string, AulaOperacao[]>();
    filteredItems.forEach((item) => {
      const time = formatTime(item.dt_inicio);
      const current = map.get(time) ?? [];
      current.push(item);
      map.set(time, current);
    });
    return Array.from(map.entries());
  }, [filteredItems]);

  const options = useMemo(() => {
    const unidades = new Map<string, string>();
    const profissionais = new Map<string, string>();
    filteredItems.forEach((item) => {
      if (item.unidade_id && item.unidade) {
        unidades.set(String(item.unidade_id), item.unidade);
      }
      if (item.profissional?.id && item.profissional?.nome) {
        profissionais.set(String(item.profissional.id), item.profissional.nome);
      }
    });
    return {
      unidades: Array.from(unidades.entries()),
      profissionais: Array.from(profissionais.entries())
    };
  }, [filteredItems]);

  const weekDates = useMemo(() => {
    const base = new Date(selectedDate);
    const start = new Date(base);
    start.setDate(base.getDate() - base.getDay() + 1);
    return Array.from({ length: 5 }).map((_, index) => {
      const day = new Date(start);
      day.setDate(start.getDate() + index);
      return day;
    });
  }, [selectedDate]);

  const handleQuickAction = async (action: string, item: AulaOperacao) => {
    if (action === "evolucao") {
      setSelected(item);
      setEvolucaoText("");
      return;
    }
    if (action === "whatsapp") {
      const phone = formatPhone(item.aluno.telefone);
      if (phone) {
        window.open(`https://wa.me/${phone}`, "_blank");
      }
      return;
    }
    if (action === "chegou") {
      await atualizarStatus(item, "chegou");
    }
  };

  const atualizarStatus = async (item: AulaOperacao, acao: string) => {
    try {
      const resp = await api.patch(`/aulas/${item.id}/status`, { acao });
      setItems((prev) =>
        prev.map((current) =>
          current.id === item.id
            ? { ...current, status_aula: STATUS_MAP_FROM_ACTION[acao] ?? current.status_aula }
            : current
        )
      );
      return resp.data;
    } catch {
      setError("Falha ao atualizar status.");
    }
  };

  const handleSalvarEvolucao = async (finalizar: boolean) => {
    if (!selected) return;
    if (!evolucaoText.trim()) {
      setError("Digite a evolucao antes de salvar.");
      return;
    }
    try {
      await api.post(`/aulas/${selected.id}/evolucoes`, {
        texto: evolucaoText,
        profissional_id: selected.profissional?.id,
        finalizar
      });
      setEvolucaoText("");
      setItems((prev) =>
        prev.map((item) =>
          item.id === selected.id
            ? {
                ...item,
                status_aula: finalizar ? "finalizada" : item.status_aula,
                ultima_evolucao: {
                  texto: evolucaoText,
                  dt_evolucao: new Date().toISOString()
                }
              }
            : item
        )
      );
    } catch {
      setError("Falha ao salvar evolucao.");
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Aulas</p>
            <h1 className="text-3xl font-display">Painel operacional</h1>
            <p className="text-sm text-gray-500">Fluxo rapido para o dia a dia do profissional.</p>
          </div>
          <div className="flex items-center gap-2 rounded-full bg-white/70 p-1 shadow-sm">
            <button
              className={cn(
                "rounded-full px-4 py-2 text-sm font-medium transition",
                mode === "agenda" ? "bg-black text-white" : "text-gray-500"
              )}
              onClick={() => setMode("agenda")}
            >
              Agenda
            </button>
            <button
              className={cn(
                "rounded-full px-4 py-2 text-sm font-medium transition",
                mode === "operacao" ? "bg-black text-white" : "text-gray-500"
              )}
              onClick={() => setMode("operacao")}
            >
              Operacao
            </button>
          </div>
        </div>

        <section className="rounded-[28px] border border-white/60 bg-white/70 p-6 shadow-lg">
          <div className="grid gap-4 lg:grid-cols-[1.3fr_1fr]">
            <div className="space-y-3">
              <label className="text-xs font-semibold uppercase tracking-widest text-gray-500">Busca rapida</label>
              <div className="flex items-center gap-3 rounded-2xl border border-black/10 bg-white px-4 py-3">
                <span className="text-xs font-semibold text-gray-400">BUSCA</span>
                <input
                  ref={searchRef}
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Aluno, CPF ou telefone"
                  className="w-full bg-transparent text-sm outline-none"
                />
                <span className="rounded-full bg-black/5 px-2 py-1 text-xs">/</span>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
                <span>Atalhos:</span>
                <span className="rounded-full bg-black/5 px-2 py-1">/ busca</span>
                <span className="rounded-full bg-black/5 px-2 py-1">Enter abre</span>
                <span className="rounded-full bg-black/5 px-2 py-1">Ctrl+S salva</span>
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-black/10 bg-white p-3">
                <label className="text-xs font-semibold uppercase tracking-widest text-gray-500">Periodo</label>
                <div className="mt-2 flex flex-wrap gap-2">
                  {(["hoje", "amanha", "semana"] as const).map((value) => (
                    <button
                      key={value}
                      onClick={() => setPeriodo(value)}
                      className={cn(
                        "rounded-full px-3 py-1 text-xs font-semibold",
                        periodo === value ? "bg-black text-white" : "bg-black/5 text-gray-600"
                      )}
                    >
                      {value === "amanha" ? "Amanha" : value[0].toUpperCase() + value.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl border border-black/10 bg-white p-3">
                <label className="text-xs font-semibold uppercase tracking-widest text-gray-500">Data alvo</label>
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(event) => setSelectedDate(event.target.value)}
                  className="mt-2 w-full rounded-xl border border-black/10 bg-transparent px-3 py-2 text-sm"
                />
              </div>
              <div className="rounded-2xl border border-black/10 bg-white p-3">
                <label className="text-xs font-semibold uppercase tracking-widest text-gray-500">Unidade</label>
                <select
                  value={filters.unidade}
                  onChange={(event) => setFilters((prev) => ({ ...prev, unidade: event.target.value }))}
                  className="mt-2 w-full rounded-xl border border-black/10 bg-transparent px-3 py-2 text-sm"
                >
                  <option value="">Todas</option>
                  {options.unidades.map(([id, label]) => (
                    <option key={id} value={id}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="rounded-2xl border border-black/10 bg-white p-3">
                <label className="text-xs font-semibold uppercase tracking-widest text-gray-500">Profissional</label>
                <select
                  value={filters.profissional}
                  onChange={(event) => setFilters((prev) => ({ ...prev, profissional: event.target.value }))}
                  className="mt-2 w-full rounded-xl border border-black/10 bg-transparent px-3 py-2 text-sm"
                >
                  <option value="">Todos</option>
                  {options.profissionais.map(([id, label]) => (
                    <option key={id} value={id}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="rounded-2xl border border-black/10 bg-white p-3 sm:col-span-2">
                <label className="text-xs font-semibold uppercase tracking-widest text-gray-500">Status</label>
                <div className="mt-2 flex flex-wrap gap-2">
                  {Object.keys(STATUS_LABELS).map((status) => (
                    <button
                      key={status}
                      onClick={() => setFilters((prev) => ({ ...prev, status: prev.status === status ? "" : status }))}
                      className={cn(
                        "rounded-full px-3 py-1 text-xs font-semibold",
                        filters.status === status ? "bg-black text-white" : "bg-black/5 text-gray-600"
                      )}
                    >
                      {STATUS_LABELS[status]}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
        )}

        {mode === "operacao" ? (
          <section className="space-y-6">
            {loading ? (
              <div className="grid gap-4">
                {Array.from({ length: 4 }).map((_, index) => (
                  <div key={index} className="rounded-[24px] bg-white/70 p-6">
                    <div className="h-4 w-40 animate-pulse rounded-full bg-black/10" />
                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      {Array.from({ length: 2 }).map((__, cardIndex) => (
                        <div key={cardIndex} className="h-28 rounded-2xl bg-black/5" />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              groupedByTime.map(([timeLabel, cards]) => (
                <div key={timeLabel} className="rounded-[26px] border border-white/70 bg-white/70 p-5 shadow-sm">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Horario</p>
                      <h2 className="text-2xl font-display">{timeLabel}</h2>
                    </div>
                    <span className="rounded-full bg-black/5 px-3 py-1 text-xs text-gray-500">
                      {cards.length} aluno(s)
                    </span>
                  </div>
                  <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    {cards.map((item) => (
                      <article
                        key={item.id}
                        onClick={() => {
                          setSelected(item);
                          setEvolucaoText(item.ultima_evolucao?.texto ?? "");
                        }}
                        className="group cursor-pointer rounded-2xl border border-black/10 bg-white p-4 shadow-sm transition hover:-translate-y-1 hover:shadow-lg"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="text-xs uppercase tracking-[0.2em] text-gray-400">
                              {formatTime(item.dt_inicio)}  {item.unidade || "Unidade"}
                            </p>
                            <h3 className="text-lg font-semibold">{item.aluno.nome}</h3>
                            <p className="text-xs text-gray-500">{item.plano.descricao || "Plano nao informado"}</p>
                          </div>
                          <span className={cn("rounded-full px-3 py-1 text-xs font-semibold", STATUS_STYLES[item.status_aula])}>
                            {STATUS_LABELS[item.status_aula] ?? "Aguardando"}
                          </span>
                        </div>
                        <div className="mt-3 grid gap-2 text-xs text-gray-600">
                          <div className="flex items-center justify-between">
                            <span>Sala</span>
                            <span className="font-medium">{item.sala || "Sala principal"}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>Profissional</span>
                            <span className="font-medium">{item.profissional.nome || "-"}</span>
                          </div>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          <span
                            className={cn(
                              "rounded-full px-2 py-1 text-[11px] font-semibold",
                              item.confirmacao ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
                            )}
                          >
                            {item.confirmacao ? "Confirmado" : "Nao confirmado"}
                          </span>
                          {!item.flags.tem_preliminares && (
                            <span className="rounded-full bg-rose-100 px-2 py-1 text-[11px] font-semibold text-rose-700">
                              Preliminares pendentes
                            </span>
                          )}
                          {item.flags.cobranca_pendente && (
                            <span className="rounded-full bg-amber-100 px-2 py-1 text-[11px] font-semibold text-amber-700">
                              Cobranca pendente
                            </span>
                          )}
                        </div>
                        <div className="mt-4 flex items-center justify-between border-t border-dashed border-black/10 pt-3">
                          {QUICK_ACTIONS.map((action) => (
                            <button
                              key={action.id}
                              onClick={(event) => {
                                event.stopPropagation();
                                handleQuickAction(action.id, item);
                              }}
                              className="rounded-full border border-black/10 px-3 py-1 text-xs font-semibold transition hover:bg-black/5"
                            >
                              <span className="mr-1">{action.icon}</span>
                              {action.label}
                            </button>
                          ))}
                        </div>
                      </article>
                    ))}
                  </div>
                </div>
              ))
            )}
          </section>
        ) : (
          <section className="rounded-[26px] border border-white/70 bg-white/70 p-6 shadow-lg">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Agenda semanal</p>
                <h2 className="text-2xl font-display">Visao por semana</h2>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                {weekDates.map((day) => (
                  <span key={day.toISOString()} className="rounded-full bg-black/5 px-3 py-1">
                    {day.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}
                  </span>
                ))}
              </div>
            </div>
            <div className="mt-6 grid gap-4 lg:grid-cols-5">
              {weekDates.map((day) => {
                const dayISO = toISODate(day);
                const dayItems = items.filter((item) => item.dt_inicio.startsWith(dayISO));
                return (
                  <div key={dayISO} className="rounded-2xl border border-black/10 bg-white p-3">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-gray-500">
                      {day.toLocaleDateString("pt-BR", { weekday: "short" })}
                    </p>
                    <h3 className="text-lg font-semibold">{day.getDate()}</h3>
                    <div className="mt-3 grid gap-2">
                      {dayItems.length === 0 && (
                        <div className="rounded-xl border border-dashed border-black/10 px-3 py-4 text-xs text-gray-400">
                          Sem aulas
                        </div>
                      )}
                      {dayItems.map((item) => (
                        <button
                          key={item.id}
                          onClick={() => {
                            setSelected(item);
                            setMode("operacao");
                          }}
                          className="rounded-xl border border-black/10 bg-gradient-to-r from-sky-100 via-white to-white p-3 text-left text-xs"
                        >
                          <p className="text-[11px] uppercase tracking-[0.2em] text-gray-500">
                            {formatTime(item.dt_inicio)}
                          </p>
                          <p className="font-semibold">{item.aluno.nome}</p>
                          <p className="text-[11px] text-gray-500">{item.plano.descricao}</p>
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}
      </div>

      {selected && (
        <aside className="fixed inset-y-0 right-0 z-50 w-full max-w-xl overflow-y-auto border-l border-black/10 bg-white/95 p-6 shadow-2xl backdrop-blur">
          <button
            onClick={() => setSelected(null)}
            className="mb-4 rounded-full border border-black/10 px-3 py-1 text-xs font-semibold text-gray-600 hover:bg-black/5"
          >
            Fechar
          </button>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-sky-200 to-coral" />
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-gray-500">Aluno</p>
                <h3 className="text-2xl font-display">{selected.aluno.nome}</h3>
                <p className="text-sm text-gray-500">
                  {formatTime(selected.dt_inicio)}  {selected.sala || "Sala principal"}
                </p>
              </div>
            </div>
            <span className={cn("rounded-full px-3 py-1 text-xs font-semibold", STATUS_STYLES[selected.status_aula])}>
              {STATUS_LABELS[selected.status_aula]}
            </span>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {[
              { id: "chegou", label: "Chegou / Iniciar" },
              { id: "finalizar", label: "Finalizar" },
              { id: "faltou", label: "Marcar falta" },
              { id: "remarcar", label: "Remarcar" }
            ].map((action) => (
              <button
                key={action.id}
                onClick={() => atualizarStatus(selected, action.id)}
                className="rounded-full border border-black/10 px-4 py-2 text-xs font-semibold hover:bg-black/5"
              >
                {action.label}
              </button>
            ))}
          </div>

          <div className="mt-6 grid gap-3 rounded-2xl border border-black/10 bg-white p-4 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Confirmacao</span>
              <span className="font-semibold">{selected.confirmacao ? "Confirmado" : "Nao confirmado"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Preliminares</span>
              <span className="font-semibold">{selected.flags.tem_preliminares ? "OK" : "Pendente"}</span>
            </div>
            {!selected.flags.tem_preliminares && (
              <button className="rounded-xl border border-dashed border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-700">
                Solicitar ao aluno
              </button>
            )}
          </div>

          <div className="mt-6">
            <div className="flex flex-wrap gap-2 text-xs font-semibold">
              {[
                "evolucao",
                "avaliacoes",
                "historico",
                "cobranca",
                "acoes"
              ].map((tab) => (
                <button key={tab} className="rounded-full border border-black/10 px-3 py-1 hover:bg-black/5">
                  {tab === "evolucao"
                    ? "Evolucao"
                    : tab === "avaliacoes"
                    ? "Avaliacoes"
                    : tab === "historico"
                    ? "Historico"
                    : tab === "cobranca"
                    ? "Cobranca"
                    : "Acoes"}
                </button>
              ))}
            </div>
            <div className="mt-4 space-y-4 rounded-2xl border border-black/10 bg-white p-4">
              <div className="flex flex-wrap gap-2">
                {["Dor/limitacao", "Carga/Exercicios", "Observacoes", "Plano da proxima aula"].map((chip) => (
                  <button
                    key={chip}
                    onClick={() => setEvolucaoText((prev) => `${prev}${prev ? "\n" : ""}${chip}: `)}
                    className="rounded-full bg-black/5 px-3 py-1 text-xs font-semibold text-gray-600"
                  >
                    {chip}
                  </button>
                ))}
              </div>
              <textarea
                value={evolucaoText}
                onChange={(event) => setEvolucaoText(event.target.value)}
                rows={6}
                placeholder="Escreva a evolucao da aula..."
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none"
              />
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleSalvarEvolucao(false)}
                  className="rounded-full bg-black px-4 py-2 text-xs font-semibold text-white"
                >
                  Salvar
                </button>
                <button
                  onClick={() => handleSalvarEvolucao(true)}
                  className="rounded-full border border-black/10 px-4 py-2 text-xs font-semibold text-gray-700"
                >
                  Salvar e Finalizar aula
                </button>
                <button
                  onClick={() => {
                    const phone = formatPhone(selected.aluno.telefone);
                    if (phone) window.open(`https://wa.me/${phone}`, "_blank");
                  }}
                  className="rounded-full border border-black/10 px-4 py-2 text-xs font-semibold text-gray-700"
                >
                  WhatsApp
                </button>
              </div>
            </div>
            <div className="mt-4 rounded-2xl border border-black/10 bg-white p-4">
              <h4 className="text-sm font-semibold">Cobranca</h4>
              <p className="text-xs text-gray-500">
                {selected.flags.cobranca_pendente ? "Ha cobrancas pendentes." : "Sem cobrancas pendentes."}
              </p>
              <button className="mt-3 rounded-full border border-black/10 px-4 py-2 text-xs font-semibold text-gray-700">
                Acessar Cobranca(s)
              </button>
            </div>
          </div>
        </aside>
      )}
    </AppShell>
  );
}

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import Link from "@tiptap/extension-link";
import TextAlign from "@tiptap/extension-text-align";
import Image from "@tiptap/extension-image";
import Mention from "@tiptap/extension-mention";
import AppShell from "@/components/layout/AppShell";
import api from "@/lib/api";

type PageResponse<T> = {
  items: T[];
  meta: { page: number; page_size: number; total: number };
};

type ContratoModelo = { id: number; titulo: string; descricao: string; ativo: boolean };
type TermoVariavel = { key: string; label: string; example: string };

export default function Page() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [showPreview, setShowPreview] = useState(true);
  const [editing, setEditing] = useState<ContratoModelo | null>(null);
  const [form, setForm] = useState({ titulo: "", descricao: "", ativo: true });
  const variaveisRef = useRef<TermoVariavel[]>([]);

  const modelosQuery = useQuery({
    queryKey: ["contratos-modelos"],
    queryFn: async () => {
      const resp = await api.get<PageResponse<ContratoModelo>>("/contratos/modelos", {
        params: { page: 1, page_size: 200, order_by: "criado_em", order_dir: "desc" }
      });
      return resp.data.items;
    }
  });

  const variaveisQuery = useQuery({
    queryKey: ["contratos-modelos-variaveis"],
    queryFn: async () => {
      const resp = await api.get<TermoVariavel[]>("/contratos/modelos/variaveis");
      return resp.data;
    }
  });

  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      Link.configure({ openOnClick: false }),
      TextAlign.configure({ types: ["heading", "paragraph"] }),
      Image,
      Mention.configure({
        HTMLAttributes: {
          class:
            "rounded-md bg-black/5 px-1.5 py-0.5 text-[11px] font-medium text-gray-700"
        },
        suggestion: {
          char: "#",
          items: ({ query }) => {
            const term = query.toLowerCase();
            return variaveisRef.current
              .filter(
                (item) =>
                  item.label.toLowerCase().includes(term) || item.key.toLowerCase().includes(term)
              )
              .slice(0, 8);
          },
          render: () => {
            let popup: HTMLDivElement | null = null;
            let listEl: HTMLDivElement | null = null;
            let items: TermoVariavel[] = [];
            let selectedIndex = 0;
            let command: ((item: { id: string; label: string }) => void) | null = null;

            const update = () => {
              if (!listEl) return;
              listEl.innerHTML = "";
              items.forEach((item, index) => {
                const button = document.createElement("button");
                button.type = "button";
                button.className =
                  "flex w-full items-start gap-2 rounded-lg px-2 py-1 text-left text-xs hover:bg-black/5";
                if (index === selectedIndex) {
                  button.className += " bg-black/10";
                }
                button.innerHTML = `<span class="font-medium">${item.label}</span><span class="text-gray-500">#${item.key}</span>`;
                button.addEventListener("click", () => {
                  command?.({ id: item.key, label: item.label });
                });
                listEl?.appendChild(button);
              });
            };

            const position = (rect: DOMRect | null) => {
              if (!popup || !rect) return;
              popup.style.left = `${rect.left}px`;
              popup.style.top = `${rect.bottom + 8}px`;
            };

            return {
              onStart: (props) => {
                items = props.items as TermoVariavel[];
                command = props.command;
                selectedIndex = 0;
                popup = document.createElement("div");
                popup.className =
                  "z-50 rounded-xl border border-black/10 bg-white/95 p-2 shadow-xl backdrop-blur";
                listEl = document.createElement("div");
                listEl.className = "flex flex-col gap-1";
                popup.appendChild(listEl);
                document.body.appendChild(popup);
                update();
                position(props.clientRect?.() ?? null);
              },
              onUpdate: (props) => {
                items = props.items as TermoVariavel[];
                command = props.command;
                selectedIndex = 0;
                update();
                position(props.clientRect?.() ?? null);
              },
              onKeyDown: (props) => {
                if (props.event.key === "ArrowDown") {
                  selectedIndex = (selectedIndex + 1) % items.length;
                  update();
                  return true;
                }
                if (props.event.key === "ArrowUp") {
                  selectedIndex = (selectedIndex - 1 + items.length) % items.length;
                  update();
                  return true;
                }
                if (props.event.key === "Enter") {
                  const item = items[selectedIndex];
                  if (item) {
                    command?.({ id: item.key, label: item.label });
                  }
                  return true;
                }
                return false;
              },
              onExit: () => {
                popup?.remove();
                popup = null;
              }
            };
          }
        },
        renderLabel({ node }) {
          return `{{${node.attrs.id}}}`;
        },
        renderHTML({ node, HTMLAttributes }) {
          return [
            "span",
            { ...HTMLAttributes, "data-mention": node.attrs.id },
            `{{${node.attrs.id}}}`
          ];
        }
      })
    ],
    content: form.descricao || "",
    immediatelyRender: false,
    onUpdate: ({ editor }) => {
      setForm((f) => ({ ...f, descricao: editor.getHTML() }));
    }
  });

  useEffect(() => {
    variaveisRef.current = variaveisQuery.data ?? [];
  }, [variaveisQuery.data]);

  useEffect(() => {
    if (!editor) return;
    const current = editor.getHTML();
    if ((form.descricao || "") !== current) {
      editor.commands.setContent(form.descricao || "", false);
    }
  }, [editor, form.descricao]);

  const createModelo = useMutation({
    mutationFn: async () => {
      return api.post("/contratos/modelos", form);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contratos-modelos"] });
      setShowModal(false);
      setEditing(null);
      setForm({ titulo: "", descricao: "", ativo: true });
    }
  });

  const updateModelo = useMutation({
    mutationFn: async () => {
      return api.put(`/contratos/modelos/${editing?.id}`, form);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contratos-modelos"] });
      setShowModal(false);
      setEditing(null);
      setForm({ titulo: "", descricao: "", ativo: true });
    }
  });

  const setLink = () => {
    if (!editor) return;
    const url = window.prompt("URL do link");
    if (!url) return;
    editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
  };

  const insertImage = () => {
    if (!editor) return;
    const url = window.prompt("URL da imagem");
    if (!url) return;
    editor.chain().focus().setImage({ src: url }).run();
  };

  const uppercaseSelection = () => {
    if (!editor) return;
    const { from, to } = editor.state.selection;
    if (from === to) return;
    const text = editor.state.doc.textBetween(from, to, "\n");
    editor.chain().focus().insertContentAt({ from, to }, text.toUpperCase()).run();
  };

  const filtered = useMemo(() => {
    const items = modelosQuery.data ?? [];
    if (!search.trim()) return items;
    const term = search.toLowerCase();
    return items.filter((m) => m.titulo.toLowerCase().includes(term));
  }, [modelosQuery.data, search]);

  const insertVariable = (key: string) => {
    if (!editor) return;
    editor.chain().focus().insertContent(`{{${key}}}`).run();
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-widest text-gray-500">Contratos</p>
            <h1 className="text-3xl font-display">Modelo de contrato</h1>
          </div>
          <button
            className="rounded-full bg-black px-4 py-2 text-white"
            onClick={() => {
              setEditing(null);
              setForm({ titulo: "", descricao: "", ativo: true });
              setShowModal(true);
            }}
          >
            Novo
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <input
            className="w-full max-w-sm rounded-full border border-black/10 bg-white/80 px-4 py-2"
            placeholder="Buscar modelo..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="rounded-2xl bg-white/70 p-4">
          <div className="grid grid-cols-3 gap-4 border-b border-black/10 pb-3 text-xs uppercase tracking-widest text-gray-500">
            <span>Titulo</span>
            <span>Status</span>
            <span>Acoes</span>
          </div>
          <div className="divide-y divide-black/5">
            {(filtered ?? []).map((modelo) => (
              <div key={modelo.id} className="grid grid-cols-3 gap-4 py-3 text-sm">
                <span className="font-medium">{modelo.titulo}</span>
                <span className="text-xs text-gray-500">{modelo.ativo ? "Ativo" : "Inativo"}</span>
                <div>
                  <button
                    className="rounded-full bg-white/70 px-3 py-1 text-xs"
                    onClick={() => {
                      setEditing(modelo);
                      setForm({
                        titulo: modelo.titulo,
                        descricao: modelo.descricao,
                        ativo: modelo.ativo
                      });
                      setShowModal(true);
                    }}
                  >
                    Editar
                  </button>
                </div>
              </div>
            ))}
            {(filtered ?? []).length === 0 && (
              <div className="py-6 text-sm text-gray-500">Nenhum modelo encontrado.</div>
            )}
          </div>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-6">
          <div className="w-full max-w-6xl rounded-3xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-display">
                {editing ? "Editar modelo" : "Novo modelo"}
              </h2>
              <button className="text-sm text-gray-500" onClick={() => setShowModal(false)}>
                Fechar
              </button>
            </div>

            <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_1fr_280px]">
              <div className="space-y-3">
                <div className="grid gap-3 sm:grid-cols-2">
                  <input
                    className="rounded-xl border border-black/10 p-3"
                    placeholder="Titulo do modelo"
                    value={form.titulo}
                    onChange={(e) => setForm((f) => ({ ...f, titulo: e.target.value }))}
                  />
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={form.ativo}
                      onChange={(e) => setForm((f) => ({ ...f, ativo: e.target.checked }))}
                    />
                    Ativo
                  </label>
                </div>
                <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-black/10 bg-white/80 p-2 text-xs">
                  <button
                    className="rounded-full bg-white/70 px-3 py-1"
                    onClick={() => editor?.chain().focus().toggleBold().run()}
                    type="button"
                  >
                    Negrito
                  </button>
                  <button
                    className="rounded-full bg-white/70 px-3 py-1"
                    onClick={() => editor?.chain().focus().toggleItalic().run()}
                    type="button"
                  >
                    Italico
                  </button>
                  <button
                    className="rounded-full bg-white/70 px-3 py-1"
                    onClick={() => editor?.chain().focus().toggleUnderline().run()}
                    type="button"
                  >
                    Sublinhado
                  </button>
                  <button
                    className="rounded-full bg-white/70 px-3 py-1"
                    onClick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
                    type="button"
                  >
                    Titulo
                  </button>
                  <button
                    className="rounded-full bg-white/70 px-3 py-1"
                    onClick={() => editor?.chain().focus().toggleBulletList().run()}
                    type="button"
                  >
                    Lista
                  </button>
                  <button className="rounded-full bg-white/70 px-3 py-1" onClick={setLink}>
                    Link
                  </button>
                  <button className="rounded-full bg-white/70 px-3 py-1" onClick={insertImage}>
                    Imagem
                  </button>
                  <button
                    className="rounded-full bg-white/70 px-3 py-1"
                    onClick={uppercaseSelection}
                  >
                    Maiuscula
                  </button>
                  <button
                    className="rounded-full bg-white/70 px-3 py-1"
                    onClick={() => editor?.chain().focus().setTextAlign("left").run()}
                  >
                    Esquerda
                  </button>
                  <button
                    className="rounded-full bg-white/70 px-3 py-1"
                    onClick={() => editor?.chain().focus().setTextAlign("center").run()}
                  >
                    Centro
                  </button>
                  <button
                    className="rounded-full bg-white/70 px-3 py-1"
                    onClick={() => editor?.chain().focus().setTextAlign("right").run()}
                  >
                    Direita
                  </button>
                </div>
                <div className="rounded-2xl border border-black/10 bg-white/80 p-3">
                  <div className="mb-2 flex items-center justify-between text-xs text-gray-500">
                    <span>Digite # para inserir variaveis do sistema.</span>
                    <button
                      className="rounded-full bg-white/70 px-3 py-1 text-[11px]"
                      onClick={() => setShowPreview((v) => !v)}
                      type="button"
                    >
                      {showPreview ? "Ocultar preview" : "Mostrar preview"}
                    </button>
                  </div>
                  <EditorContent editor={editor} className="min-h-[420px] outline-none text-sm" />
                </div>
                <button
                  className="rounded-full bg-black px-4 py-2 text-white"
                  onClick={() => (editing ? updateModelo.mutate() : createModelo.mutate())}
                  disabled={!form.titulo || !form.descricao}
                >
                  {editing ? "Salvar alteracoes" : "Salvar modelo"}
                </button>
              </div>
              {showPreview && (
                <div className="rounded-2xl bg-white/70 p-4">
                  <p className="text-xs uppercase tracking-widest text-gray-400">Preview</p>
                  <div
                    className="prose prose-sm mt-3 max-w-none rounded-xl bg-white/80 p-4"
                    dangerouslySetInnerHTML={{
                      __html: form.descricao || "<p>Sem conteudo.</p>"
                    }}
                  />
                </div>
              )}
              <div className="rounded-2xl bg-white/70 p-4">
                <p className="text-xs uppercase tracking-widest text-gray-400">Variaveis</p>
                <div className="mt-2 space-y-2 text-xs">
                  {(variaveisQuery.data ?? []).map((v) => (
                    <div
                      key={v.key}
                      className="cursor-pointer rounded-xl bg-white/80 p-2"
                      onDoubleClick={() => insertVariable(v.key)}
                      title="Duplo clique para inserir"
                    >
                      <p className="font-medium">{v.label}</p>
                      <p className="text-gray-500">
                        {"{{"}
                        {v.key}
                        {"}}"} • ex: {v.example}
                      </p>
                      <button
                        className="mt-2 rounded-full bg-white/70 px-3 py-1 text-[10px]"
                        onClick={() => insertVariable(v.key)}
                        type="button"
                      >
                        Inserir variavel
                      </button>
                    </div>
                  ))}
                  {(variaveisQuery.data ?? []).length === 0 && (
                    <p className="text-gray-500">Nenhuma variavel encontrada.</p>
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

/* Melhorias de usabilidade do Mayris Pilates (carrega depois de app.js). */
(function () {
  "use strict";

  /* ---------- 1) Abas lembram onde você estava ---------- */
  // A aba ativa vai para a URL (?aba=financeiro) e para o sessionStorage.
  // Assim, ao salvar algo e a página recarregar, a pessoa volta para a mesma aba,
  // e o link pode ser enviado direto para uma aba.
  var storeKey = "mayris:aba:" + location.pathname;

  function abaDoBotao(btn) {
    var alvo = btn && btn.getAttribute("data-bs-target");
    return alvo ? alvo.replace(/^#(tab-)?/, "") : "";
  }

  function restaurarAba() {
    var grupo = document.querySelector(".mayris-tabs");
    if (!grupo || !window.bootstrap) return;
    var quer = new URLSearchParams(location.search).get("aba");
    if (!quer) {
      try { quer = sessionStorage.getItem(storeKey); } catch (e) { quer = null; }
    }
    if (!quer) return;
    var botoes = grupo.querySelectorAll('[data-bs-toggle="pill"][data-bs-target], [data-bs-toggle="tab"][data-bs-target]');
    for (var i = 0; i < botoes.length; i++) {
      if (abaDoBotao(botoes[i]) === quer) {
        window.bootstrap.Tab.getOrCreateInstance(botoes[i]).show();
        break;
      }
    }
  }

  document.addEventListener("shown.bs.tab", function (event) {
    var btn = event.target;
    if (!btn.closest || !btn.closest(".mayris-tabs")) return;
    var aba = abaDoBotao(btn);
    if (!aba) return;
    try {
      var url = new URL(location.href);
      url.searchParams.set("aba", aba);
      history.replaceState(null, "", url);
    } catch (e) { /* navegador antigo: ignora */ }
    try { sessionStorage.setItem(storeKey, aba); } catch (e) { /* modo privado */ }
  });

  // Atalhos da ficha do aluno: abrem a aba pedida e rolam até ela
  document.addEventListener("click", function (event) {
    var atalho = event.target.closest && event.target.closest(".js-aba-atalho");
    if (!atalho || !window.bootstrap) return;
    var alvo = atalho.getAttribute("data-m-aba");
    var botao = document.querySelector('.mayris-tabs [data-bs-target="#tab-' + alvo + '"]');
    if (!botao) return;
    window.bootstrap.Tab.getOrCreateInstance(botao).show();
    botao.closest(".mayris-tabs").scrollIntoView({ behavior: "smooth", block: "start" });
  });

  function esconderAtalhosSemAba() {
    document.querySelectorAll(".js-aba-atalho").forEach(function (a) {
      var alvo = a.getAttribute("data-m-aba");
      if (!document.querySelector('.mayris-tabs [data-bs-target="#tab-' + alvo + '"]')) a.remove();
    });
  }

  /* ---------- 2) Avisos viram toasts que somem sozinhos ---------- */
  function criarToasts() {
    var avisos = document.querySelectorAll(".mayris-content > .mayris-alert, .mayris-content > .alert.mayris-alert");
    if (!avisos.length) return;
    var caixa = document.createElement("div");
    caixa.className = "m-toasts";
    caixa.setAttribute("aria-live", "polite");
    document.body.appendChild(caixa);

    avisos.forEach(function (aviso, i) {
      var tipo = (aviso.className.match(/alert-(\w+)/) || [, "info"])[1];
      var erro = tipo === "danger" || tipo === "error" || tipo === "warning";
      aviso.classList.add("m-toast", "m-toast--" + tipo);
      aviso.setAttribute("role", erro ? "alert" : "status");

      var fechar = document.createElement("button");
      fechar.type = "button";
      fechar.className = "m-toast__close";
      fechar.setAttribute("aria-label", "Fechar aviso");
      fechar.innerHTML = "&times;";
      aviso.appendChild(fechar);

      function sair() {
        aviso.classList.add("is-leaving");
        setTimeout(function () { aviso.remove(); if (!caixa.children.length) caixa.remove(); }, 260);
      }
      fechar.addEventListener("click", sair);
      caixa.appendChild(aviso);
      // sucesso/info somem em 6s; erro e alerta ficam até a pessoa fechar
      if (!erro) setTimeout(sair, 6000 + i * 400);
    });
  }

  /* ---------- 3) Busca do topo funciona de verdade ---------- */
  function ligarBuscaTopo() {
    var campo = document.querySelector(".mayris-topbar__search input");
    if (!campo) return;
    campo.setAttribute("aria-label", "Buscar aluno");
    campo.setAttribute("title", "Digite e tecle Enter (atalho: /)");
    campo.addEventListener("keydown", function (event) {
      if (event.key !== "Enter") return;
      var termo = campo.value.trim();
      if (termo) location.href = "/cadastros/alunos/?status=TODOS&q=" + encodeURIComponent(termo);
    });
  }

  /* ---------- 4) Atalho "/" foca a busca ---------- */
  document.addEventListener("keydown", function (event) {
    if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey) return;
    var alvo = event.target;
    if (alvo && (/^(INPUT|TEXTAREA|SELECT)$/.test(alvo.tagName) || alvo.isContentEditable)) return;
    var campo = document.querySelector('.mayris-filter input[name="q"]') || document.querySelector(".mayris-topbar__search input");
    if (campo) { event.preventDefault(); campo.focus(); campo.select(); }
  });

  /* ---------- 5) Cada tabela rola sem perder o cabeçalho ---------- */
  function cabecalhoFixo() {
    document.querySelectorAll(".table-responsive > .mayris-table").forEach(function (t) {
      t.closest(".table-responsive").classList.add("m-sticky-head");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    restaurarAba();
    esconderAtalhosSemAba();
    criarToasts();
    ligarBuscaTopo();
    cabecalhoFixo();
  });
})();

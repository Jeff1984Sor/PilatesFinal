document.addEventListener("submit", (event) => {
  const btn = event.target.querySelector("button[type='submit']");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = "Processando...";
  }
});

document.addEventListener("click", (event) => {
  const btn = event.target.closest(".js-var");
  if (!btn) return;
  event.preventDefault();
  const modal = btn.closest(".modal");
  if (!modal) return;
  const body = btn.closest(".modal-body");
  const targetName = body?.dataset.variableTarget || "conteudo_html";
  const field = modal.querySelector(`[name="${targetName}"]`);
  if (!field) return;
  const key = btn.dataset.var || "";
  const token = `{${key}}`;
  const start = field.selectionStart || 0;
  const end = field.selectionEnd || 0;
  const value = field.value || "";
  field.value = value.slice(0, start) + token + value.slice(end);
  field.focus();
  const cursor = start + token.length;
  field.setSelectionRange(cursor, cursor);
});

document.addEventListener("click", (event) => {
  const btn = event.target.closest(".js-format");
  if (!btn) return;
  event.preventDefault();
  const modal = btn.closest(".modal");
  if (!modal) return;
  const body = btn.closest(".modal-body");
  const targetName = body?.dataset.variableTarget || "conteudo_html";
  const field = modal.querySelector(`[name="${targetName}"]`);
  if (!field) return;
  const cmd = btn.dataset.cmd || "";
  applyFormat(field, cmd);
});

document.addEventListener("change", (event) => {
  const selectFamily = event.target.closest(".js-font-family");
  const selectSize = event.target.closest(".js-font-size");
  if (!selectFamily && !selectSize) return;
  const modal = event.target.closest(".modal");
  if (!modal) return;
  const body = event.target.closest(".modal-body");
  const targetName = body?.dataset.variableTarget || "conteudo_html";
  const field = modal.querySelector(`[name="${targetName}"]`);
  if (!field) return;
  if (selectFamily && selectFamily.value) {
    applyFormat(field, "font-family", selectFamily.value);
    selectFamily.selectedIndex = 0;
  }
  if (selectSize && selectSize.value) {
    applyFormat(field, "font-size", selectSize.value);
    selectSize.selectedIndex = 0;
  }
});

document.addEventListener("input", (event) => {
  const cpf = event.target.closest(".js-cpf");
  const phone = event.target.closest(".js-telefone");
  const cep = event.target.closest(".js-cep");
  const date = event.target.closest(".js-date");
  if (cpf) {
    cpf.value = maskCPF(cpf.value);
  }
  if (phone) {
    phone.value = maskPhone(phone.value);
  }
  if (cep) {
    cep.value = maskCEP(cep.value);
  }
  if (date && date.type === "text") {
    date.value = maskDate(date.value);
  }
});

document.addEventListener("focusin", (event) => {
  const date = event.target.closest(".js-date");
  if (!date) return;
  if (date.type === "date" && typeof date.showPicker === "function") {
    date.showPicker();
  }
});

document.addEventListener("shown.bs.modal", (event) => {
  const modal = event.target;
  if (!modal || !modal.querySelector) return;
  const inicio = modal.querySelector(".js-contrato-inicio");
  const fim = modal.querySelector(".js-contrato-fim");
  const plano = modal.querySelector(".js-plano");
  const valorParcela = modal.querySelector(".js-valor-parcela");
  const valorTotal = modal.querySelector(".js-valor-total");
  if (inicio && !inicio.value) {
    const today = new Date();
    inicio.value = today.toISOString().slice(0, 10);
  }
  if (plano && inicio && fim) {
    const selected = plano.selectedOptions[0];
    const duracao = parseInt(selected?.dataset?.duracao || "0", 10);
    if (selected && selected.value) {
      if (!fim.value) {
        fim.value = calcFimContrato(inicio.value, duracao || 1);
      }
    } else {
      fim.value = "";
    }
  }
  if (plano && valorParcela && valorTotal) {
    const selected = plano.selectedOptions[0];
    if (selected && selected.value) {
      const valor = parseFloat(selected.dataset.valor || "0");
      if (!valorParcela.value) {
        valorParcela.value = valor ? valor.toFixed(2) : "";
      }
      const duracao = parseInt(selected.dataset.duracao || "0", 10);
      if (!valorTotal.value) {
        valorTotal.value = valor && duracao ? (valor * duracao).toFixed(2) : "";
      }
    } else {
      valorParcela.value = "";
      valorTotal.value = "";
    }
  }

  const recorrencia = modal.querySelector("select[name='recorrencia']");
  const quantidade = modal.querySelector(".js-recorrencia-quantidade");
  if (recorrencia && quantidade) {
    if (recorrencia.value === "MENSAL" || recorrencia.value === "ANUAL") {
      quantidade.classList.remove("d-none");
    } else {
      quantidade.classList.add("d-none");
    }
  }
});

document.addEventListener("hidden.bs.modal", (event) => {
  const modal = event.target;
  if (!modal || !modal.querySelectorAll) return;
  modal.querySelectorAll(".js-photo-field").forEach((field) => {
    stopPhotoStream(field);
    const camera = field.querySelector(".js-photo-camera");
    if (camera) camera.classList.add("d-none");
  });
});

document.addEventListener("change", (event) => {
  const plano = event.target.closest(".js-plano");
  if (!plano) return;
  const modal = plano.closest(".modal");
  if (!modal) return;
  const inicio = modal.querySelector(".js-contrato-inicio");
  const fim = modal.querySelector(".js-contrato-fim");
  const valorParcela = modal.querySelector(".js-valor-parcela");
  const valorTotal = modal.querySelector(".js-valor-total");
  const selected = plano.selectedOptions[0];
  const duracao = parseInt(selected?.dataset?.duracao || "0", 10);
  if (inicio && fim) {
    if (selected && selected.value) {
      fim.value = calcFimContrato(inicio.value, duracao || 1);
    } else {
      fim.value = "";
    }
  }
  if (valorParcela && valorTotal) {
    if (selected && selected.value) {
      const valor = parseFloat(selected.dataset.valor || "0");
      valorParcela.value = valor ? valor.toFixed(2) : "";
      valorTotal.value = valor && duracao ? (valor * duracao).toFixed(2) : "";
    } else {
      valorParcela.value = "";
      valorTotal.value = "";
    }
  }
});

document.addEventListener("input", (event) => {
  const valorParcela = event.target.closest(".js-valor-parcela");
  if (!valorParcela) return;
  const modal = valorParcela.closest(".modal");
  const plano = modal?.querySelector(".js-plano");
  const valorTotal = modal?.querySelector(".js-valor-total");
  if (!plano || !valorTotal) return;
  const selected = plano.selectedOptions[0];
  const duracao = parseInt(selected?.dataset?.duracao || "0", 10);
  const valor = parseFloat(valorParcela.value || "0");
  valorTotal.value = valor && duracao ? (valor * duracao).toFixed(2) : "";
});

document.addEventListener("click", (event) => {
  const btn = event.target.closest(".js-add-phone");
  if (!btn) return;
  event.preventDefault();
  const container = btn.closest(".js-phones");
  if (!container) return;
  const count = container.querySelectorAll(".js-phone-row").length + 1;
  const row = document.createElement("div");
  row.className = "row g-2 align-items-center mb-2 js-phone-row";
  row.innerHTML = `
    <div class="col-md-6">
      <input class="form-control js-telefone" name="telefone_${count}" placeholder="(00) 00000-0000" />
    </div>
    <div class="col-md-2">
      <button type="button" class="btn btn-outline-danger js-remove-phone">Remover</button>
    </div>
  `;
  container.appendChild(row);
});

document.addEventListener("click", (event) => {
  const btn = event.target.closest(".js-remove-phone");
  if (!btn) return;
  event.preventDefault();
  const row = btn.closest(".js-phone-row");
  if (row) row.remove();
});

const photoStreams = new WeakMap();

document.addEventListener("click", async (event) => {
  const btn = event.target.closest(".js-photo-start");
  if (!btn) return;
  event.preventDefault();
  const field = btn.closest(".js-photo-field");
  if (!field) return;
  const camera = field.querySelector(".js-photo-camera");
  const video = field.querySelector(".js-photo-video");
  if (!camera || !video || !navigator.mediaDevices?.getUserMedia) {
    alert("Camera indisponivel neste navegador.");
    return;
  }
  stopPhotoStream(field);
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    photoStreams.set(field, stream);
    video.srcObject = stream;
    await video.play();
    camera.classList.remove("d-none");
  } catch (err) {
    alert("Nao foi possivel acessar a camera.");
  }
});

document.addEventListener("click", (event) => {
  const btn = event.target.closest(".js-photo-shot");
  if (!btn) return;
  event.preventDefault();
  const field = btn.closest(".js-photo-field");
  if (!field) return;
  const video = field.querySelector(".js-photo-video");
  const canvas = field.querySelector(".js-photo-canvas");
  const input = field.querySelector(".js-photo-input");
  const preview = field.querySelector(".js-photo-preview");
  if (!video || !canvas || !input || !preview) return;
  const width = video.videoWidth || 640;
  const height = video.videoHeight || 480;
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.drawImage(video, 0, 0, width, height);
  canvas.toBlob((blob) => {
    if (!blob) return;
    const file = new File([blob], "foto-aluno.jpg", { type: "image/jpeg" });
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
    updatePhotoPreview(preview, URL.createObjectURL(blob));
    stopPhotoStream(field);
    const camera = field.querySelector(".js-photo-camera");
    if (camera) camera.classList.add("d-none");
  }, "image/jpeg", 0.92);
});

document.addEventListener("click", (event) => {
  const btn = event.target.closest(".js-photo-stop");
  if (!btn) return;
  event.preventDefault();
  const field = btn.closest(".js-photo-field");
  if (!field) return;
  stopPhotoStream(field);
  const camera = field.querySelector(".js-photo-camera");
  if (camera) camera.classList.add("d-none");
});

document.addEventListener("change", (event) => {
  const input = event.target.closest(".js-photo-input");
  if (!input) return;
  const field = input.closest(".js-photo-field");
  const preview = field?.querySelector(".js-photo-preview");
  const file = input.files?.[0];
  if (!preview || !file) return;
  updatePhotoPreview(preview, URL.createObjectURL(file));
  stopPhotoStream(field);
  const camera = field?.querySelector(".js-photo-camera");
  if (camera) camera.classList.add("d-none");
});

document.addEventListener("change", (event) => {
  const slot = event.target.closest(".js-slot");
  if (!slot) return;
  const form = slot.closest("form");
  const max = parseInt(form?.dataset?.max || "0", 10);
  if (!max) return;
  const checked = form.querySelectorAll(".js-slot:checked").length;
  if (checked > max) {
    slot.checked = false;
    alert(`Selecione no maximo ${max} horarios por semana.`);
  }
});

const profOptionsCache = new WeakMap();

document.addEventListener("change", (event) => {
  const slotSelect = event.target.closest(".js-slot-select");
  if (!slotSelect) return;
  const container = slotSelect.closest(".border");
  const profSelect = container?.querySelector(".js-prof-select");
  if (!profSelect) return;
  if (!profOptionsCache.has(profSelect)) {
    const options = Array.from(profSelect.options).map((opt) => ({
      value: opt.value,
      text: opt.text,
    }));
    profOptionsCache.set(profSelect, options);
  }
  const allOptions = profOptionsCache.get(profSelect) || [];
  const allowedRaw = slotSelect.selectedOptions[0]?.dataset?.allowedProfs || "";
  const allowed = allowedRaw ? allowedRaw.split(",").filter(Boolean) : null;
  const current = profSelect.value;
  profSelect.innerHTML = "";
  allOptions.forEach((opt) => {
    if (!opt.value) {
      profSelect.add(new Option(opt.text, opt.value));
      return;
    }
    if (!allowed || allowed.includes(opt.value)) {
      profSelect.add(new Option(opt.text, opt.value));
    }
  });
  if (allowed && current && !allowed.includes(current)) {
    profSelect.value = "";
  } else if (current) {
    profSelect.value = current;
  }
});

document.addEventListener("change", (event) => {
  const select = event.target.closest("select[name='recorrencia']");
  if (!select) return;
  const modal = select.closest(".modal");
  const field = modal?.querySelector(".js-recorrencia-quantidade");
  if (!field) return;
  if (select.value === "MENSAL" || select.value === "ANUAL") {
    field.classList.remove("d-none");
  } else {
    field.classList.add("d-none");
    const input = field.querySelector("input");
    if (input) input.value = "";
  }
});

document.addEventListener("change", (event) => {
  const select = event.target.closest(".js-modelo-evolucao");
  if (!select) return;
  const card = select.closest(".evolucao-card");
  const textarea = card?.querySelector(".js-evolucao-text");
  if (!textarea) return;
  const option = select.selectedOptions[0];
  const texto = option?.dataset?.text || "";
  if (texto) {
    textarea.value = texto;
  }
});

document.addEventListener("blur", async (event) => {
  const cepInput = event.target.closest(".js-cep");
  if (!cepInput) return;
  const cep = cepInput.value.replace(/\D/g, "");
  if (cep.length !== 8) return;
  const modal = cepInput.closest(".modal");
  try {
    const resp = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
    const data = await resp.json();
    if (data.erro) return;
    const logradouro = modal.querySelector(".js-logradouro");
    const bairro = modal.querySelector(".js-bairro");
    const cidade = modal.querySelector(".js-cidade");
    if (logradouro) logradouro.value = data.logradouro || "";
    if (bairro) bairro.value = data.bairro || "";
    if (cidade) cidade.value = data.localidade || "";
  } catch (err) {
    return;
  }
}, true);

function handleDropdowns() {
  if (window.innerWidth < 992) {
    document.querySelectorAll(".navbar .dropdown-menu").forEach((menu) => {
      menu.style.display = "";
    });
  }
}

window.addEventListener("resize", handleDropdowns);
handleDropdowns();

document.querySelectorAll(".js-photo-preview").forEach((preview) => {
  const src = preview.getAttribute("src");
  if (src) {
    preview.classList.add("is-visible");
  }
});

function maskCPF(value) {
  const v = value.replace(/\D/g, "").slice(0, 11);
  return v
    .replace(/^(\d{3})(\d)/, "$1.$2")
    .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/\.(\d{3})(\d)/, ".$1-$2");
}

function maskPhone(value) {
  const v = value.replace(/\D/g, "").slice(0, 11);
  if (v.length <= 10) {
    return v
      .replace(/^(\d{2})(\d)/, "($1) $2")
      .replace(/(\d{4})(\d)/, "$1-$2");
  }
  return v
    .replace(/^(\d{2})(\d)/, "($1) $2")
    .replace(/(\d{5})(\d)/, "$1-$2");
}

function maskCEP(value) {
  const v = value.replace(/\D/g, "").slice(0, 8);
  return v.replace(/^(\d{5})(\d)/, "$1-$2");
}

function maskDate(value) {
  const v = value.replace(/\D/g, "").slice(0, 8);
  return v
    .replace(/^(\d{2})(\d)/, "$1/$2")
    .replace(/^(\d{2})\/(\d{2})(\d)/, "$1/$2/$3");
}

function calcFimContrato(inicioIso, duracaoMeses) {
  if (!inicioIso) return "";
  const [y, m, d] = inicioIso.split("-").map((x) => parseInt(x, 10));
  if (!y || !m || !d) return "";
  const totalMonths = m - 1 + duracaoMeses;
  const year = y + Math.floor(totalMonths / 12);
  const month = (totalMonths % 12) + 1;
  const day = Math.min(d, 28);
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function applyFormat(field, cmd, value) {
  const start = field.selectionStart || 0;
  const end = field.selectionEnd || 0;
  const content = field.value || "";
  const selected = content.slice(start, end) || "";
  let before = content.slice(0, start);
  let after = content.slice(end);
  let wrapped = selected;

  if (cmd === "bold") {
    wrapped = `<strong>${selected}</strong>`;
  } else if (cmd === "italic") {
    wrapped = `<em>${selected}</em>`;
  } else if (cmd === "underline") {
    wrapped = `<u>${selected}</u>`;
  } else if (cmd === "align-left") {
    wrapped = `<div style="text-align:left;">${selected || " "}</div>`;
  } else if (cmd === "align-center") {
    wrapped = `<div style="text-align:center;">${selected || " "}</div>`;
  } else if (cmd === "align-right") {
    wrapped = `<div style="text-align:right;">${selected || " "}</div>`;
  } else if (cmd === "align-justify") {
    wrapped = `<div style="text-align:justify;">${selected || " "}</div>`;
  } else if (cmd === "font-family") {
    wrapped = `<span style="font-family:${value};">${selected || " "}</span>`;
  } else if (cmd === "font-size") {
    wrapped = `<span style="font-size:${value};">${selected || " "}</span>`;
  }

  const next = before + wrapped + after;
  field.value = next;
  field.focus();
  const cursor = before.length + wrapped.length;
  field.setSelectionRange(cursor, cursor);
}

function stopPhotoStream(field) {
  const stream = photoStreams.get(field);
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    photoStreams.delete(field);
  }
}

function updatePhotoPreview(preview, src) {
  const old = preview.dataset.blobUrl;
  if (old) URL.revokeObjectURL(old);
  preview.dataset.blobUrl = src;
  preview.src = src;
  preview.classList.add("is-visible");
}

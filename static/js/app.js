document.addEventListener("submit", (event) => {
  const form = event.target;
  if (form) {
    form.querySelectorAll(".js-wysiwyg").forEach((editor) => {
      const targetName = editor.dataset.target;
      const source = form.querySelector(`.js-wysiwyg-source[name="${targetName}"]`);
      if (source) {
        source.value = editor.innerHTML || "";
      }
    });
  }
  const btn = event.target.querySelector("button[type='submit']");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = "Processando...";
  }
});


function getEditorRoot(node) {
  if (!node || !node.closest) return null;
  return node.closest(".modal") || node.closest(".js-variable-root");
}

function getVariableTarget(node) {
  const targetHolder = node?.closest("[data-variable-target]");
  return targetHolder?.dataset.variableTarget || "conteudo_html";
}

function getTargetField(root, targetName) {
  if (!root) return null;
  const wysiwyg = root.querySelector(`.js-wysiwyg[data-target="${targetName}"]`);
  if (wysiwyg) return wysiwyg;
  return root.querySelector(`[name="${targetName}"]`) || root.querySelector("#id_conteudo_html");
}

function getWysiwygSource(root, targetName) {
  if (!root) return null;
  return root.querySelector(`.js-wysiwyg-source[name="${targetName}"]`);
}

function insertTextAtCursor(el, text) {
  el.focus();
  const sel = window.getSelection();
  if (!sel || sel.rangeCount === 0) {
    el.innerHTML = `${el.innerHTML || ""}${text}`;
    return;
  }
  const range = sel.getRangeAt(0);
  range.deleteContents();
  const node = document.createTextNode(text);
  range.insertNode(node);
  range.setStartAfter(node);
  range.setEndAfter(node);
  sel.removeAllRanges();
  sel.addRange(range);
}

function syncWysiwygToSource(root, targetName) {
  const editor = root?.querySelector(`.js-wysiwyg[data-target="${targetName}"]`);
  const source = getWysiwygSource(root, targetName);
  if (editor && source) {
    source.value = editor.innerHTML || "";
  }
}

function insertVariableToken(root, field, key, targetName) {
  if (!field || !key) return;
  const token = `{${key}}`;
  if (field.isContentEditable) {
    insertTextAtCursor(field, token);
    syncWysiwygToSource(root, targetName);
    return;
  }
  const hasFocus = document.activeElement === field;
  const value = field.value || "";
  const start = hasFocus ? (field.selectionStart || 0) : value.length;
  const end = hasFocus ? (field.selectionEnd || start) : value.length;
  field.value = value.slice(0, start) + token + value.slice(end);
  field.focus();
  const cursor = start + token.length;
  field.setSelectionRange(cursor, cursor);
}

document.addEventListener("click", (event) => {
  const btn = event.target.closest(".js-var");
  if (!btn) return;
  event.preventDefault();
  const root = getEditorRoot(btn);
  if (!root) return;
  const key = btn.dataset.var || "";
  const selectedInput = root.querySelector(".js-selected-variable");
  if (selectedInput) {
    selectedInput.value = key;
  }
});

document.addEventListener("dblclick", (event) => {
  const btn = event.target.closest(".js-var");
  if (!btn) return;
  event.preventDefault();
  const root = getEditorRoot(btn);
  if (!root) return;
  const targetName = getVariableTarget(btn);
  const field = getTargetField(root, targetName);
  if (!field) return;
  const key = btn.dataset.var || "";
  const selectedInput = root.querySelector(".js-selected-variable");
  if (selectedInput) {
    selectedInput.value = key;
  }
  insertVariableToken(root, field, key, targetName);
});

document.addEventListener("click", (event) => {
  const btn = event.target.closest(".js-insert-selected");
  if (!btn) return;
  event.preventDefault();
  const root = getEditorRoot(btn);
  if (!root) return;
  const selectedInput = root.querySelector(".js-selected-variable");
  const key = (selectedInput?.value || "").trim();
  if (!key) return;
  const targetName = getVariableTarget(btn);
  const field = getTargetField(root, targetName);
  if (!field) return;
  insertVariableToken(root, field, key, targetName);
});

document.addEventListener("click", (event) => {
  const btn = event.target.closest(".js-format");
  if (!btn) return;
  event.preventDefault();
  const root = getEditorRoot(btn);
  if (!root) return;
  const targetName = getVariableTarget(btn);
  const field = getTargetField(root, targetName);
  if (!field) return;
  const cmd = btn.dataset.cmd || "";
  applyFormat(field, cmd);
  if (field.isContentEditable) {
    syncWysiwygToSource(root, targetName);
  }
});

document.addEventListener("change", (event) => {
  const selectFamily = event.target.closest(".js-font-family");
  const selectSize = event.target.closest(".js-font-size");
  if (!selectFamily && !selectSize) return;
  const root = getEditorRoot(event.target);
  if (!root) return;
  const targetName = getVariableTarget(event.target);
  const field = getTargetField(root, targetName);
  if (!field) return;
  if (selectFamily && selectFamily.value) {
    applyFormat(field, "font-family", selectFamily.value);
    selectFamily.selectedIndex = 0;
  }
  if (selectSize && selectSize.value) {
    applyFormat(field, "font-size", selectSize.value);
    selectSize.selectedIndex = 0;
  }
  if (field.isContentEditable) {
    syncWysiwygToSource(root, targetName);
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

function setContratoDefaults(modal) {
  if (!modal) return;
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
      const duracao = parseInt(selected.dataset.duracao || "0", 10);
      const parcelaAtual = parseFloat(valorParcela.value || "0");
      const totalAtual = parseFloat(valorTotal.value || "0");
      if (!valorParcela.value || parcelaAtual === 0) {
        valorParcela.value = valor ? valor.toFixed(2) : "";
      }
      if (!valorTotal.value || totalAtual === 0) {
        valorTotal.value = valor && duracao ? (valor * duracao).toFixed(2) : "";
      }
    } else {
      valorParcela.value = "";
      valorTotal.value = "";
    }
  }
}

document.addEventListener("shown.bs.modal", (event) => {
  const modal = event.target;
  if (!modal || !modal.querySelector) return;
  modal.querySelectorAll(".js-wysiwyg").forEach((editor) => {
    const targetName = editor.dataset.target;
    const source = modal.querySelector(`.js-wysiwyg-source[name="${targetName}"]`);
    if (source) {
      editor.innerHTML = source.value || "";
    }
  });
  setContratoDefaults(modal);

  const recorrencia = modal.querySelector("select[name='recorrencia']");
  const quantidade = modal.querySelector(".js-recorrencia-quantidade");
  if (recorrencia && quantidade) {
    if (recorrencia.value === "MENSAL" || recorrencia.value === "ANUAL") {
      quantidade.classList.remove("d-none");
    } else {
      quantidade.classList.add("d-none");
    }
  }

  if (modal.querySelector(".js-reserva-date")) {
    initReservaModal(modal);
  }
});

document.addEventListener("input", (event) => {
  const editor = event.target.closest(".js-wysiwyg");
  if (!editor) return;
  const root = getEditorRoot(editor);
  const targetName = editor.dataset.target;
  const source = root?.querySelector(`.js-wysiwyg-source[name="${targetName}"]`);
  if (source) {
    source.value = editor.innerHTML || "";
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

document.addEventListener("change", (event) => {
  const inicio = event.target.closest(".js-contrato-inicio");
  if (!inicio) return;
  const modal = inicio.closest(".modal");
  if (!modal) return;
  const plano = modal.querySelector(".js-plano");
  const fim = modal.querySelector(".js-contrato-fim");
  if (!plano || !fim) return;
  const selected = plano.selectedOptions[0];
  const duracao = parseInt(selected?.dataset?.duracao || "0", 10);
  if (selected && selected.value) {
    fim.value = calcFimContrato(inicio.value, duracao || 1);
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
const slotTimeCache = new WeakMap();

function buildTimeOptions(select) {
  const options = Array.from(select.options)
    .filter((opt) => opt.value)
    .map((opt) => ({
      value: opt.value,
      text: opt.text,
      day: opt.dataset.day || "",
      allowedProfs: opt.dataset.allowedProfs || "",
    }));
  slotTimeCache.set(select, options);
  return options;
}

function renderTimeOptions(select, dayValue) {
  const day = String(dayValue || "");
  const options = slotTimeCache.get(select) || buildTimeOptions(select);
  select.innerHTML = "";
  if (!day) {
    select.add(new Option("Selecione o dia", ""));
    select.disabled = true;
    return;
  }
  const filtered = options.filter((opt) => String(opt.day) === day);
  if (!filtered.length) {
    select.add(new Option("Sem horarios para este dia", ""));
    select.disabled = true;
    return;
  }
  select.add(new Option("Selecione um horario", ""));
  const seen = new Set();
  filtered.forEach((opt) => {
    const key = `${opt.value}::${opt.text}`;
    if (seen.has(key)) return;
    seen.add(key);
    const option = new Option(opt.text, opt.value);
    if (opt.allowedProfs) {
      option.dataset.allowedProfs = opt.allowedProfs;
    }
    select.add(option);
  });
  select.disabled = false;
}

function updateProfOptionsFromTime(timeSelect) {
  const container = timeSelect.closest(".border");
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
  const allowedRaw = timeSelect.selectedOptions[0]?.dataset?.allowedProfs || "";
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
}

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
  const daySelect = event.target.closest(".js-slot-day");
  if (!daySelect) return;
  const container = daySelect.closest(".border");
  const timeSelect = container?.querySelector(".js-slot-time");
  if (!timeSelect) return;
  renderTimeOptions(timeSelect, daySelect.value);
  const profSelect = container.querySelector(".js-prof-select");
  if (profSelect) profSelect.value = "";
});

document.addEventListener("change", (event) => {
  const timeSelect = event.target.closest(".js-slot-time");
  if (!timeSelect) return;
  updateProfOptionsFromTime(timeSelect);
});

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".js-slot-time").forEach((select) => {
    buildTimeOptions(select);
  });
  document.querySelectorAll(".js-slot-day").forEach((select) => {
    if (select.value) {
      const container = select.closest(".border");
      const timeSelect = container?.querySelector(".js-slot-time");
      if (timeSelect) {
        renderTimeOptions(timeSelect, select.value);
      }
    }
  });
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

document.addEventListener("click", (event) => {
  const btnWeek = event.target.closest(".js-hf-select-week");
  const btnAll = event.target.closest(".js-hf-select-all");
  const btnClear = event.target.closest(".js-hf-clear");
  if (!btnWeek && !btnAll && !btnClear) return;
  event.preventDefault();
  const form = event.target.closest("form");
  if (!form) return;
  const select = form.querySelector("select[name='dias'][multiple]");
  if (select) {
    const options = Array.from(select.options);
    if (btnClear) {
      options.forEach((opt) => (opt.selected = false));
      return;
    }
    if (btnAll) {
      options.forEach((opt) => (opt.selected = true));
      return;
    }
    if (btnWeek) {
      options.forEach((opt) => {
        const day = parseInt(opt.value || "0", 10);
        opt.selected = day >= 0 && day <= 4;
      });
    }
    return;
  }
  const checkboxes = Array.from(form.querySelectorAll("input[name='dias']"));
  if (btnClear) {
    checkboxes.forEach((cb) => (cb.checked = false));
    return;
  }
  if (btnAll) {
    checkboxes.forEach((cb) => (cb.checked = true));
    return;
  }
  if (btnWeek) {
    checkboxes.forEach((cb) => {
      const day = parseInt(cb.value || "0", 10);
      cb.checked = day >= 0 && day <= 4;
    });
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

function initReservaModal(modal) {
  const dateInput = modal.querySelector(".js-reserva-date");
  const timeSelect = modal.querySelector(".js-reserva-time");
  const aulaSelect = modal.querySelector("select[name='aulaSessao']");
  const emptyHint = modal.querySelector(".js-reserva-empty");
  const scriptId = modal.dataset.reservaSlots;
  if (!dateInput || !timeSelect || !aulaSelect) return;
  const script = scriptId ? document.getElementById(scriptId) : null;
  let slots = [];
  if (script) {
    try {
      slots = JSON.parse(script.textContent || "[]");
    } catch (err) {
      slots = [];
    }
  }
  if (!Array.isArray(slots) || slots.length === 0) {
    slots = buildSlotsFromSelect(aulaSelect);
  }
  const byDate = new Map();
  slots.forEach((slot) => {
    if (!slot?.date) return;
    if (!byDate.has(slot.date)) byDate.set(slot.date, []);
    byDate.get(slot.date).push(slot);
  });
  byDate.forEach((items) => {
    items.sort((a, b) => (a.time_start || "").localeCompare(b.time_start || ""));
  });

  const setEmpty = (isEmpty) => {
    if (isEmpty) {
      timeSelect.innerHTML = '<option value="">Sem horarios disponiveis</option>';
      timeSelect.disabled = true;
      if (emptyHint) emptyHint.classList.remove("d-none");
    } else {
      timeSelect.disabled = false;
      if (emptyHint) emptyHint.classList.add("d-none");
    }
  };

  const renderTimes = (dateValue, selectedId) => {
    const normalizedDate = normalizeDateValue(dateValue);
    if (normalizedDate && normalizedDate !== dateValue) {
      dateInput.value = normalizedDate;
    }
    const items = byDate.get(normalizedDate || dateValue) || [];
    if (!items.length) {
      setEmpty(true);
      return;
    }
    setEmpty(false);
    timeSelect.innerHTML = '<option value="">Selecione um horario</option>';
    items.forEach((slot) => {
      const opt = new Option(slot.label || slot.time_start || "", String(slot.id));
      timeSelect.add(opt);
    });
    if (selectedId) {
      timeSelect.value = String(selectedId);
    } else {
      timeSelect.selectedIndex = 0;
    }
  };

  const currentId = aulaSelect.value;
  const currentSlot = slots.find((slot) => String(slot.id) === String(currentId));
  if (currentSlot?.date) {
    dateInput.value = normalizeDateValue(currentSlot.date) || currentSlot.date;
  } else if (!dateInput.value && slots.length) {
    dateInput.value = normalizeDateValue(slots[0].date) || slots[0].date;
  }
  renderTimes(dateInput.value, currentId);

  dateInput.addEventListener("change", () => {
    renderTimes(dateInput.value, null);
    aulaSelect.value = "";
  });

  timeSelect.addEventListener("change", () => {
    aulaSelect.value = timeSelect.value;
  });
}

function buildSlotsFromSelect(select) {
  const slots = [];
  Array.from(select.options).forEach((opt) => {
    const value = opt.value;
    if (!value) return;
    const text = (opt.text || "").trim();
    const matchIso = text.match(/(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})/);
    const matchBr = text.match(/(\d{2}\/\d{2}\/\d{4})\s+(\d{2}:\d{2})/);
    const match = matchIso || matchBr;
    if (!match) return;
    const date = normalizeDateValue(match[1]) || match[1];
    const time = match[2];
    slots.push({
      id: value,
      date,
      time_start: time,
      label: text,
    });
  });
  return slots;
}

function normalizeDateValue(value) {
  if (!value) return "";
  const raw = String(value).trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw;
  const br = raw.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!br) return raw;
  return `${br[3]}-${br[2]}-${br[1]}`;
}

window.addEventListener("resize", handleDropdowns);
handleDropdowns();

document.querySelectorAll(".js-photo-preview").forEach((preview) => {
  const src = preview.getAttribute("src");
  if (src) {
    preview.classList.add("is-visible");
  }
});

document.addEventListener("DOMContentLoaded", () => {
  function selectVariable(btn) {
    const root = getEditorRoot(btn);
    if (!root) return;
    const key = btn.dataset.var || "";
    const selectedInput = root.querySelector(".js-selected-variable");
    if (selectedInput) selectedInput.value = key;
  }

  function insertSelected(btn) {
    const root = getEditorRoot(btn);
    if (!root) return;
    const selectedInput = root.querySelector(".js-selected-variable");
    const key = (selectedInput?.value || "").trim();
    if (!key) return;
    const targetName = getVariableTarget(btn);
    const field = getTargetField(root, targetName);
    if (!field) return;
    insertVariableToken(root, field, key, targetName);
  }

  document.querySelectorAll(".js-variable-root .js-var").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      event.preventDefault();
      selectVariable(btn);
      const now = Date.now();
      const last = Number(btn.dataset.lastClickAt || "0");
      btn.dataset.lastClickAt = String(now);
      if (now - last <= 500) {
        const root = getEditorRoot(btn);
        if (!root) return;
        const targetName = getVariableTarget(btn);
        const field = getTargetField(root, targetName);
        if (!field) return;
        insertVariableToken(root, field, btn.dataset.var || "", targetName);
      }
    });
    btn.addEventListener("dblclick", (event) => {
      event.preventDefault();
      selectVariable(btn);
      const root = getEditorRoot(btn);
      if (!root) return;
      const targetName = getVariableTarget(btn);
      const field = getTargetField(root, targetName);
      if (!field) return;
      insertVariableToken(root, field, btn.dataset.var || "", targetName);
    });
  });

  document.querySelectorAll(".js-variable-root .js-insert-selected").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      event.preventDefault();
      insertSelected(btn);
    });
  });

  document.querySelectorAll(".js-variable-root .js-wysiwyg").forEach((editor) => {
    const targetName = editor.dataset.target;
    const root = getEditorRoot(editor);
    const source = root?.querySelector(`.js-wysiwyg-source[name="${targetName}"]`);
    if (source) {
      editor.innerHTML = source.value || "";
    }
  });

  const params = new URLSearchParams(window.location.search || "");
  const tab = params.get("tab");
  if (!tab) return;
  const trigger = document.querySelector(`[data-bs-target="#tab-${tab}"]`);
  if (!trigger || typeof bootstrap === "undefined") return;
  const instance = bootstrap.Tab.getOrCreateInstance(trigger);
  instance.show();
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
  if (field.isContentEditable) {
    field.focus();
    if (cmd === "bold") {
      document.execCommand("bold");
    } else if (cmd === "italic") {
      document.execCommand("italic");
    } else if (cmd === "underline") {
      document.execCommand("underline");
    } else if (cmd === "align-left") {
      document.execCommand("justifyLeft");
    } else if (cmd === "align-center") {
      document.execCommand("justifyCenter");
    } else if (cmd === "align-right") {
      document.execCommand("justifyRight");
    } else if (cmd === "align-justify") {
      document.execCommand("justifyFull");
    } else if (cmd === "font-family") {
      document.execCommand("fontName", false, value);
    } else if (cmd === "font-size") {
      const px = parseInt((value || "").replace("px", ""), 10);
      const sizeMap = { 12: "2", 14: "3", 16: "4", 18: "5", 20: "6" };
      const fontSize = sizeMap[px] || "3";
      document.execCommand("fontSize", false, fontSize);
    }
    return;
  }
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

// Aulas - painel operacional
function initAulasOperacao() {
  const root = document.querySelector("[data-operacao-root]");
  if (!root) return;

  const url = root.dataset.operacaoUrl || "";
  const evolucaoTemplate = root.dataset.evolucaoUrlTemplate || "";
  const avaliacaoTemplate = root.dataset.avaliacaoUrlTemplate || "";
  const cobrancaTemplate = root.dataset.cobrancaUrlTemplate || "";
  const historicoTemplate = root.dataset.historicoUrlTemplate || "";
  const statusTemplate = root.dataset.statusUrlTemplate || "";

  const searchInput = root.querySelector(".js-operacao-search");
  const dateInput = root.querySelector(".js-operacao-date");
  const unidadeSelect = root.querySelector(".js-operacao-unidade");
  const profissionalSelect = root.querySelector(".js-operacao-profissional");
  const periodButtons = root.querySelectorAll(".js-period");
  const statusButtons = root.querySelectorAll(".js-status");
  const loading = root.querySelector(".js-operacao-loading");
  const content = root.querySelector(".js-operacao-content");

  const drawer = root.querySelector(".js-aulas-drawer");
  const drawerClose = root.querySelector(".js-close-drawer");
  const drawerName = root.querySelector(".js-drawer-name");
  const drawerMeta = root.querySelector(".js-drawer-meta");
  const drawerStatus = root.querySelector(".js-drawer-status");
  const drawerAvatar = root.querySelector(".js-drawer-avatar");
  const drawerFicha = root.querySelector(".js-ficha-link");
  const drawerConfirmacao = root.querySelector(".js-drawer-confirmacao");
  const drawerPreliminares = root.querySelector(".js-drawer-preliminares");
  const drawerPreliminaresCta = root.querySelector(".js-drawer-preliminares-cta");
  const drawerCobranca = root.querySelector(".js-drawer-cobranca");
  const evolucaoText = root.querySelector(".js-evolucao-text");
  const evolucaoList = root.querySelector(".js-evolucao-list");
  const avaliacaoText = root.querySelector(".js-avaliacao-text");
  const avaliacaoList = root.querySelector(".js-avaliacao-list");
  const cobrancaList = root.querySelector(".js-cobranca-list");
  const historicoList = root.querySelector(".js-historico-list");
  const remarcarTemplate = root.dataset.remarcarUrlTemplate || "";
  const remarcarModalEl = document.getElementById("remarcarModal");
  const remarcarDate = remarcarModalEl?.querySelector(".js-remarcar-date");
  const remarcarTime = remarcarModalEl?.querySelector(".js-remarcar-time");
  const remarcarProf = remarcarModalEl?.querySelector(".js-remarcar-profissional");
  const remarcarSave = remarcarModalEl?.querySelector(".js-remarcar-save");

  let selected = null;
  let selectedId = null;
  let items = [];
  let debounceTimer = null;
  let selectedStatus = "";
  let selectedPeriod = "hoje";

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }


  function statusBadgeClass(status) {
    if (status === "em_aula") return "aulas-badge is-live";
    if (status === "finalizada") return "aulas-badge is-done";
    if (status === "faltou" || status === "remarcada") return "aulas-badge is-miss";
    return "aulas-badge is-pending";
  }

  function statusThemeClass(status) {
    if (status === "em_aula") return "is-em_aula";
    if (status === "finalizada") return "is-finalizada";
    if (status === "faltou") return "is-faltou";
    if (status === "remarcada") return "is-remarcada";
    return "is-aguardando_chegar";
  }

  function applyStatusTheme(target, status) {
    if (!target) return;
    const classes = [
      "is-aguardando_chegar",
      "is-em_aula",
      "is-finalizada",
      "is-faltou",
      "is-remarcada",
    ];
    target.classList.remove(...classes);
    target.classList.add(statusThemeClass(status));
  }

  function applyActionButtons(status) {
    const actionMap = {
      aguardando_chegar: "chegou",
      em_aula: "chegou",
      finalizada: "finalizar",
      faltou: "faltou",
      remarcada: "remarcar",
    };
    root.querySelectorAll(".js-drawer-action").forEach((btn) => {
      btn.classList.remove("is-active");
      if (btn.dataset.action === actionMap[status]) {
        btn.classList.add("is-active");
      }
    });
  }

  function formatTime(iso) {
    const date = new Date(iso);
    return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  }

  function formatDayLabel(iso) {
    const date = new Date(iso);
    return date.toLocaleDateString("pt-BR", {
      weekday: "short",
      day: "2-digit",
      month: "2-digit"
    });
  }

  function isoDateKey(iso) {
    return new Date(iso).toISOString().slice(0, 10);
  }

  function formatPhone(raw) {
    if (!raw) return "";
    const digits = String(raw).replace(/\D/g, "");
    return digits.startsWith("55") ? digits : `55${digits}`;
  }

  function render() {
    if (!content) return;
    content.innerHTML = "";
    if (!items.length) {
      content.innerHTML = '<div class="agenda-empty">Sem aulas para o filtro.</div>';
      return;
    }
    const renderRows = (list, dateLabel = "") => {
      const grouped = {};
      list.forEach((item) => {
        const key = formatTime(item.dt_inicio);
        if (!grouped[key]) grouped[key] = [];
        grouped[key].push(item);
      });
      const times = Object.keys(grouped).sort((a, b) => a.localeCompare(b));
      times.forEach((time) => {
        const row = document.createElement("div");
        row.className = "aulas-time-row";
        const label = document.createElement("div");
        label.className = "aulas-time-label";
        label.innerHTML = `
          <div class="aulas-time-label__time">${time}</div>
          ${dateLabel ? `<div class="aulas-time-label__date">${dateLabel}</div>` : ""}
          <div class="aulas-time-label__count">${grouped[time].length} aluno(s)</div>
        `;
        const cards = document.createElement("div");
        cards.className = "aulas-cards";
        grouped[time].forEach((item) => {
          const card = document.createElement("div");
          card.className = `aulas-card ${statusThemeClass(item.status_aula)}`;
          const indicators = [];
          indicators.push(item.confirmacao ? "Confirmado" : "Nao confirmado");
          if (!item.flags.tem_preliminares) indicators.push("Preliminares pendentes");
          if (item.flags.cobranca_pendente) indicators.push("Cobranca pendente");
          card.innerHTML = `
            <div class="aulas-card__header">
              <div>
                <div class="aulas-card__meta">${formatTime(item.dt_inicio)}  ${item.unidade || "Unidade"}</div>
                <div class="aulas-card__title">${item.aluno.nome}</div>
                <div class="aulas-card__meta">${item.plano.descricao || "Plano nao informado"}</div>
              </div>
              <span class="${statusBadgeClass(item.status_aula)}">${item.status_aula.replace("_", " ")}</span>
            </div>
            <div class="aulas-card__meta">Sala: ${item.sala || "Sala principal"}</div>
            <div class="aulas-card__meta">Profissional: ${item.profissional.nome || "-"}</div>
            <div class="aulas-indicators">
              ${indicators.map((label) => `<span class="aulas-indicator">${label}</span>`).join("")}
            </div>
            <div class="aulas-quick-actions">
              <button data-action="chegou">Chegou</button>
              <button data-action="evolucao">Evolucao</button>
              <button data-action="whatsapp">WhatsApp</button>
            </div>
          `;
          card.addEventListener("click", () => openDrawer(item));
          card.querySelectorAll("button[data-action]").forEach((btn) => {
            btn.addEventListener("click", (event) => {
              event.stopPropagation();
              const action = btn.dataset.action;
              if (action === "whatsapp") {
                const phone = formatPhone(item.aluno.telefone);
                if (phone) window.open(`https://wa.me/${phone}`, "_blank");
                return;
              }
              if (action === "evolucao") {
                openDrawer(item);
                return;
              }
              if (action === "chegou") {
                updateStatus(item, "chegou");
              }
            });
          });
          cards.appendChild(card);
        });
        row.appendChild(label);
        row.appendChild(cards);
        content.appendChild(row);
      });
    };

    if (selectedPeriod === "semana") {
      const byDate = {};
      items.forEach((item) => {
        const key = isoDateKey(item.dt_inicio);
        if (!byDate[key]) byDate[key] = [];
        byDate[key].push(item);
      });
      const dates = Object.keys(byDate).sort((a, b) => a.localeCompare(b));
      dates.forEach((key) => {
        const section = document.createElement("div");
        section.className = "aulas-date-block";
        const title = document.createElement("div");
        title.className = "aulas-date-title";
        title.textContent = formatDayLabel(byDate[key][0].dt_inicio);
        section.appendChild(title);
        content.appendChild(section);
        renderRows(byDate[key], formatDayLabel(byDate[key][0].dt_inicio));
      });
      return;
    }

    if (items.length) {
      renderRows(items, formatDayLabel(items[0].dt_inicio));
    }
  }

  function openDrawer(item) {
    selected = item;
    selectedId = item.id;
    if (!drawer) return;
    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
    applyStatusTheme(drawer, item.status_aula);
    if (drawerName) drawerName.textContent = item.aluno.nome;
    if (drawerMeta) drawerMeta.textContent = `${formatTime(item.dt_inicio)}  ${item.sala || "Sala principal"}`;
    if (drawerStatus) {
      drawerStatus.textContent = item.status_aula.replace("_", " ");
      drawerStatus.className = `${statusBadgeClass(item.status_aula)} js-drawer-status`;
    }
    if (drawerAvatar) {
      const initials = (item.aluno.nome || "A")
        .split(" ")
        .filter(Boolean)
        .slice(0, 2)
        .map((chunk) => chunk[0].toUpperCase())
        .join("");
      drawerAvatar.textContent = initials || "A";
    }
    if (drawerFicha) {
      if (item.aluno.ficha_url) {
        drawerFicha.href = item.aluno.ficha_url;
        drawerFicha.classList.remove("d-none");
      } else {
        drawerFicha.classList.add("d-none");
      }
    }
    if (drawerConfirmacao) drawerConfirmacao.textContent = item.confirmacao ? "Confirmado" : "Nao confirmado";
    if (drawerPreliminares) drawerPreliminares.textContent = item.flags.tem_preliminares ? "OK" : "Pendente";
    if (drawerPreliminaresCta) {
      drawerPreliminaresCta.classList.toggle("d-none", item.flags.tem_preliminares);
    }
    if (drawerCobranca) {
      drawerCobranca.textContent = item.flags.cobranca_pendente ? "Ha cobrancas pendentes." : "Sem cobrancas pendentes.";
    }
    if (evolucaoText) evolucaoText.value = item.ultima_evolucao?.texto || "";
    if (avaliacaoText) avaliacaoText.value = "";
    applyActionButtons(item.status_aula);
    loadEvolucoes();
    loadAvaliacoes();
    loadCobranca();
    loadHistorico();
  }

  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove("is-open");
    drawer.setAttribute("aria-hidden", "true");
    selected = null;
    selectedId = null;
  }

  function updateStatus(item, action) {
    const csrf = getCookie("csrftoken");
    const urlAction = statusTemplate.replace("/0/", `/${item.id}/`);
    fetch(urlAction, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf
      },
      body: JSON.stringify({ acao: action })
    }).then(() => {
      const actionMap = {
        chegou: "em_aula",
        iniciar: "em_aula",
        finalizar: "finalizada",
        faltou: "faltou",
        remarcar: "remarcada",
      };
      if (actionMap[action]) {
        item.status_aula = actionMap[action];
        applyStatusTheme(drawer, item.status_aula);
        if (drawerStatus) {
          drawerStatus.textContent = item.status_aula.replace("_", " ");
          drawerStatus.className = `${statusBadgeClass(item.status_aula)} js-drawer-status`;
        }
        applyActionButtons(item.status_aula);
      }
      loadData();
    });
  }

  function saveEvolucao(finalizar) {
    if (!selected || !evolucaoText) return;
    const text = evolucaoText.value.trim();
    if (!text) return;
    const csrf = getCookie("csrftoken");
    const urlAction = evolucaoTemplate.replace("/0/", `/${selected.id}/`);
    fetch(urlAction, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf
      },
      body: JSON.stringify({ texto: text, profissional_id: selected.profissional?.id, finalizar: finalizar })
    }).then(() => {
      evolucaoText.value = "";
      loadEvolucoes();
      loadData();
    });
  }

  function saveAvaliacao() {
    if (!selected || !avaliacaoText) return;
    const text = avaliacaoText.value.trim();
    if (!text) return;
    const csrf = getCookie("csrftoken");
    const urlAction = avaliacaoTemplate.replace("/0/", `/${selected.id}/`);
    const editId = avaliacaoText.dataset.editId || "";
    fetch(urlAction, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf
      },
      body: JSON.stringify({
        texto: text,
        profissional_id: selected.profissional?.id,
        acao: editId ? "update" : "create",
        avaliacao_id: editId ? parseInt(editId, 10) : null,
      })
    }).then(async (resp) => {
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        alert(data.error || "Nao foi possivel salvar a avaliacao.");
        return;
      }
      avaliacaoText.value = "";
      avaliacaoText.dataset.editId = "";
      if (saveAvaliacaoBtn) saveAvaliacaoBtn.textContent = "Salvar avaliacao";
      loadAvaliacoes();
    });
  }

  function renderList(container, items, type) {
    if (!container) return;
    if (!items.length) {
      container.innerHTML = '<div class="aulas-empty">Sem registros.</div>';
      return;
    }
    container.innerHTML = items
      .map((item) => {
        if (type === "evolucao") {
          return `
            <div class="aulas-note">
              <div class="aulas-note__meta">${item.dt_evolucao ? new Date(item.dt_evolucao).toLocaleString("pt-BR") : ""} ${item.profissional ? "- " + item.profissional : ""}</div>
              <div class="aulas-note__text">${item.texto}</div>
            </div>
          `;
        }
        if (type === "avaliacao") {
          return `
            <div class="aulas-note">
              <div class="aulas-note__meta">${item.dt_avaliacao ? new Date(item.dt_avaliacao).toLocaleString("pt-BR") : ""} ${item.profissional ? "- " + item.profissional : ""}</div>
              <div class="aulas-note__text">${item.texto}</div>
              <div class="aulas-quick-actions">
                <button class="btn btn-sm btn-outline-secondary js-avaliacao-edit" data-id="${item.id}">Editar</button>
                <button class="btn btn-sm btn-outline-danger js-avaliacao-delete" data-id="${item.id}">Excluir</button>
              </div>
            </div>
          `;
        }
        if (type === "historico") {
          const statusLabel = item.status ? item.status.replace("_", " ") : "";
          return `
            <div class="aulas-note">
              <div class="aulas-note__meta">${item.data || ""} - ${item.hora_inicio || ""}-${item.hora_fim || ""}</div>
              <div class="aulas-note__text">${item.servico || "Servico"} ${item.profissional ? "- " + item.profissional : ""}</div>
              <div class="aulas-note__meta">${item.unidade || ""} - ${statusLabel}</div>
            </div>
          `;
        }
        return "";
      })
      .join("");
    if (type === "avaliacao") {
      container.querySelectorAll(".js-avaliacao-edit").forEach((btn) => {
        btn.addEventListener("click", () => {
          const note = btn.closest(".aulas-note");
          const textEl = note?.querySelector(".aulas-note__text");
          if (!avaliacaoText || !textEl) return;
          avaliacaoText.value = textEl.textContent.trim();
          avaliacaoText.dataset.editId = btn.dataset.id || "";
          if (saveAvaliacaoBtn) saveAvaliacaoBtn.textContent = "Atualizar avaliacao";
          avaliacaoText.focus();
        });
      });
      container.querySelectorAll(".js-avaliacao-delete").forEach((btn) => {
        btn.addEventListener("click", () => {
          if (!selected) return;
          if (!confirm("Excluir avaliacao?")) return;
          const csrf = getCookie("csrftoken");
          const urlAction = avaliacaoTemplate.replace("/0/", `/${selected.id}/`);
          fetch(urlAction, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrf
            },
            body: JSON.stringify({ acao: "delete", avaliacao_id: parseInt(btn.dataset.id || "0", 10) })
          }).then(() => loadAvaliacoes());
        });
      });
    }
  }

  function renderCobranca(container, items) {
    if (!container) return;
    if (!items.length) {
      container.innerHTML = '<div class="aulas-empty">Sem cobrancas.</div>';
      return;
    }
    container.innerHTML = items
      .map((item) => {
        const venc = item.dt_vencimento ? new Date(item.dt_vencimento).toLocaleDateString("pt-BR") : "-";
        return `
          <div class="aulas-cobranca">
            <div>
              <div class="aulas-note__text">Contrato ${item.contrato || "-"}</div>
              <div class="aulas-note__meta">Vencimento ${venc} - ${item.status} - R$ ${item.valor}</div>
            </div>
            <div class="aulas-cobranca__actions">
              ${item.status !== "PAGO" ? `<button class="btn btn-sm btn-outline-success js-cobranca-acao" data-acao="baixar" data-url="${item.baixar_url}">Dar baixa</button>` : ""}
              <a class="btn btn-sm btn-outline-secondary" href="${item.recibo_url}" target="_blank" rel="noopener noreferrer">Recibo</a>
              <button class="btn btn-sm btn-outline-danger js-cobranca-acao" data-acao="excluir" data-url="${item.excluir_url}">Excluir</button>
            </div>
          </div>
        `;
      })
      .join("");
    container.querySelectorAll(".js-cobranca-acao").forEach((btn) => {
      btn.addEventListener("click", () => {
        const urlTarget = btn.dataset.url;
        if (!urlTarget) return;
        const csrf = getCookie("csrftoken");
        fetch(urlTarget, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrf
          },
        }).then(() => loadCobranca());
      });
    });
  }

  function loadEvolucoes() {
    if (!selected || !evolucaoTemplate) return;
    const urlAction = evolucaoTemplate.replace("/0/", `/${selected.id}/`);
    fetch(urlAction)
      .then((resp) => resp.json())
      .then((data) => renderList(evolucaoList, data.items || [], "evolucao"));
  }

  function loadAvaliacoes() {
    if (!selected || !avaliacaoTemplate) return;
    const urlAction = avaliacaoTemplate.replace("/0/", `/${selected.id}/`);
    fetch(urlAction)
      .then((resp) => resp.json())
      .then((data) => renderList(avaliacaoList, data.items || [], "avaliacao"));
  }

  function loadCobranca() {
    if (!selected || !cobrancaTemplate) return;
    const urlAction = cobrancaTemplate.replace("/0/", `/${selected.id}/`);
    fetch(urlAction)
      .then((resp) => resp.json())
      .then((data) => renderCobranca(cobrancaList, data.items || []));
  }

  function openRemarcarModal() {
    if (!selected || !remarcarModalEl || !remarcarDate || !remarcarTime) return;
    const start = new Date(selected.dt_inicio);
    const dateValue = start.toISOString().slice(0, 10);
    const timeValue = start.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    remarcarDate.value = dateValue;
    remarcarTime.value = timeValue;
    if (remarcarProf) remarcarProf.value = "";
    const modal = bootstrap.Modal.getOrCreateInstance(remarcarModalEl);
    modal.show();
  }

  function saveRemarcar() {
    if (!selected || !remarcarTemplate || !remarcarDate || !remarcarTime) return;
    const data = remarcarDate.value;
    const hora = remarcarTime.value;
    if (!data || !hora) {
      alert("Informe data e hora.");
      return;
    }
    const profissionalId = remarcarProf?.value || "";
    const csrf = getCookie("csrftoken");
    const urlAction = remarcarTemplate.replace("/0/", `/${selected.id}/`);
    fetch(urlAction, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf
      },
      body: JSON.stringify({ data: data, hora_inicio: hora, profissional_id: profissionalId || null })
    }).then(async (resp) => {
      if (!resp.ok) {
        const payload = await resp.json().catch(() => ({}));
        alert(payload.error || "Nao foi possivel remarcar.");
        return;
      }
      const modal = bootstrap.Modal.getInstance(remarcarModalEl);
      if (modal) modal.hide();
      loadData();
    });
  }

  function loadHistorico() {
    if (!selected || !historicoTemplate) return;
    const urlAction = historicoTemplate.replace("/0/", `/${selected.id}/`);
    fetch(urlAction)
      .then((resp) => resp.json())
      .then((data) => renderList(historicoList, data.items || [], "historico"));
  }

  function loadData() {
    if (!url) return;
    if (loading) loading.style.display = "grid";
    if (content) content.innerHTML = "";
    const params = new URLSearchParams();
    params.set("data", dateInput?.value || "");
    params.set("periodo", selectedPeriod);
    if (unidadeSelect?.value) params.set("unidade_id", unidadeSelect.value);
    if (profissionalSelect?.value) params.set("profissional_id", profissionalSelect.value);
    if (selectedStatus) params.set("status_aula", selectedStatus);
    if (searchInput?.value) params.set("q", searchInput.value);
    fetch(`${url}?${params.toString()}`)
      .then((resp) => resp.json())
      .then((data) => {
        items = data.items || [];
        render();
        if (selectedId) {
          const found = items.find((item) => item.id === selectedId);
          if (found) openDrawer(found);
        }
      })
      .finally(() => {
        if (loading) loading.style.display = "none";
      });
  }

  periodButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      periodButtons.forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      selectedPeriod = btn.dataset.value || "hoje";
      loadData();
    });
  });

  statusButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const value = btn.dataset.value || "";
      if (selectedStatus === value) {
        selectedStatus = "";
        btn.classList.remove("is-active");
      } else {
        statusButtons.forEach((b) => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        selectedStatus = value;
      }
      loadData();
    });
  });

  [dateInput, unidadeSelect, profissionalSelect].forEach((el) => {
    if (!el) return;
    el.addEventListener("change", loadData);
  });

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(loadData, 350);
    });
  }


  if (drawerClose) drawerClose.addEventListener("click", closeDrawer);

  root.querySelectorAll(".js-drawer-action").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!selected) return;
      if (btn.dataset.action === "remarcar") {
        openRemarcarModal();
        return;
      }
      updateStatus(selected, btn.dataset.action || "");
    });
  });

  const saveBtn = root.querySelector(".js-evolucao-save");
  const saveFinalBtn = root.querySelector(".js-evolucao-save-final");
  const saveAvaliacaoBtn = root.querySelector(".js-avaliacao-save");
  if (saveBtn) saveBtn.addEventListener("click", () => saveEvolucao(false));
  if (saveFinalBtn) saveFinalBtn.addEventListener("click", () => saveEvolucao(true));
  if (saveAvaliacaoBtn) saveAvaliacaoBtn.addEventListener("click", saveAvaliacao);
  if (remarcarSave) remarcarSave.addEventListener("click", saveRemarcar);

  root.querySelectorAll(".js-evolucao-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!evolucaoText) return;
      evolucaoText.value = `${evolucaoText.value}${evolucaoText.value ? "\n" : ""}${btn.textContent}: `;
      evolucaoText.focus();
    });
  });

  root.querySelectorAll(".js-whatsapp").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      event.preventDefault();
      if (!selected) return;
      const phone = formatPhone(selected.aluno.telefone);
      if (phone) window.open(`https://wa.me/${phone}`, "_blank");
    });
  });

  root.querySelectorAll(".aulas-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      root.querySelectorAll(".aulas-tab").forEach((tab) => tab.classList.remove("is-active"));
      btn.classList.add("is-active");
      const target = btn.dataset.tab;
      root.querySelectorAll(".aulas-drawer__panel").forEach((panel) => {
        if (panel.dataset.panel === target) {
          panel.classList.remove("d-none");
        } else {
          panel.classList.add("d-none");
        }
      });
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && searchInput) {
      event.preventDefault();
      searchInput.focus();
    }
    if (event.key === "Enter" && !selected && items.length > 0) {
      openDrawer(items[0]);
    }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
      if (selected) {
        event.preventDefault();
        saveEvolucao(false);
      }
    }
  });

  loadData();
}

document.addEventListener("DOMContentLoaded", initAulasOperacao);

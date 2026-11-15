"use strict";
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const state = {
  csrf: "",
  project: "",
  snapshot: null,
  catalog: null,
  capabilities: null,
  view: "overview",
  busy: false,
};
const priorityNames = {
  "review-first": "Revisar primeiro",
  "review-next": "Revisar depois",
  context: "Contexto",
};
const decisionNames = {
  open: "Aberto",
  "in-review": "Em análise",
  "follow-up": "Acompanhar",
  dismissed: "Descartado",
};
const roleNames = {
  "nmap-before": "Nmap · anterior",
  "nmap-after": "Nmap · atual",
  trivy: "Trivy · JSON v2",
  zap: "ZAP · Traditional JSON",
};
function el(tag, className, content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined) node.textContent = content;
  return node;
}
function btn(label, action, className = "text-button") {
  const node = el("button", className, label);
  node.type = "button";
  node.addEventListener("click", action);
  return node;
}
function pre(value) {
  return el("pre", "", JSON.stringify(value, null, 2));
}
function empty(title, description) {
  const node = el("div", "empty");
  node.append(el("strong", "", title), el("span", "", description));
  return node;
}
function date(value) {
  return new Date(value).toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}
let toastTimeout;
function toast(message, error = false) {
  clearTimeout(toastTimeout);
  const node = $("#toast");
  node.textContent = message;
  node.className = "toast" + (error ? " error" : "");
  node.hidden = false;
  toastTimeout = setTimeout(() => (node.hidden = true), 6500);
}
async function api(path, method = "GET", body) {
  const response = await fetch(path, {
    method,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": state.csrf },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.error || "Não foi possível concluir a operação");
  return data;
}
function projectPath(action = "") {
  if (!state.project) throw new Error("Crie ou selecione um projeto primeiro");
  return "/api/projects/" + state.project + (action ? "/" + action : "");
}
function requireProject() {
  if (state.project) return true;
  newProject();
  return false;
}
async function task(button, work) {
  if (button.disabled) return;
  button.disabled = true;
  const original = button.textContent;
  button.textContent = "Processando…";
  try {
    await work();
  } catch (error) {
    toast(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}
function modal(title, content) {
  $("#modal-title").textContent = title;
  $("#modal-body").replaceChildren(content);
  if (!$("#modal").open) $("#modal").showModal();
}
function closeModal() {
  $("#modal").close();
}
function formField(label, type, name, value = "") {
  const wrapper = el("label", "", label);
  const input = document.createElement(
    type === "textarea" ? "textarea" : "input",
  );
  if (type !== "textarea") input.type = type;
  input.name = name;
  input.value = value;
  input.required = true;
  wrapper.append(input);
  return [wrapper, input];
}
function newProject() {
  const form = el("form", "modal-form");
  const [field, input] = formField("Nome do projeto", "text", "name");
  input.maxLength = 100;
  const submit = el("button", "primary", "Criar projeto");
  submit.type = "submit";
  const error = el("p", "modal-error");
  form.append(field, submit, error);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    submit.disabled = true;
    try {
      const project = await api("/api/projects", "POST", { name: input.value });
      await loadProjects(project.id);
      closeModal();
      toast("Projeto criado. Importe relatórios para começar.");
    } catch (e) {
      error.textContent = e.message;
    } finally {
      submit.disabled = false;
    }
  });
  modal("Um espaço para sua próxima ideia", form);
  input.focus();
}
async function loadProjects(selected = state.project) {
  const projects = await api("/api/projects");
  const select = $("#project-select");
  select.replaceChildren(el("option", "", "Selecione um projeto"));
  select.firstChild.value = "";
  projects.forEach((project) => {
    const option = el("option", "", project.name);
    option.value = project.id;
    select.append(option);
  });
  state.project = projects.some((p) => p.id === selected)
    ? selected
    : projects[0]?.id || "";
  select.value = state.project;
  await refresh();
}
let refreshSequence = 0;
async function refresh() {
  const sequence = ++refreshSequence;
  const project = state.project;
  const snapshot = project ? await api("/api/projects/" + project) : null;
  if (sequence !== refreshSequence || project !== state.project) return false;
  state.snapshot = snapshot;
  render();
  return true;
}
function latestDocument() {
  return state.snapshot?.review?.document || null;
}
function currentDecision(item) {
  const review = state.snapshot?.review;
  return state.snapshot?.decisions
    .filter((d) => d.review === review?.id && d.item === item.id)
    .at(-1);
}
function render() {
  const snapshot = state.snapshot,
    report = latestDocument();
  $("#project-title").textContent =
    snapshot?.project.name || "Comece uma investigação";
  $("#stat-sources").textContent = snapshot?.sources.length || 0;
  $("#stat-first").textContent =
    report?.summary.by_priority["review-first"] || 0;
  $("#stat-items").textContent = report?.items.length || 0;
  $("#nav-count").textContent = report?.items.length || 0;
  $("#stat-decisions").textContent = snapshot
    ? new Set(
        snapshot.decisions
          .filter((d) => d.review === snapshot.review?.id)
          .map((d) => d.item),
      ).size
    : 0;
  $("#stale").hidden = !snapshot?.review_stale;
  $("#delete-project").disabled = !snapshot;
  renderQueue();
  renderSources();
  renderMessages();
  renderActivity();
  renderStudio();
}
function showView(view) {
  state.view = view;
  $$(".view").forEach((node) => (node.hidden = node.id !== "view-" + view));
  $$(".nav").forEach((node) => {
    const selected = node.dataset.view === view;
    node.classList.toggle("active", selected);
    if (selected) node.setAttribute("aria-current", "page");
    else node.removeAttribute("aria-current");
  });
  const chat = $("#chat-panel");
  if (view === "chat") {
    $("#chat-destination").append(chat);
    chat.classList.remove("open");
  } else if ($("#chat-destination").contains(chat)) {
    $(".workarea").append(chat);
  }
  window.scrollTo({ top: 0, behavior: "instant" });
}
function queueCard(item, compact = false) {
  const card = el("article", "queue-item");
  card.id = (compact ? "preview-" : "") + item.id;
  const meta = el("div", "item-meta");
  meta.append(
    el("span", "pill " + item.priority, priorityNames[item.priority]),
    el("span", "rule-name", item.rule_id),
  );
  const decision = currentDecision(item);
  if (decision)
    meta.append(el("span", "decision-state", decisionNames[decision.state]));
  card.append(meta, el("h3", "", item.title), el("p", "", item.reason));
  const actions = el("div", "item-actions");
  if (compact) {
    actions.append(btn("Abrir evidências →", () => openItem(item.id)));
  } else {
    card.append(
      el("p", "", "Próxima verificação: " + item.next_steps.join(" ")),
    );
    actions.append(
      btn("Registrar decisão", () => decisionModal(item), "secondary"),
      btn("Perguntar ao assistente ↗", () => {
        showView("chat");
        $("#question").value = "Explique a regra " + item.rule_id;
        $("#question").focus();
      }),
    );
    const details = el("details", "item-details");
    details.append(
      el("summary", "", "Conferir fatos e origem"),
      pre({ facts: item.facts, references: item.references }),
    );
    card.append(details);
  }
  card.append(actions);
  return card;
}
function renderQueue() {
  const report = latestDocument(),
    preview = $("#overview-queue"),
    list = $("#review-list");
  preview.replaceChildren();
  list.replaceChildren();
  if (!report) {
    preview.append(
      empty(
        "Seu contexto começa aqui",
        "Explore a demonstração ou importe seus próprios relatórios.",
      ),
    );
    list.append(
      empty(
        "Ainda não há uma revisão",
        "Importe relatórios e selecione “Gerar revisão”.",
      ),
    );
    return;
  }
  preview.append(
    ...report.items.slice(0, 2).map((item) => queueCard(item, true)),
  );
  if (!report.items.length)
    preview.append(
      empty(
        "Sem itens nos campos examinados",
        "Isso não comprova segurança ou cobertura completa.",
      ),
    );
  const priority = $("#priority-filter").value,
    query = $("#review-search").value.toLocaleLowerCase();
  const items = report.items.filter(
    (item) =>
      (!priority || item.priority === priority) &&
      JSON.stringify(item).toLocaleLowerCase().includes(query),
  );
  list.append(...items.map((item) => queueCard(item)));
  if (!items.length)
    list.append(
      empty(
        "Nenhum item neste recorte",
        "Confira os filtros e os limites de cobertura; ausência de itens não atesta segurança.",
      ),
    );
}
function openItem(id) {
  showView("review");
  $("#priority-filter").value = "";
  $("#review-search").value = "";
  renderQueue();
  const item = document.getElementById(id);
  if (item) {
    $("details", item).open = true;
    item.scrollIntoView({ block: "center" });
  }
}
function decisionModal(item) {
  const form = el("form", "modal-form");
  const stateLabel = el("label", "", "Decisão declarada");
  const select = document.createElement("select");
  Object.entries(decisionNames).forEach(([code, label]) => {
    const option = el("option", "", label);
    option.value = code;
    select.append(option);
  });
  select.value = currentDecision(item)?.state || "in-review";
  stateLabel.append(select);
  const [authorLabel, author] = formField(
    "Responsável declarado (sem autenticação de identidade)",
    "text",
    "author",
  );
  author.maxLength = 100;
  const [noteLabel, note] = formField(
    "Justificativa e evidência consultada",
    "textarea",
    "note",
  );
  note.maxLength = 2000;
  note.rows = 4;
  const submit = el("button", "primary", "Registrar no histórico");
  submit.type = "submit";
  const error = el("p", "modal-error");
  form.append(
    el("p", "feedback", item.title),
    stateLabel,
    authorLabel,
    noteLabel,
    submit,
    error,
  );
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    submit.disabled = true;
    try {
      await api(projectPath("decisions"), "POST", {
        review_id: state.snapshot.review.id,
        item_id: item.id,
        state: select.value,
        author: author.value,
        note: note.value,
      });
      await refresh();
      closeModal();
      toast("Decisão registrada com histórico preservado.");
    } catch (e) {
      error.textContent = e.message;
    } finally {
      submit.disabled = false;
    }
  });
  modal("Uma decisão com contexto", form);
}
function renderSources() {
  const list = $("#source-list");
  list.replaceChildren();
  if (!state.snapshot?.sources.length) {
    list.append(
      empty(
        "Nenhuma evidência importada",
        "Seus relatórios serão armazenados somente neste workspace local.",
      ),
    );
    return;
  }
  const active = {};
  state.snapshot.sources.forEach((s) => (active[s.role] = s.id));
  [...state.snapshot.sources].reverse().forEach((source) => {
    const card = el("article", "source-card");
    card.append(
      el("span", "pill", roleNames[source.role] || source.role),
      el("h3", "", source.name),
      el("code", "", "SHA-256 " + source.sha256),
      el(
        "small",
        "",
        date(source.created) +
          (active[source.role] === source.id
            ? " · versão selecionada para a próxima revisão"
            : " · versão anterior preservada"),
      ),
      btn("Conferir campos e cobertura →", () => inspectSource(source.id)),
    );
    list.append(card);
  });
}
async function inspectSource(id) {
  try {
    const source = await api(projectPath("sources/" + id));
    const wrapper = el("div");
    wrapper.append(el("p", "feedback", source.name), pre(source.normalized));
    modal("Campos selecionados da fonte", wrapper);
  } catch (e) {
    toast(e.message, true);
  }
}
async function fileBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1]);
    reader.onerror = () => reject(new Error("Não foi possível ler o arquivo"));
    reader.readAsDataURL(file);
  });
}
function importModal() {
  if (!requireProject()) return;
  const form = el("form", "modal-form");
  const label = el("label", "", "Tipo e papel do relatório");
  const select = document.createElement("select");
  Object.entries(roleNames).forEach(([role, name]) => {
    const option = el("option", "", name);
    option.value = role;
    select.append(option);
  });
  label.append(select);
  const [fileLabel, input] = formField(
    "Arquivo local · até 32 MiB",
    "file",
    "report",
  );
  input.removeAttribute("value");
  input.accept = ".xml,.json";
  const help = el(
    "p",
    "feedback",
    "A nova importação será selecionada para a próxima revisão. Versões anteriores e suas decisões permanecem preservadas. Nenhum motor será executado.",
  );
  const submit = el("button", "primary", "Importar evidência");
  submit.type = "submit";
  const error = el("p", "modal-error");
  form.append(label, fileLabel, help, submit, error);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = input.files[0];
    if (!file) return;
    if (file.size > 32 * 1024 * 1024) {
      error.textContent = "O arquivo excede 32 MiB.";
      return;
    }
    submit.disabled = true;
    submit.textContent = "Validando e importando…";
    try {
      await api(projectPath("sources"), "POST", {
        role: select.value,
        name: file.name,
        content_base64: await fileBase64(file),
      });
      await refresh();
      closeModal();
      toast("Fonte importada. Gere a revisão para atualizar a fila.");
      showView("sources");
    } catch (e) {
      error.textContent = e.message;
    } finally {
      submit.disabled = false;
      submit.textContent = "Importar evidência";
    }
  });
  modal("Importar um relatório existente", form);
}
async function generateReview(button) {
  if (!requireProject()) return;
  await task(button, async () => {
    await api(projectPath("review"), "POST", {});
    await refresh();
    showView("review");
    toast("Revisão gerada a partir das fontes selecionadas.");
  });
}
function renderActivity() {
  const list = $("#activity-list");
  list.replaceChildren();
  const decisions = state.snapshot?.decisions || [];
  if (!decisions.length) {
    list.append(
      empty(
        "A investigação ainda está aberta",
        "Registre decisões na fila de revisão para construir o histórico.",
      ),
    );
    return;
  }
  [...decisions].reverse().forEach((decision) => {
    const card = el("article", "activity-card");
    card.append(
      el("span", "pill", decisionNames[decision.state]),
      el("h3", "", decision.author + " · responsável declarado"),
      el("p", "", decision.note),
      el(
        "small",
        "",
        date(decision.created) + " · revisão " + decision.review.slice(0, 12),
      ),
      el("code", "", " · item " + decision.item.slice(-12)),
    );
    list.append(card);
  });
}
function renderMessages() {
  const messages = $("#messages");
  messages.replaceChildren();
  for (const message of state.snapshot?.messages || []) {
    const user = el("div", "message user");
    user.append(
      el("span", "message-label", "VOCÊ"),
      el("span", "", message.question),
    );
    const assistant = el("div", "message assistant");
    const reply = message.response;
    assistant.append(
      el(
        "span",
        "message-label",
        reply.mode === "local-ollama-generation"
          ? "ATLAS · IA LOCAL"
          : "ATLAS · BUSCA LOCAL",
      ),
      el("span", "", reply.text),
    );
    if (reply.generation_notice)
      assistant.append(el("p", "warning-text", reply.generation_notice));
    const citations = el("div", "citations");
    reply.citations.forEach((citation, index) => {
      const action = () => {
        if (citation.kind === "review-item") {
          if (reply.review_record_id === state.snapshot?.review?.id)
            openItem(citation.item_id);
          else modal("Referência de uma revisão anterior", pre(citation));
        } else if (citation.kind === "source")
          inspectSource(citation.source_id);
        else if (
          citation.kind === "catalog" ||
          citation.kind === "capability"
        ) {
          showView("catalog");
          $("#catalog-search").value = citation.tool_id;
          renderCatalog();
        } else if (citation.kind === "studio") {
          const record = state.snapshot?.studio.find(
            (r) => r.id === citation.record_id,
          );
          modal("Referência do estúdio", pre(record?.document || citation));
        } else
          modal(
            "Referência da revisão",
            pre({ citation, response: reply.text }),
          );
      };
      citations.append(
        btn(
          "[" +
            (index + 1) +
            "] " +
            (citation.rule_id ||
              citation.role ||
              citation.tool_id ||
              (citation.kind === "studio" ? "Estúdio" : "Revisão")),
          action,
        ),
      );
    });
    assistant.append(citations);
    messages.append(user, assistant);
  }
  messages.scrollTop = messages.scrollHeight;
}
async function sendQuestion(question) {
  if (!requireProject()) return;
  if (state.busy) return;
  const project = state.project;
  state.busy = true;
  const submit = $("#chat-form button");
  submit.disabled = true;
  const pending = el(
    "div",
    "busy-text",
    $("#use-model").checked
      ? "Consultando o modelo local…"
      : "Consultando o contexto…",
  );
  $("#messages").append(pending);
  try {
    await api("/api/projects/" + project + "/chat", "POST", {
      question,
      use_model: $("#use-model").checked,
    });
    if (state.project === project) {
      $("#question").value = "";
      await refresh();
    }
  } catch (e) {
    toast(e.message, true);
  } finally {
    pending.remove();
    state.busy = false;
    submit.disabled = false;
  }
}
function renderCatalog() {
  if (!state.catalog) return;
  const list = $("#catalog-list"),
    query = $("#catalog-search").value.toLocaleLowerCase();
  list.replaceChildren();
  const tools = state.catalog.tools.filter((tool) =>
    JSON.stringify(tool).toLocaleLowerCase().includes(query),
  );
  tools.forEach((tool) => {
    const card = el("article", "catalog-card");
    card.append(
      el(
        "span",
        "pill",
        tool.source_status === "source-indexed" ? "FONTE INDEXADA" : "CATÁLOGO",
      ),
      el("h3", "", tool.name),
      el("p", "", tool.purpose),
    );
    const details = el("details");
    details.append(el("summary", "", "Origem, licença e limites"), pre(tool));
    card.append(details);
    list.append(card);
  });
  if (!tools.length)
    list.append(
      empty("Nenhuma tecnologia encontrada", "Tente outro nome ou categoria."),
    );
}
function renderCapabilities() {
  const root = $("#capabilities");
  root.replaceChildren();
  for (const capability of state.capabilities?.capabilities || []) {
    const card = el("article", "capability-card");
    card.append(
      el("span", "pill", capability.status),
      el("h3", "", capability.name),
      el("p", "", capability.description),
      btn("Perguntar no chat ↗", () => {
        showView("chat");
        $("#question").value = "Como " + capability.name + " está integrado?";
        $("#question").focus();
      }),
    );
    root.append(card);
  }
}
function renderStudio() {
  const records = state.snapshot?.studio || [];
  const analysis = records.filter((r) => r.kind === "analysis").at(-1),
    plan = records.filter((r) => r.kind === "blueprint").at(-1);
  const root = $("#source-analysis");
  root.replaceChildren();
  if (analysis) {
    const data = analysis.document;
    root.append(
      el(
        "div",
        "notice",
        data.files + " arquivos · " + Object.keys(data.languages).join(", "),
      ),
      btn("Ver mapa estrutural e limites →", () =>
        modal("Mapa estático de código-fonte", pre(data)),
      ),
    );
  }
  const output = $("#blueprint-output");
  output.replaceChildren();
  if (plan) {
    const wrapper = el("div", "studio-result");
    wrapper.append(
      el("h3", "", plan.document.name),
      el("p", "", "Plano em rascunho · template explícito · requer validação"),
    );
    const ul = el("ul");
    plan.document.modules.forEach((module) =>
      ul.append(el("li", "", module.name)),
    );
    wrapper.append(
      ul,
      btn("Conferir plano completo →", () =>
        modal("Plano de produto", pre(plan.document)),
      ),
      btn(
        "↓ Baixar plano e protótipo",
        () => download("export-studio"),
        "secondary",
      ),
    );
    output.append(wrapper);
  }
}
async function download(action, query = "") {
  try {
    const response = await fetch(projectPath(action) + query);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error);
    }
    const blob = await response.blob(),
      url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download =
      action === "export-studio"
        ? "atlas-product-plan.zip"
        : "atlas-project.zip";
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 3000);
  } catch (e) {
    toast(e.message, true);
  }
}
function exportModal() {
  if (!requireProject()) return;
  if (!state.snapshot.review) {
    toast("Gere uma revisão antes de exportar.", true);
    return;
  }
  const wrapper = el("div", "modal-form");
  wrapper.append(
    el(
      "p",
      "feedback",
      "O pacote contém a revisão JSON/HTML, fontes declaradas, conferência de reprodução, decisões, chat e dados do estúdio.",
    ),
  );
  const label = el("label", "checkbox-label");
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  label.append(
    checkbox,
    el(
      "span",
      "",
      "Incluir os relatórios originais da revisão (podem conter dados sensíveis)",
    ),
  );
  wrapper.append(
    label,
    btn(
      "Baixar pacote ZIP",
      async () => {
        await download("export", checkbox.checked ? "?originals=1" : "");
        closeModal();
      },
      "primary",
    ),
  );
  modal("Uma investigação que você pode levar", wrapper);
}
$("#modal-close").addEventListener("click", closeModal);
$("#new-project").addEventListener("click", newProject);
$("#project-select").addEventListener("change", async (event) => {
  state.project = event.target.value;
  closeModal();
  state.snapshot = null;
  render();
  try {
    await refresh();
  } catch (e) {
    toast(e.message, true);
  }
});
$$("[data-view]").forEach((button) =>
  button.addEventListener("click", () => showView(button.dataset.view)),
);
$$("[data-go]").forEach((button) =>
  button.addEventListener("click", () => showView(button.dataset.go)),
);
$$('[data-action="import"]').forEach((button) =>
  button.addEventListener("click", importModal),
);
$$('[data-action="review"]').forEach((button) =>
  button.addEventListener("click", () => generateReview(button)),
);
$("#demo").addEventListener("click", (event) =>
  task(event.currentTarget, async () => {
    const project = await api("/api/demo", "POST", {});
    await loadProjects(project.id);
    toast("Demonstração sintética criada: nenhum sistema foi acessado.");
  }),
);
$("#priority-filter").addEventListener("change", renderQueue);
$("#review-search").addEventListener("input", renderQueue);
$("#catalog-search").addEventListener("input", renderCatalog);
$("#chat-toggle").addEventListener("click", () => {
  if (state.view === "chat") $("#question").focus();
  else $("#chat-panel").classList.toggle("open");
});
$("#chat-close").addEventListener("click", () => {
  if (state.view === "chat") showView("overview");
  $("#chat-panel").classList.remove("open");
});
$("#chat-form").addEventListener("submit", (event) => {
  event.preventDefault();
  sendQuestion($("#question").value);
});
$$("[data-question]").forEach((button) =>
  button.addEventListener("click", () => {
    $("#question").value = button.dataset.question;
    sendQuestion(button.dataset.question);
  }),
);
$("#use-model").addEventListener("change", () => {
  $("#chat-mode-label").textContent = $("#use-model").checked
    ? "IA local · confira as afirmações"
    : "Busca local com referências";
});
$("#export").addEventListener("click", exportModal);
$("#replay").addEventListener("click", (event) => {
  if (!requireProject()) return;
  task(event.currentTarget, async () => {
    const result = await api(projectPath("replay"), "POST", {});
    const content = el("div");
    content.append(
      el(
        "p",
        "notice",
        result.status === "matched"
          ? "Revisão reproduzida: fontes e conteúdo coincidem com as regras instaladas."
          : "A conferência encontrou divergências.",
      ),
      pre(result),
    );
    modal("Conferência de reprodução", content);
  });
});
$("#delete-project").addEventListener("click", () => {
  if (!state.project) return;
  const form = el("form", "modal-form");
  const [field, input] = formField(
    "Digite EXCLUIR para remover o projeto e seus dados locais",
    "text",
    "confirm",
  );
  const submit = el("button", "primary", "Excluir definitivamente");
  submit.type = "submit";
  const error = el("p", "modal-error");
  form.append(
    el(
      "p",
      "feedback",
      "Exporte antes se precisar conservar as fontes e decisões. A remoção não apaga exportações ou backups feitos fora do aplicativo.",
    ),
    field,
    submit,
    error,
  );
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (input.value !== "EXCLUIR") {
      error.textContent = "Digite EXCLUIR para confirmar.";
      return;
    }
    submit.disabled = true;
    try {
      await api(projectPath(), "DELETE", {});
      await loadProjects("");
      closeModal();
      toast("Projeto excluído do workspace local.");
    } catch (e) {
      error.textContent = e.message;
    } finally {
      submit.disabled = false;
    }
  });
  modal("Excluir " + state.snapshot.project.name + "?", form);
});
$("#source-zip").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  if (!requireProject()) {
    event.target.value = "";
    return;
  }
  if (file.size > 16 * 1024 * 1024) {
    toast("O ZIP excede 16 MiB.", true);
    return;
  }
  const label = $("#source-analysis");
  label.textContent = "Mapeando a estrutura, sem executar código…";
  try {
    await api(projectPath("inspect-source"), "POST", {
      content_base64: await fileBase64(file),
    });
    await refresh();
    toast("Mapa estrutural preservado no estúdio.");
  } catch (e) {
    toast(e.message, true);
    renderStudio();
  } finally {
    event.target.value = "";
  }
});
$("#blueprint-form").addEventListener("submit", (event) => {
  event.preventDefault();
  if (!requireProject()) return;
  const form = event.currentTarget;
  task($("button", form), async () => {
    await api(projectPath("blueprint"), "POST", {
      name: form.elements.name.value,
      brief: form.elements.brief.value,
    });
    await refresh();
    toast("Plano e backlog criados. Confira as hipóteses antes de construir.");
  });
});
async function init() {
  try {
    const boot = await api("/api/bootstrap");
    state.csrf = boot.csrf;
    $("#app-version").textContent = "v" + boot.version;
    $("#model-status").textContent = boot.model_configured
      ? boot.model + " · configuração detectada"
      : "não configurada";
    $("#use-model").disabled = !boot.model_configured;
    [state.catalog, state.capabilities] = await Promise.all([
      api("/api/catalog"),
      api("/api/capabilities"),
    ]);
    renderCatalog();
    renderCapabilities();
    await loadProjects();
  } catch (e) {
    toast("Não foi possível iniciar: " + e.message, true);
    $("#overview-queue").replaceChildren(
      empty(
        "Servidor indisponível",
        "Inicie python scripts/app_server.py e abra o endereço informado.",
      ),
    );
  }
}
init();

$("#diagnostics").addEventListener("click", (event) => {
  task(event.currentTarget, async () => {
    const result = await api("/api/diagnostics", "POST", {});
    const content = el("div");
    content.append(
      el(
        "p",
        "notice",
        result.status === "ok"
          ? "Conferência concluída: arquivos e banco íntegros nas verificações realizadas."
          : "A conferência encontrou pontos que precisam de atenção.",
      ),
      pre(result),
    );
    modal("Diagnóstico do workspace", content);
  });
});

const { JSDOM, VirtualConsole } = require("jsdom");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const assert = require("node:assert/strict");
const path = require("node:path").resolve(__dirname, "..");
const temp = fs.mkdtempSync(
  require("node:path").join(require("node:os").tmpdir(), "atlas-ui-test-"),
);
const child = spawn(
  process.env.PYTHON || "python",
  [
    "-u",
    "-c",
    "import os,sys;from pathlib import Path;sys.path.insert(0,str(Path(os.environ['ATLAS_TEST_ROOT'])/'scripts'));from app_server import LocalServer;from app_service import Application;s=LocalServer(('127.0.0.1',0),Application(os.environ['ATLAS_TEST_DB']));print(s.server_port,flush=True);s.serve_forever()",
  ],
  {
    env: {
      ...process.env,
      ATLAS_TEST_ROOT: path,
      ATLAS_TEST_DB: require("node:path").join(temp, "test.sqlite3"),
      ATLAS_OLLAMA_MODEL: "",
    },
  },
);
let dom;
async function until(test, label) {
  const start = Date.now();
  while (!test()) {
    if (Date.now() - start > 10000) throw new Error("Timeout: " + label);
    await new Promise((r) => setTimeout(r, 25));
  }
}
(async () => {
  const port = await new Promise((resolve, reject) => {
    child.stdout.once("data", (data) => resolve(Number(String(data).trim())));
    child.once("error", reject);
    child.once("exit", (code) =>
      reject(new Error("Test server exited: " + code)),
    );
  });
  const origin = "http://127.0.0.1:" + port;
  let cookie = "";
  const errors = [],
    downloads = [];
  const console = new VirtualConsole();
  console.on("jsdomError", (error) => errors.push(String(error)));
  console.on("error", (error) => errors.push(String(error)));
  dom = await JSDOM.fromURL(origin, {
    resources: "usable",
    runScripts: "dangerously",
    pretendToBeVisual: true,
    virtualConsole: console,
    beforeParse(window) {
      window.fetch = async (url, options = {}) => {
        const headers = {
          ...(options.headers || {}),
          ...(cookie ? { Cookie: cookie } : {}),
        };
        const result = await fetch(new URL(url, origin), {
          ...options,
          headers,
        });
        const setCookie = result.headers.get("set-cookie");
        if (setCookie) cookie = setCookie.split(";")[0];
        return result;
      };
      window.scrollTo = () => {};
      window.HTMLElement.prototype.scrollIntoView = function () {};
      window.HTMLDialogElement.prototype.showModal = function () {
        this.open = true;
      };
      window.HTMLDialogElement.prototype.close = function () {
        this.open = false;
      };
      window.URL.createObjectURL = (blob) => {
        downloads.push(blob);
        return "blob:test";
      };
      window.URL.revokeObjectURL = () => {};
      window.HTMLAnchorElement.prototype.click = function () {};
    },
  });
  const w = dom.window,
    d = w.document,
    $ = (s) => d.querySelector(s),
    $$ = (s) => [...d.querySelectorAll(s)];
  await until(
    () => $("#capabilities").children.length === 7,
    "bootstrap and capabilities",
  );
  $("#demo").click();
  await until(() => $("#stat-items").textContent === "8", "demo 8 items");
  assert.equal($("#stat-first").textContent, "4");
  assert.equal($("#stat-sources").textContent, "4");
  $('[data-view="review"]').click();
  assert.equal($$("#review-list .queue-item").length, 8);
  $("#priority-filter").value = "review-first";
  $("#priority-filter").dispatchEvent(new w.Event("change"));
  assert.equal($$("#review-list .queue-item").length, 4);
  $("#review-list .item-actions .secondary").click();
  assert.equal($("#modal").open, true);
  $('#modal input[name="author"]').value = "Analista de teste DOM";
  $("#modal textarea").value = "Conferência de escopo registrada no teste.";
  $("#modal form").dispatchEvent(
    new w.Event("submit", { bubbles: true, cancelable: true }),
  );
  await until(
    () => $("#stat-decisions").textContent === "1",
    "decision persistence",
  );
  $('[data-view="chat"]').click();
  $("#question").value = "O que revisar primeiro?";
  $("#chat-form").dispatchEvent(
    new w.Event("submit", { bubbles: true, cancelable: true }),
  );
  await until(() => $$(".message.assistant").length === 1, "grounded chat");
  assert.ok($$(".citations button").length >= 1);
  $(".citations button").click();
  assert.equal($("#view-review").hidden, false);
  assert.equal($("#review-list details").open, true);
  $('[data-view="sources"]').click();
  $('[data-action="import"]').click();
  const file = new w.File(
    [fs.readFileSync(path + "/tests/fixtures/trivy-synthetic.json")],
    "new-trivy.json",
    { type: "application/json" },
  );
  Object.defineProperty($('#modal input[type="file"]'), "files", {
    value: [file],
    configurable: true,
  });
  $("#modal select").value = "trivy";
  $("#modal form").dispatchEvent(
    new w.Event("submit", { bubbles: true, cancelable: true }),
  );
  await until(() => $("#stat-sources").textContent === "5", "UI file import");
  assert.equal($("#stale").hidden, false);
  $('#view-review [data-action="review"]').click();
  await until(() => $("#stale").hidden === true, "new review");
  assert.equal($("#stat-decisions").textContent, "0");
  $("#compare-reviews").click();
  assert.equal($("#modal select").options.length, 2);
  $("#modal form").dispatchEvent(
    new w.Event("submit", { bubbles: true, cancelable: true }),
  );
  await until(
    () => $("#modal-title").textContent === "Evolução das revisões",
    "review evolution",
  );
  assert.ok(
    $("#modal-body").textContent.includes(
      "Não observado depois não significa corrigido",
    ),
  );
  assert.ok(
    $("#modal-body").textContent.includes("Mesmos campos selecionados: 4"),
  );
  $("#modal-close").click();
  $('[data-view="chat"]').click();
  $("#question").value = "O que mudou entre as revisões?";
  $("#chat-form").dispatchEvent(
    new w.Event("submit", { bubbles: true, cancelable: true }),
  );
  await until(() => $$(".message.assistant").length === 2, "evolution chat");
  $$(".message.assistant").at(-1).querySelector(".citations button").click();
  await until(
    () =>
      $("#modal-title").textContent === "Evolução das revisões" &&
      $("#modal").open,
    "evolution chat citation",
  );
  $("#modal-close").click();

  $('[data-view="studio"]').click();
  const zipResult = require("node:child_process").spawnSync(
    process.env.PYTHON || "python",
    [
      "-c",
      "import io,zipfile,sys;b=io.BytesIO();z=zipfile.ZipFile(b,'w');z.writestr('main.py','print(123)');z.writestr('LICENSE','candidate');z.close();sys.stdout.buffer.write(b.getvalue())",
    ],
  );
  assert.equal(zipResult.status, 0);
  const sourceZip = new w.File([zipResult.stdout], "own-source.zip", {
    type: "application/zip",
  });
  Object.defineProperty($("#source-zip"), "files", {
    value: [sourceZip],
    configurable: true,
  });
  $("#source-zip").dispatchEvent(new w.Event("change"));
  await until(
    () => $("#source-analysis").textContent.includes("2 arquivos"),
    "static source archive import",
  );
  $("#blueprint-form input").value = "Meu produto de teste";
  $("#blueprint-form textarea").value =
    "Organizar evidências para equipes pequenas.";
  $("#blueprint-form").dispatchEvent(
    new w.Event("submit", { bubbles: true, cancelable: true }),
  );
  await until(
    () => $("#blueprint-output").textContent.includes("Meu produto de teste"),
    "product plan",
  );
  $("#blueprint-output .secondary").click();
  await until(() => downloads.length === 1, "prototype zip download");
  assert.ok(downloads[0].size > 1000);
  $("#export").click();
  $("#modal .primary").click();
  await until(() => downloads.length === 2, "project export download");
  const projects = await (await w.fetch("/api/projects")).json();
  assert.equal(projects.length, 1);
  const snapshot = await (
    await w.fetch("/api/projects/" + projects[0].id)
  ).json();
  assert.equal(snapshot.decisions.length, 1);
  assert.equal(snapshot.messages.length, 2);
  assert.equal(snapshot.studio.length, 2);
  // Delay an old workspace response until a newer selection has loaded.
  const originalProject = projects[0].id;
  $("#new-project").click();
  $('#modal input[name="name"]').value = "Projeto de concorrência";
  $("#modal form").dispatchEvent(
    new w.Event("submit", { bubbles: true, cancelable: true }),
  );
  await until(
    () => $("#project-title").textContent === "Projeto de concorrência",
    "second workspace",
  );
  const newerProject = $("#project-select").value;
  const baseFetch = w.fetch;
  let releaseOld,
    blocked = false;
  w.fetch = async (url, options = {}) => {
    const response = await baseFetch(url, options);
    if (
      url === "/api/projects/" + originalProject &&
      (!options.method || options.method === "GET")
    ) {
      blocked = true;
      await new Promise((resolve) => (releaseOld = resolve));
    }
    return response;
  };
  $("#project-select").value = originalProject;
  $("#project-select").dispatchEvent(new w.Event("change"));
  await until(() => blocked, "delayed old response");
  $("#project-select").value = newerProject;
  $("#project-select").dispatchEvent(new w.Event("change"));
  await until(
    () => $("#project-title").textContent === "Projeto de concorrência",
    "newer workspace response",
  );
  releaseOld();
  await new Promise((resolve) => setTimeout(resolve, 75));
  assert.equal($("#project-title").textContent, "Projeto de concorrência");
  assert.equal($("#project-select").value, newerProject);
  assert.equal($("#stat-items").textContent, "0");
  w.fetch = baseFetch;
  $("#delete-project").click();
  $("#modal input").value = "EXCLUIR";
  $("#modal form").dispatchEvent(
    new w.Event("submit", { bubbles: true, cancelable: true }),
  );
  await until(
    () => $("#project-title").textContent === snapshot.project.name,
    "remaining original workspace",
  );
  $("#delete-project").click();
  $("#modal input").value = "EXCLUIR";
  $("#modal form").dispatchEvent(
    new w.Event("submit", { bubbles: true, cancelable: true }),
  );
  await until(() => $("#stat-items").textContent === "0", "project delete");
  $("#diagnostics").click();
  await until(
    () => $("#modal-title").textContent === "Diagnóstico do workspace",
    "workspace diagnostics",
  );
  const diagnostic = JSON.parse($("#modal-body pre").textContent);
  assert.equal(diagnostic.database.status, "ok");
  assert.equal(diagnostic.chat.optional_model.status, "not-configured");
  assert.equal(diagnostic.version, "0.2.0");
  assert.deepEqual(errors, []);
  process.stdout.write(
    JSON.stringify(
      {
        method: "jsdom DOM and HTTP integration, not real-browser layout QA",
        checks: [
          "bootstrap",
          "demo-three-producers",
          "review-filter",
          "decision-history",
          "grounded-chat-citation-navigation",
          "file-import-staleness",
          "new-review-isolated-decisions",
          "static-source-archive",
          "blueprint-and-prototype-download",
          "project-export",
          "persistent-state",
          "project-deletion",
          "delayed-workspace-response",
          "review-evolution",
          "evolution-chat-reference",
          "workspace-diagnostics",
        ],
        javascriptErrors: errors.length,
        downloads: downloads.length,
      },
      null,
      2,
    ) + "\n",
  );
})()
  .catch((error) => {
    process.stderr.write(error.stack + "\n");
    process.exitCode = 1;
  })
  .finally(() => {
    dom?.window.close();
    child.kill();
    fs.rmSync(temp, { recursive: true, force: true });
  });

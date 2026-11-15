"use strict";
const { JSDOM } = require("jsdom");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const root = path.resolve(__dirname, "..");
const directory = fs.mkdtempSync(
  path.join(os.tmpdir(), "atlas-prototype-test-"),
);
let dom;
try {
  const result = spawnSync(
    process.env.PYTHON || "python",
    [
      "-c",
      "import os,sys;from pathlib import Path;sys.path.insert(0,str(Path(os.environ['ATLAS_TEST_ROOT'])/'scripts'));from app_studio import blueprint;from app_scaffold import scaffold;files=scaffold(blueprint('Produto próprio','Organizar o trabalho de uma equipe'));target=Path(os.environ['ATLAS_TEST_OUTPUT']);[(target/Path(name).name).write_text(content,encoding='utf-8') for name,content in files.items()]",
    ],
    {
      env: {
        ...process.env,
        ATLAS_TEST_ROOT: root,
        ATLAS_TEST_OUTPUT: directory,
      },
      encoding: "utf8",
    },
  );
  assert.equal(result.status, 0, result.stderr);
  const html = fs.readFileSync(path.join(directory, "index.html"), "utf8"),
    script = fs.readFileSync(path.join(directory, "app.js"), "utf8");
  function create(saved) {
    const instance = new JSDOM(html, {
      url: "http://127.0.0.1:8787",
      runScripts: "outside-only",
      beforeParse(w) {
        w.structuredClone = structuredClone;
        w.HTMLElement.prototype.scrollIntoView = function () {};
        w.confirm = () => true;
      },
    });
    if (saved)
      for (const [key, value] of saved)
        instance.window.localStorage.setItem(key, value);
    instance.window.eval(script);
    return instance;
  }
  dom = create();
  let w = dom.window,
    d = w.document,
    $ = (s) => d.querySelector(s);
  assert.equal($("#total").textContent, "6");
  const checkbox = $("#tasks input");
  checkbox.checked = true;
  checkbox.dispatchEvent(new w.Event("change"));
  assert.equal($("#done").textContent, "1");
  $("#task").value = "<img src=x onerror=alert(1)>";
  $("#add").dispatchEvent(
    new w.Event("submit", { bubbles: true, cancelable: true }),
  );
  assert.equal($("#total").textContent, "7");
  assert.equal(d.querySelectorAll("img").length, 0);
  assert.ok($("#tasks").textContent.includes("<img"));
  $("#question").value = "O que falta?";
  $("#chat").dispatchEvent(
    new w.Event("submit", { bubbles: true, cancelable: true }),
  );
  assert.equal(d.querySelectorAll("#messages .message").length, 2);
  assert.ok($("#messages").textContent.includes("<img"));
  const saved = Object.entries(w.localStorage);
  dom.window.close();
  dom = create(saved);
  d = dom.window.document;
  $ = (s) => d.querySelector(s);
  assert.equal($("#total").textContent, "7");
  assert.equal($("#done").textContent, "1");
  $("#reset").click();
  assert.equal($("#total").textContent, "6");
  assert.equal($("#done").textContent, "0");
  process.stdout.write(
    JSON.stringify(
      {
        method:
          "jsdom DOM test of generated original template, not browser layout QA",
        checks: [
          "task-rendering",
          "task-completion",
          "task-creation",
          "inert-user-text",
          "local-chat",
          "browser-storage-restore",
          "reset",
        ],
      },
      null,
      2,
    ) + "\n",
  );
} finally {
  dom?.window.close();
  fs.rmSync(directory, { recursive: true, force: true });
}

const form = document.getElementById("scan-form");
const submitButton = document.getElementById("submit-button");
const statusText = document.getElementById("status-text");
const durationText = document.getElementById("duration-text");
const statusPill = document.getElementById("status-pill");
const themeToggleButton = document.getElementById("theme-toggle");
const themeToggleLabel = document.getElementById("theme-toggle-label");
const terminalOutput = document.getElementById("terminal-output");
const historyList = document.getElementById("history-list");
const historySearchInput = document.getElementById("history-search");
const refreshHistoryButton = document.getElementById("refresh-history");
const juiceShopButton = document.getElementById("use-juice-shop-target");
const authAuditConfig = document.getElementById("auth-audit-config");
const hydraConfig = document.getElementById("hydra-config");
const wiresharkConfig = document.getElementById("wireshark-config");
const authAuditEndpointPathInput = document.getElementById("auth-audit-endpoint-path");
const authAuditRequestFormatInput = document.getElementById("auth-audit-request-format");
const authAuditUsernameFieldInput = document.getElementById("auth-audit-username-field");
const authAuditPasswordFieldInput = document.getElementById("auth-audit-password-field");
const authAuditFailureMarkerInput = document.getElementById("auth-audit-failure-marker");
const authAuditAttemptsInput = document.getElementById("auth-audit-attempts");
const hydraUsernameInput = document.getElementById("hydra-username");
const hydraUsernameSourceInput = document.getElementById("hydra-username-source");
const hydraUsernameListHint = document.getElementById("hydra-username-list-hint");
const hydraPasswordInput = document.getElementById("hydra-password");
const hydraPasswordSourceInput = document.getElementById("hydra-password-source");
const hydraPasswordListHint = document.getElementById("hydra-password-list-hint");
const hydraPortInput = document.getElementById("hydra-port");
const wiresharkInterfaceInput = document.getElementById("wireshark-interface");
const wiresharkDurationInput = document.getElementById("wireshark-duration");
const moduleCheckboxes = Array.from(document.querySelectorAll('input[name="modules"]'));
const EXECUTION_ORDER = ["nmap", "hydra", "wireshark", "whatweb", "theharvester", "gobuster", "sslyze", "nikto", "sqlmap", "auth-audit"];

const STREAM_ENDPOINTS = {
  nmap: "/api/scans/nmap/stream",
  hydra: "/api/scans/hydra/stream",
  wireshark: "/api/scans/wireshark/stream",
  whatweb: "/api/scans/whatweb/stream",
  theharvester: "/api/scans/theharvester/stream",
  gobuster: "/api/scans/gobuster/stream",
  sslyze: "/api/scans/sslyze/stream",
  nikto: "/api/scans/nikto/stream",
  sqlmap: "/api/scans/sqlmap/stream",
  "auth-audit": "/api/scans/auth-audit/stream",
};

let historyRefreshPending = false;
let allHistoryEntries = [];

function applyTheme(themeName) {
  document.body.classList.remove("theme-light", "theme-dark");
  document.body.classList.add(themeName);
  localStorage.setItem("pentest-toolbox-theme", themeName);

  const isDark = themeName === "theme-dark";
  if (themeToggleButton) {
    themeToggleButton.setAttribute("aria-pressed", isDark ? "true" : "false");
  }
  if (themeToggleLabel) {
    themeToggleLabel.textContent = isDark ? "Mode clair" : "Mode sombre";
  }
}

function initializeTheme() {
  const savedTheme = localStorage.getItem("pentest-toolbox-theme");
  if (savedTheme === "theme-dark" || savedTheme === "theme-light") {
    applyTheme(savedTheme);
    return;
  }
  applyTheme("theme-light");
}

function setPendingState(isPending) {
  submitButton.disabled = isPending;
  submitButton.textContent = isPending ? "Execution..." : "Lancer";
}

function setStatus(kind, message, duration = "-") {
  statusText.textContent = message;
  durationText.textContent = duration;
  statusPill.className = "status-dot";

  if (kind === "running") {
    statusPill.classList.add("status-running");
    statusPill.textContent = "running";
    return;
  }

  if (kind === "success") {
    statusPill.classList.add("status-success");
    statusPill.textContent = "success";
    return;
  }

  if (kind === "error") {
    statusPill.classList.add("status-error");
    statusPill.textContent = "error";
    return;
  }

  statusPill.classList.add("status-idle");
  statusPill.textContent = "idle";
}

function appendTerminalLine(line = "") {
  terminalOutput.textContent += `${line}\n`;
  terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

function resetTerminal() {
  terminalOutput.textContent = "";
}

function getSelectedModules() {
  return Array.from(document.querySelectorAll('input[name="modules"]:checked')).map((input) => input.value);
}

function getExecutionOrder(selectedModules) {
  return EXECUTION_ORDER.filter((moduleId) => selectedModules.includes(moduleId));
}

function isModuleSelected(moduleId) {
  return getSelectedModules().includes(moduleId);
}

function toggleModuleConfigs() {
  if (authAuditConfig) {
    authAuditConfig.hidden = !isModuleSelected("auth-audit");
  }
  if (hydraConfig) {
    hydraConfig.hidden = !isModuleSelected("hydra");
  }
  if (wiresharkConfig) {
    wiresharkConfig.hidden = !isModuleSelected("wireshark");
  }
  toggleHydraUsernameMode();
  toggleHydraPasswordMode();
}

function toggleHydraUsernameMode() {
  if (!hydraUsernameSourceInput || !hydraUsernameInput || !hydraUsernameListHint) {
    return;
  }

  const selectedOption = hydraUsernameSourceInput.selectedOptions[0];
  const mode = hydraUsernameSourceInput.value;
  const listPath = selectedOption?.dataset.path || "";
  const isManual = mode === "manual";

  hydraUsernameInput.disabled = !isManual;
  hydraUsernameInput.placeholder = isManual ? "utilisateur SSH" : "desactive avec une wordlist";
  hydraUsernameListHint.textContent = isManual
    ? "Source utilisateurs : saisie manuelle."
    : `Wordlist Kali utilisateurs : ${listPath}`;
}

function toggleHydraPasswordMode() {
  if (!hydraPasswordSourceInput || !hydraPasswordInput || !hydraPasswordListHint) {
    return;
  }

  const selectedOption = hydraPasswordSourceInput.selectedOptions[0];
  const mode = hydraPasswordSourceInput.value;
  const listPath = selectedOption?.dataset.path || "";
  const isManual = mode === "manual";

  hydraPasswordInput.disabled = !isManual;
  hydraPasswordInput.placeholder = isManual ? "mot de passe SSH" : "desactive avec une wordlist";
  hydraPasswordListHint.hidden = isManual;
  hydraPasswordListHint.textContent = isManual ? "" : `Wordlist Kali utilisee : ${listPath}`;
}

function getHydraOptions() {
  const username = hydraUsernameInput?.value.trim() || "";
  const usernameSelectedOption = hydraUsernameSourceInput?.selectedOptions?.[0];
  const usernameMode = hydraUsernameSourceInput?.value || "shortlist";
  const usernameListPath = usernameSelectedOption?.dataset.path || "";
  const password = hydraPasswordInput?.value || "";
  const selectedOption = hydraPasswordSourceInput?.selectedOptions?.[0];
  const passwordMode = hydraPasswordSourceInput?.value || "manual";
  const passwordListPath = selectedOption?.dataset.path || "";
  const port = hydraPortInput?.value.trim() || "22";

  if (usernameMode === "manual" && !username) {
    throw new Error("Hydra requiert un identifiant SSH.");
  }

  if (usernameMode !== "manual" && !usernameListPath) {
    throw new Error("La wordlist utilisateurs Hydra selectionnee est indisponible.");
  }

  if (passwordMode === "manual" && !password) {
    throw new Error("Hydra requiert un mot de passe SSH.");
  }

  if (passwordMode !== "manual" && !passwordListPath) {
    throw new Error("La wordlist Hydra selectionnee est indisponible.");
  }

  if (!/^\d+$/.test(port)) {
    throw new Error("Le port Hydra doit etre numerique.");
  }

  return {
    username,
    username_mode: usernameMode,
    username_list_path: usernameListPath,
    password,
    password_mode: passwordMode,
    password_list_path: passwordListPath,
    port: Number(port),
  };
}

function getWiresharkOptions() {
  const captureInterface = wiresharkInterfaceInput?.value.trim() || "eth0";
  const duration = wiresharkDurationInput?.value || "10";

  if (!captureInterface) {
    throw new Error("Wireshark requiert une interface reseau.");
  }

  if (!/^\d+$/.test(duration)) {
    throw new Error("Wireshark requiert une duree numerique en secondes.");
  }

  if (Number(duration) < 1 || Number(duration) > 300) {
    throw new Error("Wireshark autorise une duree comprise entre 1 et 300 secondes.");
  }

  return {
    interface: captureInterface,
    duration: Number(duration),
  };
}

function getAuthAuditOptions() {
  const endpointPath = authAuditEndpointPathInput?.value.trim() || "/rest/user/login";
  const requestFormat = authAuditRequestFormatInput?.value || "json";
  const usernameField = authAuditUsernameFieldInput?.value.trim() || "email";
  const passwordField = authAuditPasswordFieldInput?.value.trim() || "password";
  const failureMarker = authAuditFailureMarkerInput?.value.trim() || "Invalid email or password.";
  const attempts = authAuditAttemptsInput?.value.trim() || "3";

  if (!endpointPath) {
    throw new Error("Auth Audit requiert un endpoint de connexion.");
  }

  if (!["json", "form"].includes(requestFormat)) {
    throw new Error("Auth Audit requiert un format de requete valide.");
  }

  if (!usernameField || !passwordField) {
    throw new Error("Auth Audit requiert le nom des champs identifiant et mot de passe.");
  }

  if (!/^\d+$/.test(attempts)) {
    throw new Error("Auth Audit requiert un nombre de tentatives numerique.");
  }

  if (Number(attempts) < 1 || Number(attempts) > 5) {
    throw new Error("Auth Audit autorise entre 1 et 5 tentatives.");
  }

  return {
    endpoint_path: endpointPath,
    request_format: requestFormat,
    username_field: usernameField,
    password_field: passwordField,
    failure_marker: failureMarker,
    attempts: Number(attempts),
  };
}

function getModuleOptions(moduleId) {
  if (moduleId === "hydra") {
    return getHydraOptions();
  }
  if (moduleId === "wireshark") {
    return getWiresharkOptions();
  }
  if (moduleId === "auth-audit") {
    return getAuthAuditOptions();
  }
  return {};
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function formatDate(value) {
  try {
    return new Date(value).toLocaleString("fr-FR");
  } catch {
    return value;
  }
}

function renderHistory(entries) {
  if (!entries.length) {
    historyList.innerHTML = '<p class="history-empty">Aucune commande executee pour le moment.</p>';
    return;
  }

  historyList.innerHTML = entries.map((entry) => `
    <article class="history-item">
      <div class="history-item-head">
        <strong>${escapeHtml(entry.module_name)} • ${escapeHtml(entry.target)}</strong>
        <span class="history-state ${entry.ok ? "history-ok" : "history-ko"}">${entry.ok ? "OK" : "KO"}</span>
      </div>
      <p class="history-date">${escapeHtml(formatDate(entry.created_at))}</p>
      <code class="history-command">${escapeHtml(entry.command)}</code>
      <p class="history-meta">${entry.duration_seconds}s • code ${entry.exit_code}</p>
      <div class="history-links">
        <a href="${entry.json_artifact_url}" target="_blank" rel="noreferrer">JSON</a>
        <a href="${entry.pdf_artifact_url}" target="_blank" rel="noreferrer">PDF</a>
      </div>
    </article>
  `).join("");
}

function renderHistory(entries) {
  if (!entries.length) {
    historyList.innerHTML = '<p class="history-empty">Aucune commande executee pour le moment.</p>';
    return;
  }

  historyList.innerHTML = entries.map((entry) => `
    <article class="history-item">
      <div class="history-item-head">
        <strong>${escapeHtml(entry.module_name)} • ${escapeHtml(entry.target)}</strong>
        <span class="history-state ${entry.ok ? "history-ok" : "history-ko"}">${entry.ok ? "OK" : "KO"}</span>
      </div>
      <p class="history-date">${escapeHtml(formatDate(entry.created_at))}</p>
      <p class="history-meta">${entry.duration_seconds}s • code ${entry.exit_code}</p>
      <details class="history-details">
        <summary>Voir la commande</summary>
        <code class="history-command">${escapeHtml(entry.command)}</code>
      </details>
      <div class="history-links">
        <a href="${entry.json_artifact_url}" target="_blank" rel="noreferrer">JSON</a>
        <a href="${entry.pdf_artifact_url}" target="_blank" rel="noreferrer">PDF</a>
      </div>
    </article>
  `).join("");
}

function applyHistoryFilter() {
  const query = historySearchInput?.value.trim().toLowerCase() || "";
  if (!query) {
    renderHistory(allHistoryEntries);
    return;
  }

  const filteredEntries = allHistoryEntries.filter((entry) => {
    const haystack = [
      entry.module_name,
      entry.target,
      entry.command,
      entry.created_at,
      entry.exit_code,
    ].join(" ").toLowerCase();
    return haystack.includes(query);
  });

  if (!filteredEntries.length) {
    historyList.innerHTML = '<p class="history-empty">Aucun resultat ne correspond a cette recherche.</p>';
    return;
  }

  renderHistory(filteredEntries);
}

async function loadHistory() {
  if (historyRefreshPending) {
    return;
  }

  historyRefreshPending = true;
  refreshHistoryButton.disabled = true;

  try {
    const response = await fetch("/api/scans/history");
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Impossible de charger l'historique.");
    }
    allHistoryEntries = payload;
    applyHistoryFilter();
  } catch (error) {
    historyList.innerHTML = `<p class="history-empty">${escapeHtml(error.message)}</p>`;
  } finally {
    historyRefreshPending = false;
    refreshHistoryButton.disabled = false;
  }
}

async function streamScan(moduleId, target, scripts, options = {}) {
  const endpoint = STREAM_ENDPOINTS[moduleId];
  if (!endpoint) {
    throw new Error(`Aucun endpoint configure pour ${moduleId}.`);
  }

  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target, scripts, options }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Impossible de lancer ${moduleId}.`);
  }

  if (!response.body) {
    throw new Error("Le flux de sortie est indisponible.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finished = false;
  let latestResult = null;
  let latestError = null;

  while (!finished) {
    const { value, done } = await reader.read();
    finished = done;
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

    let lineBreakIndex = buffer.indexOf("\n");
    while (lineBreakIndex >= 0) {
      const line = buffer.slice(0, lineBreakIndex).trim();
      buffer = buffer.slice(lineBreakIndex + 1);
      if (line) {
        const event = JSON.parse(line);
        const eventResult = handleStreamEvent(event);
        if (event.event === "finish" && eventResult) {
          latestResult = eventResult;
        }
        if (event.event === "error") {
          latestError = event;
        }
      }
      lineBreakIndex = buffer.indexOf("\n");
    }
  }

  if (buffer.trim()) {
    const event = JSON.parse(buffer.trim());
    const eventResult = handleStreamEvent(event);
    if (event.event === "finish" && eventResult) {
      latestResult = eventResult;
    }
    if (event.event === "error") {
      latestError = event;
    }
  }

  if (latestResult) {
    return latestResult;
  }

  if (latestError) {
    return {
      module_id: moduleId,
      module_name: latestError.module_name || moduleId,
      command: "",
      stdout: "",
      stderr: latestError.message || "Erreur inconnue",
      exit_code: -1,
      duration_seconds: 0,
      ok: false,
    };
  }

  throw new Error(`Le flux ${moduleId} s'est termine sans resultat exploitable.`);
}

function handleStreamEvent(event) {
  if (event.event === "start") {
    appendTerminalLine(`$ [${event.module_name}] ${event.command}`);
    appendTerminalLine("");
    setStatus("running", `Execution de ${event.module_name} sur ${event.target}...`);
    return;
  }

  if (event.event === "stdout") {
    appendTerminalLine(event.line);
    return;
  }

  if (event.event === "stderr") {
    appendTerminalLine(`[${event.module_name}][stderr] ${event.line}`);
    return;
  }

  if (event.event === "error") {
    appendTerminalLine("");
    appendTerminalLine(`[${event.module_name || "scan"}][error] ${event.message}`);
    setStatus("error", `${event.module_name || "Le scan"} n'a pas pu etre termine.`);
    return;
  }

  if (event.event === "finish") {
    appendTerminalLine("");
    appendTerminalLine(`[${event.module_name}][done] code=${event.exit_code} duree=${event.duration_seconds}s`);
    setStatus(event.ok ? "success" : "error", `${event.module_name} termine sur ${event.target}.`, `${event.duration_seconds}s`);
    return {
      module_id: event.module_id,
      module_name: event.module_name,
      command: event.command,
      stdout: event.stdout || "",
      stderr: event.stderr || "",
      exit_code: event.exit_code,
      duration_seconds: event.duration_seconds,
      ok: event.ok,
    };
  }

  return null;
}

async function createSessionArtifact(target, modules, results) {
  const response = await fetch("/api/scans/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target, modules, results }),
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "Impossible de sauvegarder la session.");
  }
  return payload;
}

if (form) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const target = document.getElementById("target").value.trim();
    const selectedModules = getSelectedModules();

    if (!selectedModules.length) {
      resetTerminal();
      appendTerminalLine("[error] Veuillez cocher au moins un outil.");
      setStatus("error", "Aucun outil selectionne.");
      return;
    }

    setPendingState(true);
    resetTerminal();
    appendTerminalLine("$ preparation...");
    appendTerminalLine(`[queue] ${selectedModules.join(" -> ")}`);
    appendTerminalLine("");
    setStatus("running", "Preparation des scans...");

    try {
      const executionOrder = getExecutionOrder(selectedModules);
      const unsupportedModules = selectedModules.filter((moduleId) => !executionOrder.includes(moduleId));

      if (unsupportedModules.length) {
        throw new Error(`Outil non pris en charge par l'interface active: ${unsupportedModules.join(", ")}.`);
      }

      if (!executionOrder.length) {
        throw new Error("Aucun outil executable n'a ete trouve dans l'interface active.");
      }

      const sessionResults = [];
      for (const moduleId of executionOrder) {
        const result = await streamScan(moduleId, target, [], getModuleOptions(moduleId));
        sessionResults.push(result);
        appendTerminalLine("");
      }

      const session = await createSessionArtifact(target, executionOrder, sessionResults);
      appendTerminalLine(`[session][done] code=${session.exit_code} duree=${session.duration_seconds}s`);
      appendTerminalLine(`[session][files] JSON: ${session.json_artifact_url}`);
      appendTerminalLine(`[session][files] PDF : ${session.pdf_artifact_url}`);
      setStatus(session.ok ? "success" : "error", `Session terminee sur ${target}.`, `${session.duration_seconds}s`);
      loadHistory();
    } catch (error) {
      appendTerminalLine(`[error] ${error.message}`);
      setStatus("error", "Le scan n'a pas pu etre lance.");
    } finally {
      setPendingState(false);
    }
  });
}

if (refreshHistoryButton) {
  refreshHistoryButton.addEventListener("click", () => {
    loadHistory();
  });
}

if (themeToggleButton) {
  themeToggleButton.addEventListener("click", () => {
    const nextTheme = document.body.classList.contains("theme-dark") ? "theme-light" : "theme-dark";
    applyTheme(nextTheme);
  });
}

if (historySearchInput) {
  historySearchInput.addEventListener("input", () => {
    applyHistoryFilter();
  });
}

moduleCheckboxes.forEach((checkbox) => {
  checkbox.addEventListener("change", () => {
    toggleModuleConfigs();
  });
});

if (hydraPasswordSourceInput) {
  hydraPasswordSourceInput.addEventListener("change", () => {
    toggleHydraPasswordMode();
  });
}

if (hydraUsernameSourceInput) {
  hydraUsernameSourceInput.addEventListener("change", () => {
    toggleHydraUsernameMode();
  });
}

if (juiceShopButton) {
  juiceShopButton.addEventListener("click", () => {
    const targetInput = document.getElementById("target");
    targetInput.value = juiceShopButton.dataset.target || "";
    targetInput.focus();
  });
}

initializeTheme();

if (form) {
  toggleModuleConfigs();
  loadHistory();
}

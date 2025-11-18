const tg = window.Telegram?.WebApp;

const state = {
  documents: [],
  providers: [
    {
      id: "ollama",
      label: "Local Ollama",
      description: "Direct embeddings + chat via local runner.",
      status: "warn",
      statusLabel: "Manual setup",
      selected: false,
    },
    {
      id: "openai",
      label: "OpenAI Compatible",
      description: "HTTPS endpoint with OpenAI-style schema.",
      status: "ok",
      statusLabel: "Ready",
      selected: true,
    },
    {
      id: "azure",
      label: "Azure OpenAI",
      description: "Regional deployments with managed keys.",
      status: "warn",
      statusLabel: "Token required",
      selected: false,
    },
  ],
  prompt: "You are a precise assistant that references uploaded documents.",
  promptSaved: true,
  qdrant: {
    mode: "not_configured",
    url: "",
    collection: "tgrag-bot",
    status: null,
  },
};

let qdrantUI = null;
const numberFormatter = new Intl.NumberFormat();

function initTelegram() {
  if (!tg) return;
  tg.ready();
  tg.expand();
  const themeClass = tg.colorScheme === "dark" ? "tg-dark" : "tg-light";
  document.body.classList.add(themeClass);
}

function sanitizeInput(value) {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length ? trimmed : null;
}

async function fetchJson(url, options = {}) {
  const headers = { Accept: "application/json", ...(options.headers || {}) };
  if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "same-origin",
  });

  const raw = await response.text();
  let parsed = null;
  if (raw) {
    try {
      parsed = JSON.parse(raw);
    } catch {
      parsed = raw;
    }
  }

  if (!response.ok) {
    const detail =
      (parsed && typeof parsed === "object" && (parsed.detail || parsed.message)) ||
      (typeof parsed === "string" ? parsed : null) ||
      `Request failed (${response.status})`;
    throw new Error(detail);
  }

  return parsed;
}

function setButtonBusy(button, busyText, isBusy) {
  if (!button) return;
  if (isBusy) {
    if (!button.dataset.originalText) {
      button.dataset.originalText = button.textContent;
    }
    if (busyText) {
      button.textContent = busyText;
    }
    button.disabled = true;
    return;
  }

  if (button.dataset.originalText) {
    button.textContent = button.dataset.originalText;
  }
  button.disabled = false;
}

function defaultQdrantStatus(mode, collection) {
  return {
    mode,
    collection,
    reachable: false,
    collection_exists: false,
    points_count: null,
    vectors_count: null,
    last_error:
      mode === "disabled"
        ? "Qdrant is disabled."
        : "Qdrant credentials are not configured yet.",
  };
}

function normalizeQdrantStatus(status, mode, collection) {
  if (!status || typeof status !== "object") {
    return defaultQdrantStatus(mode, collection);
  }
  return {
    ...defaultQdrantStatus(mode, collection),
    ...status,
    mode: status.mode || mode,
    collection: status.collection || collection,
  };
}

function resolveQdrantBadge(mode, status) {
  if (mode === "disabled") {
    return { label: "Disabled", variant: "warn" };
  }
  if (status.reachable && status.collection_exists) {
    return { label: "Connected", variant: "ok" };
  }
  if (status.reachable && !status.collection_exists) {
    return { label: "Connected · no collection", variant: "warn" };
  }
  if (mode === "not_configured") {
    return { label: "Not configured", variant: "warn" };
  }
  if (status.last_error) {
    return { label: "Error", variant: "error" };
  }
  return { label: "Pending", variant: "warn" };
}

function describeConnection(status, mode) {
  if (mode === "disabled") {
    return "Disabled";
  }
  if (status.reachable && status.collection_exists) {
    return "Connected";
  }
  if (status.reachable) {
    return "Connected · create collection";
  }
  if (status.last_error) {
    return status.last_error;
  }
  if (mode === "not_configured") {
    return "Awaiting credentials";
  }
  return "No status yet";
}

function formatMetric(value) {
  if (typeof value !== "number") {
    return "–";
  }
  return numberFormatter.format(value);
}

function formatDateAgo(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
    return "–";
  }
  const diff = Date.now() - date.getTime();
  const minutes = Math.round(diff / 60000);
  if (minutes < 1) return "now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;
  const days = Math.round(hours / 24);
  return `${days} d ago`;
}

function formatFileSize(bytes) {
  if (typeof bytes !== "number" || Number.isNaN(bytes) || bytes < 0) {
    return "–";
  }
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  const units = ["KB", "MB", "GB", "TB"];
  let value = bytes / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  const formatted = value >= 10 ? Math.round(value) : value.toFixed(1);
  return `${formatted} ${units[unitIndex]}`;
}

function renderDocuments() {
  const list = document.getElementById("doc-table");
  const counter = document.getElementById("doc-count");

  counter.textContent = `${state.documents.length} ${
    state.documents.length === 1 ? "item" : "items"
  }`;

  if (!state.documents.length) {
    list.innerHTML = `
      <div class="empty-state">
        <span>✨</span>
        <p>No documents yet. Drop files to start building memory.</p>
      </div>
    `;
    return;
  }

  list.innerHTML = state.documents
    .map(
      (doc) => {
        const uploadedAt =
          doc.uploadedAt instanceof Date ? doc.uploadedAt : new Date(doc.uploadedAt);
        const uploadedLabel = formatDateAgo(uploadedAt);
        const sizeLabel = formatFileSize(doc.size);
        const indexedLabel = doc.indexed
          ? `Indexed${doc.chunks ? ` · ${doc.chunks} chunk${doc.chunks === 1 ? "" : "s"}` : ""}`
          : "Pending";
        return `
        <div class="table__row" role="row">
          <div class="table__cell" role="cell">
            <strong>${doc.name}</strong>
            <div class="table__meta">${sizeLabel}</div>
          </div>
          <div class="table__cell" role="cell">${uploadedLabel}</div>
          <div class="table__cell" role="cell">${indexedLabel}</div>
          <div class="table__cell table__cell--actions" role="cell">
            <button class="ghost-button" data-action="index" data-id="${doc.id}">
              ${doc.indexed ? "Reindex" : "Add to Index"}
            </button>
            <button class="ghost-button" data-action="unindex" data-id="${doc.id}">
              Remove
            </button>
            <button class="secondary-button" data-action="delete" data-id="${doc.id}">
              Delete
            </button>
          </div>
        </div>
      `;
      },
    )
    .join("");
}

function normalizeDocumentPayload(payload) {
  if (!payload) return null;
  return {
    id: payload.id,
    name: payload.name,
    size: payload.size ?? 0,
    uploadedAt: payload.uploaded_at ? new Date(payload.uploaded_at) : new Date(),
    indexed: Boolean(payload.indexed),
    chunks: payload.chunks ?? 0,
  };
}

function upsertDocument(document) {
  if (!document) return;
  const index = state.documents.findIndex((item) => item.id === document.id);
  if (index >= 0) {
    state.documents[index] = document;
    return;
  }
  state.documents.unshift(document);
}

async function loadDocuments({ silent = false } = {}) {
  const refreshBtn = document.getElementById("refresh-btn");
  setButtonBusy(refreshBtn, "Refreshing…", true);
  try {
    const data = await fetchJson("/api/documents");
    const items = Array.isArray(data?.items) ? data.items : [];
    state.documents = items
      .map(normalizeDocumentPayload)
      .filter(Boolean);
    renderDocuments();
    if (!silent) {
      showToast("Document list updated", "success");
    }
  } catch (error) {
    showToast(error.message || "Failed to load documents", "error");
  } finally {
    setButtonBusy(refreshBtn, "Refresh", false);
  }
}

async function uploadDocuments(files) {
  if (!files.length) return;
  const uploadBtn = document.getElementById("upload-btn");
  setButtonBusy(uploadBtn, "Uploading…", true);
  try {
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      const payload = await fetchJson("/api/documents", {
        method: "POST",
        body: formData,
      });
      const document = normalizeDocumentPayload(payload);
      upsertDocument(document);
    }
    renderDocuments();
    showToast(`${files.length} file(s) uploaded`, "success");
  } catch (error) {
    showToast(error.message || "Failed to upload documents", "error");
  } finally {
    setButtonBusy(uploadBtn, "Upload", false);
  }
}

async function handleDocumentAction(action, doc) {
  try {
    if (action === "index") {
      const payload = await fetchJson(`/api/documents/${doc.id}/index`, {
        method: "POST",
      });
      upsertDocument(normalizeDocumentPayload(payload));
      renderDocuments();
      showToast(`Document ${doc.name} scheduled for indexing`, "success");
      return;
    }
    if (action === "unindex") {
      const payload = await fetchJson(
        `/api/documents/${doc.id}/remove-from-index`,
        {
          method: "POST",
        },
      );
      upsertDocument(normalizeDocumentPayload(payload));
      renderDocuments();
      showToast(`Document ${doc.name} removed from index`, "info");
      return;
    }
    if (action === "delete") {
      await fetchJson(`/api/documents/${doc.id}`, { method: "DELETE" });
      state.documents = state.documents.filter((item) => item.id !== doc.id);
      renderDocuments();
      showToast(`Document ${doc.name} deleted`, "error");
      return;
    }
  } catch (error) {
    showToast(error.message || "Document action failed", "error");
  }
}

function renderPrompt() {
  const textarea = document.getElementById("prompt-editor");
  const counter = document.getElementById("prompt-counter");
  const status = document.getElementById("prompt-status");
  textarea.value = state.prompt;
  counter.textContent = `${state.prompt.length} / ${textarea.maxLength}`;
  status.textContent = state.promptSaved ? "Saved" : "Unsaved changes";
}

function renderProviders() {
  const container = document.getElementById("provider-list");
  const status = document.getElementById("provider-status");
  const active = state.providers.find((p) => p.selected);
  status.textContent = active
    ? `${active.label} selected`
    : "No provider selected";

  container.innerHTML = state.providers
    .map(
      (provider) => `
        <label class="provider-card">
          <input
            class="provider-input"
            type="radio"
            name="provider"
            value="${provider.id}"
            ${provider.selected ? "checked" : ""}
          />
          <div class="provider-card__meta">
            <strong>${provider.label}</strong>
            <p>${provider.description}</p>
          </div>
          <span class="status-pill status-pill--${provider.status}">
            ${provider.statusLabel}
          </span>
        </label>
      `,
    )
    .join("");
}

function applyQdrantResponse(payload) {
  if (!payload) return;
  state.qdrant.mode = payload.mode || state.qdrant.mode;
  state.qdrant.url = payload.url || "";
  state.qdrant.collection = payload.collection || state.qdrant.collection;
  state.qdrant.status = payload.status || state.qdrant.status;
  renderQdrantPanel();
}

function renderQdrantPanel() {
  if (!qdrantUI) return;
  const { mode, url, collection } = state.qdrant;
  const status = normalizeQdrantStatus(state.qdrant.status, mode, collection);

  qdrantUI.modeInputs.forEach((input) => {
    input.checked = input.value === mode;
  });

  qdrantUI.url.value = url || "";
  qdrantUI.collection.value = collection || "";
  qdrantUI.url.disabled = mode === "disabled";
  qdrantUI.collection.disabled = mode === "disabled";
  qdrantUI.apiKey.disabled = mode !== "cloud";

  const { label, variant } = resolveQdrantBadge(mode, status);
  qdrantUI.statusLabel.textContent = label;
  qdrantUI.statusLabel.classList.remove(
    "status-pill--ok",
    "status-pill--warn",
    "status-pill--error",
  );
  qdrantUI.statusLabel.classList.add(`status-pill--${variant}`);
  const connectionText = describeConnection(status, mode);
  qdrantUI.connection.textContent = connectionText;
  qdrantUI.connection.title = status.last_error || connectionText;
  qdrantUI.statusLabel.title = status.last_error || "";
  qdrantUI.points.textContent = formatMetric(status.points_count);
  qdrantUI.vectors.textContent = formatMetric(status.vectors_count);
}

async function loadQdrantSettings({ silent = true } = {}) {
  if (!qdrantUI) return;
  setButtonBusy(qdrantUI.refresh, "Loading…", true);
  qdrantUI.saveButton.disabled = true;
  try {
    const response = await fetchJson("/api/settings/qdrant");
    applyQdrantResponse(response);
    if (!silent) {
      showToast("Qdrant settings synced", "success");
    }
  } catch (error) {
    showToast(error.message || "Failed to load Qdrant settings", "error");
  } finally {
    setButtonBusy(qdrantUI.refresh, "Check status", false);
    qdrantUI.saveButton.disabled = false;
    qdrantUI.apiKey.value = "";
  }
}

async function refreshQdrantStatus(notify = false) {
  if (!qdrantUI) return;
  setButtonBusy(qdrantUI.refresh, "Checking…", true);
  try {
    const status = await fetchJson("/qdrant/status");
    if (status) {
      state.qdrant.status = status;
      state.qdrant.mode = status.mode || state.qdrant.mode;
      state.qdrant.collection = status.collection || state.qdrant.collection;
    }
    renderQdrantPanel();
    if (notify) {
      showToast("Qdrant status refreshed", "success");
    }
  } catch (error) {
    showToast(error.message || "Failed to refresh status", "error");
  } finally {
    setButtonBusy(qdrantUI.refresh, "Check status", false);
  }
}

async function handleQdrantSubmit(event) {
  event.preventDefault();
  if (!qdrantUI) return;
  const formData = new FormData(qdrantUI.form);
  const payload = {
    mode: formData.get("mode") || state.qdrant.mode,
    url: sanitizeInput(formData.get("url")),
    collection: sanitizeInput(formData.get("collection")) || state.qdrant.collection,
  };
  const apiKeyValue = sanitizeInput(formData.get("api_key"));
  if (apiKeyValue) {
    payload.api_key = apiKeyValue;
  }

  try {
    setButtonBusy(qdrantUI.saveButton, "Saving…", true);
    const response = await fetchJson("/api/settings/qdrant", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    applyQdrantResponse(response);
    showToast("Qdrant settings saved", "success");
  } catch (error) {
    showToast(error.message || "Failed to save Qdrant settings", "error");
  } finally {
    setButtonBusy(qdrantUI.saveButton, "Save settings", false);
    qdrantUI.apiKey.value = "";
  }
}

function initQdrantPanel() {
  const form = document.getElementById("qdrant-form");
  if (!form) return;
  qdrantUI = {
    form,
    statusLabel: document.getElementById("qdrant-status-label"),
    modeInputs: Array.from(form.querySelectorAll('input[name="mode"]')),
    url: document.getElementById("qdrant-url"),
    collection: document.getElementById("qdrant-collection"),
    apiKey: document.getElementById("qdrant-key"),
    connection: document.getElementById("qdrant-connection"),
    points: document.getElementById("qdrant-points"),
    vectors: document.getElementById("qdrant-vectors"),
    refresh: document.getElementById("qdrant-refresh"),
    saveButton: document.getElementById("qdrant-save"),
  };

  qdrantUI.form.addEventListener("submit", handleQdrantSubmit);
  qdrantUI.refresh.addEventListener("click", () => refreshQdrantStatus(true));
  qdrantUI.modeInputs.forEach((input) => {
    input.addEventListener("change", (event) => {
      if (event.target.checked) {
        state.qdrant.mode = event.target.value;
        renderQdrantPanel();
      }
    });
  });
  qdrantUI.url.addEventListener("input", (event) => {
    state.qdrant.url = event.target.value;
  });
  qdrantUI.collection.addEventListener("input", (event) => {
    state.qdrant.collection = event.target.value;
  });

  renderQdrantPanel();
  loadQdrantSettings({ silent: true });
}

function showToast(message, variant = "info") {
  const root = document.getElementById("toast-root");
  const toast = document.createElement("div");
  toast.className = `toast toast--${variant}`;
  toast.textContent = message;
  root.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("toast--exit");
    setTimeout(() => toast.remove(), 250);
  }, 2600);
}

function attachHandlers() {
  const fileInput = document.getElementById("file-input");
  const uploadBtn = document.getElementById("upload-btn");
  const refreshBtn = document.getElementById("refresh-btn");
  const dropzone = document.getElementById("dropzone");
  const docTable = document.getElementById("doc-table");
  const promptEditor = document.getElementById("prompt-editor");
  const savePrompt = document.getElementById("save-prompt");
  const resetPrompt = document.getElementById("reset-prompt");
  const providerList = document.getElementById("provider-list");
  const addProvider = document.getElementById("add-provider");
  const modal = document.getElementById("provider-modal");
  const closeModal = document.getElementById("close-modal");

  uploadBtn.addEventListener("click", () => fileInput.click());
  refreshBtn.addEventListener("click", () => {
    loadDocuments({ silent: false });
  });

  fileInput.addEventListener("change", (event) => {
    const files = Array.from(event.target.files ?? []);
    if (!files.length) return;
    uploadDocuments(files).finally(() => {
      fileInput.value = "";
    });
  });

  docTable.addEventListener("click", (event) => {
    const target = event.target.closest("button");
    if (!target) return;
    const { action, id } = target.dataset;
    const doc = state.documents.find((item) => item.id === id);
    if (!doc) return;

    handleDocumentAction(action, doc);
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (event) => {
    const files = Array.from(event.dataTransfer?.files ?? []);
    if (!files.length) return;
    uploadDocuments(files);
  });

  promptEditor.addEventListener("input", (event) => {
    state.prompt = event.target.value;
    state.promptSaved = false;
    renderPrompt();
  });

  savePrompt.addEventListener("click", () => {
    state.promptSaved = true;
    renderPrompt();
    showToast("Prompt saved (stub)", "success");
  });

  resetPrompt.addEventListener("click", () => {
    state.prompt = "You are a precise assistant that references uploaded documents.";
    state.promptSaved = true;
    renderPrompt();
    showToast("Prompt reset", "info");
  });

  providerList.addEventListener("change", (event) => {
    if (event.target.name !== "provider") return;
    const next = event.target.value;
    state.providers = state.providers.map((provider) => ({
      ...provider,
      selected: provider.id === next,
    }));
    renderProviders();
    showToast(`Switched to ${next}`, "info");
  });

  addProvider.addEventListener("click", () => {
    modal.showModal();
  });

  closeModal.addEventListener("click", () => modal.close());

  modal.addEventListener("close", () => {
    if (modal.returnValue === "confirm") {
      showToast("Provider saved (stub)", "success");
    }
  });
}

function bootstrap() {
  initTelegram();
  attachHandlers();
  initQdrantPanel();
  renderDocuments();
  renderPrompt();
  renderProviders();
  loadDocuments({ silent: true });
}

document.addEventListener("DOMContentLoaded", bootstrap);

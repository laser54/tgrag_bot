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
};

function initTelegram() {
  if (!tg) return;
  tg.ready();
  tg.expand();
  const themeClass = tg.colorScheme === "dark" ? "tg-dark" : "tg-light";
  document.body.classList.add(themeClass);
}

function formatDateAgo(date) {
  const diff = Date.now() - date.getTime();
  const minutes = Math.round(diff / 60000);
  if (minutes < 1) return "now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;
  const days = Math.round(hours / 24);
  return `${days} d ago`;
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
      (doc) => `
        <div class="table__row" role="row">
          <div class="table__cell" role="cell">
            <strong>${doc.name}</strong>
            <div class="table__meta">${doc.size}</div>
          </div>
          <div class="table__cell" role="cell">${formatDateAgo(doc.uploadedAt)}</div>
          <div class="table__cell" role="cell">${
            doc.indexed ? "Indexed" : "Pending"
          }</div>
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
      `,
    )
    .join("");
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
    showToast("Refreshing document list (stub)", "info");
  });

  fileInput.addEventListener("change", (event) => {
    const files = Array.from(event.target.files ?? []);
    if (!files.length) return;
    files.forEach((file) => {
      state.documents.unshift({
        id: crypto.randomUUID(),
        name: file.name,
        size: `${Math.round(file.size / 1024)} KB`,
        uploadedAt: new Date(),
        indexed: false,
      });
    });
    renderDocuments();
    showToast(`${files.length} file(s) queued for upload`, "success");
    fileInput.value = "";
  });

  docTable.addEventListener("click", (event) => {
    const target = event.target.closest("button");
    if (!target) return;
    const { action, id } = target.dataset;
    const doc = state.documents.find((item) => item.id === id);
    if (!doc) return;

    if (action === "index") {
      doc.indexed = true;
      showToast(`Document ${doc.name} scheduled for indexing`, "success");
    }
    if (action === "unindex") {
      doc.indexed = false;
      showToast(`Document ${doc.name} removed from index`, "info");
    }
    if (action === "delete") {
      state.documents = state.documents.filter((item) => item.id !== id);
      showToast(`Document ${doc.name} deleted`, "error");
    }
    renderDocuments();
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
    files.forEach((file) => {
      state.documents.unshift({
        id: crypto.randomUUID(),
        name: file.name,
        size: `${Math.round(file.size / 1024)} KB`,
        uploadedAt: new Date(),
        indexed: false,
      });
    });
    renderDocuments();
    showToast(`${files.length} file(s) queued`, "success");
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
  renderDocuments();
  renderPrompt();
  renderProviders();
}

document.addEventListener("DOMContentLoaded", bootstrap);

const API_ENDPOINT = "/api/rag/answer";

const chatWidget = document.querySelector("#chatWidget");
const chatBody = document.querySelector("#chatBody");
const chatForm = document.querySelector("#chatForm");
const questionInput = document.querySelector("#questionInput");
const chatLauncher = document.querySelector("#chatLauncher");
const backendStatus = document.querySelector("#backendStatus");
const detailsDialog = document.querySelector("#detailsDialog");
const detailsContent = document.querySelector("#detailsContent");

chatLauncher.addEventListener("click", openChat);
document.querySelector("#openChatHero").addEventListener("click", openChat);
document.querySelector("#openChatBand").addEventListener("click", openChat);
document.querySelector("#closeChat").addEventListener("click", closeChat);
document.querySelector("#closeDetails").addEventListener("click", () => detailsDialog.close());

checkBackend();

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  appendMessage("user", question);
  questionInput.value = "";
  setFormDisabled(true);
  const pending = appendMessage("assistant", "Recherche des preuves et generation de la reponse...");

  try {
    const response = await askRag(question);
    pending.remove();
    appendAssistantResponse(response);
  } catch (error) {
    pending.remove();
    appendError(error);
  } finally {
    setFormDisabled(false);
    questionInput.focus();
  }
});

function openChat() {
  chatWidget.classList.add("open");
  chatWidget.setAttribute("aria-hidden", "false");
  chatLauncher.hidden = true;
  questionInput.focus();
}

function closeChat() {
  chatWidget.classList.remove("open");
  chatWidget.setAttribute("aria-hidden", "true");
  chatLauncher.hidden = false;
}

function setFormDisabled(disabled) {
  questionInput.disabled = disabled;
  chatForm.querySelector("button").disabled = disabled;
}

function appendMessage(type, text) {
  const article = document.createElement("article");
  article.className = `message ${type}`;
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  article.appendChild(paragraph);
  chatBody.appendChild(article);
  scrollChatToEnd();
  return article;
}

function appendAssistantResponse(rawResponse) {
  const response = normalizeRagResponse(rawResponse);
  const article = document.createElement("article");
  article.className = `message assistant ${response.refused ? "is-refused" : ""}`;

  const answer = document.createElement("p");
  answer.className = "answer-text";
  answer.textContent = response.answer || "Le backend n'a retourne aucune reponse textuelle.";
  article.appendChild(answer);

  if (response.citations.length) {
    const citations = document.createElement("div");
    citations.className = "citation-list";
    response.citations.slice(0, 4).forEach((citation) => {
      const chip = document.createElement("button");
      chip.className = "citation-chip";
      chip.type = "button";
      chip.textContent = formatCitation(citation);
      chip.addEventListener("click", () => openDetails(response));
      citations.appendChild(chip);
    });
    article.appendChild(citations);
  }

  const tools = document.createElement("div");
  tools.className = "message-tools";

  const detailsButton = document.createElement("button");
  detailsButton.className = "details-button";
  detailsButton.type = "button";
  detailsButton.textContent = "Voir les preuves";
  detailsButton.addEventListener("click", () => openDetails(response));

  const meta = document.createElement("span");
  meta.className = "meta-line";
  meta.textContent = `Confiance: ${response.confidence || "n/a"} | preuves: ${response.evidence.length}`;

  tools.append(detailsButton, meta);
  article.appendChild(tools);
  chatBody.appendChild(article);
  scrollChatToEnd();
}

function appendError(error) {
  backendStatus.textContent = "Backend indisponible";
  backendStatus.classList.add("is-error");

  const article = document.createElement("article");
  article.className = "message assistant error-message";

  const title = document.createElement("strong");
  title.textContent = "La reponse RAG n'a pas pu etre recuperee.";

  const detail = document.createElement("p");
  detail.textContent = error.message || "Erreur inconnue.";

  article.append(title, detail);
  chatBody.appendChild(article);
  scrollChatToEnd();
}

async function askRag(question) {
  const payload = buildRagPayload(question);
  const result = await fetch(API_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const body = await readJson(result);
  if (!result.ok) {
    throw new Error(formatBackendError(result.status, body));
  }

  backendStatus.textContent = "Backend connecte";
  backendStatus.classList.remove("is-error");
  return body;
}

function buildRagPayload(question) {
  return { question };
}

async function checkBackend() {
  try {
    const result = await fetch("/api/health");
    backendStatus.textContent = result.ok ? "Backend connecte" : "Backend non verifie";
    backendStatus.classList.toggle("is-error", !result.ok);
  } catch {
    backendStatus.textContent = "Backend indisponible";
    backendStatus.classList.add("is-error");
  }
}

function openDetails(response) {
  const evidence = response.evidence || [];
  const citations = response.citations || [];
  detailsContent.innerHTML = "";

  const stats = document.createElement("div");
  stats.className = "details-grid";
  stats.append(
    statBlock("Request ID", response.request_id || "n/a"),
    statBlock("Confiance", response.confidence || "n/a"),
    statBlock("Refus", response.refused ? "oui" : "non"),
    statBlock("Citations", String(citations.length))
  );

  const citationList = document.createElement("div");
  citationList.className = "evidence-list";
  citations.forEach((citation, index) => {
    const node = document.createElement("article");
    node.className = "evidence-item";
    node.innerHTML = `
      <span>Citation ${index + 1}</span>
      <strong>${escapeHtml(formatCitation(citation))}</strong>
      ${citation.quote ? `<p>${escapeHtml(citation.quote)}</p>` : ""}
      <code>${escapeHtml(citation.chunk_id || citation.document_id || "")}</code>
    `;
    citationList.appendChild(node);
  });

  const evidenceList = document.createElement("div");
  evidenceList.className = "evidence-list";
  evidence.forEach((item, index) => {
    const chunk = item.chunk || {};
    const metadata = chunk.metadata || {};
    const node = document.createElement("article");
    node.className = "evidence-item";
    node.innerHTML = `
      <span>Preuve ${index + 1}</span>
      <strong>${escapeHtml(metadata.citation_label || metadata.document_title || chunk.document_title || "Source")}</strong>
      <p>${escapeHtml((chunk.text || "").slice(0, 700))}</p>
      <code>retrieval: ${formatScore(item.score)} | rerank: ${formatScore(item.rerank_score)} | ${escapeHtml(
        chunk.chunk_id || ""
      )}</code>
    `;
    evidenceList.appendChild(node);
  });

  detailsContent.append(stats);
  if (citations.length) {
    detailsContent.append(sectionTitle("Citations"), citationList);
  }
  if (evidence.length) {
    detailsContent.append(sectionTitle("Passages recuperes"), evidenceList);
  }
  if (!citations.length && !evidence.length) {
    const empty = document.createElement("p");
    empty.className = "empty-details";
    empty.textContent = "Aucune preuve detaillee n'a ete retournee par le backend.";
    detailsContent.appendChild(empty);
  }
  detailsDialog.showModal();
}

function normalizeRagResponse(response) {
  return {
    answer: response?.answer || "",
    citations: Array.isArray(response?.citations) ? response.citations : [],
    evidence: Array.isArray(response?.evidence) ? response.evidence : [],
    confidence: response?.confidence || "n/a",
    refused: Boolean(response?.refused),
    request_id: response?.request_id || "n/a",
  };
}

function sectionTitle(text) {
  const title = document.createElement("h3");
  title.className = "details-section-title";
  title.textContent = text;
  return title;
}

function statBlock(label, value) {
  const node = document.createElement("div");
  node.className = "detail-stat";
  node.innerHTML = `<span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong>`;
  return node;
}

function formatCitation(citation) {
  const parts = [
    citation.document_title,
    citation.article,
    citation.section,
    citation.page ? `p. ${citation.page}` : null,
  ];
  return parts.filter(Boolean).join(" | ") || citation.document_id || "Source";
}

function formatBackendError(status, body) {
  const detail = typeof body?.detail === "string" ? body.detail : "Erreur backend sans detail.";
  return `HTTP ${status}: ${detail}`;
}

async function readJson(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { detail: text };
  }
}

function formatScore(value) {
  return typeof value === "number" ? value.toFixed(3) : "n/a";
}

function scrollChatToEnd() {
  chatBody.scrollTop = chatBody.scrollHeight;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

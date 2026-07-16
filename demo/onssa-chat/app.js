const API_ENDPOINT = "/api/rag/answer";

const sampleResponse = {
  answer:
    "La base reglementaire de la securite sanitaire des produits alimentaires est etablie par la loi n°28-07 relative a la securite sanitaire des produits alimentaires, promulguee par le dahir n°1-10-08 du 26 safar 1431 (11 fevrier 2010).\n\nSelon l'article 5, les produits primaires, les produits alimentaires et les aliments pour animaux doivent etre produits, manipules, traites, transformes, emballes, transportes, entreposes et mis en vente dans des conditions d'hygiene et de salubrite propres a preserver leur qualite et a garantir leur securite sanitaire.\n\nLe decret n°2-10-473 du 7 chaoual 1432 (6 septembre 2011) precise les mesures d'application de la loi n°28-07, notamment les autorisations, les agrements sanitaires, les conditions d'hygiene, l'autocontrole et la tracabilite.",
  citations: [
    {
      document_id: "onssa-pdf-aabcbe4f861b8483",
      document_title: "LOI 28-07 FR",
      source_file: "data/raw/pdfs/onssa/LOI_28-07_FR.pdf",
      page: 4,
      article: "Article 5",
      section: null,
      chunk_id: "chunk-468a590d583ddf4ed482aa18",
      quote:
        "Article 5 Afin qu'aucun produit primaire ni produit alimentaire ne constitue un danger...",
    },
    {
      document_id: "onssa-pdf-da0be16b7fa0fd13",
      document_title: "DEC 2-10-473 FR",
      source_file: "data/raw/pdfs/onssa/DEC_2-10-473_FR.pdf",
      page: 1,
      article: null,
      section: "TITRE PREMIER",
      chunk_id: "chunk-2dc9b1bb09ff0e5e6d7f3087",
      quote:
        "Le present decret fixe les mesures permettant de preserver la qualite et de garantir la securite sanitaire...",
    },
  ],
  evidence: [
    {
      chunk: {
        chunk_id: "chunk-468a590d583ddf4ed482aa18",
        text:
          "Article 5 Afin qu'aucun produit primaire ni produit alimentaire ni un aliment pour animaux ne constitue un danger pour la vie ou la sante humaine ou animale...",
        metadata: {
          vertical: "regulation",
          domain: "reglementation_transversale",
          subdomain: "securite_sanitaire",
          document_title: "LOI 28-07 FR",
          page_start: 4,
          page_end: 5,
          article: "Article 5",
          citation_label: "LOI 28-07 FR, Article 5, pp. 4-5",
        },
      },
      score: 0.5977447,
      rerank_score: 0.6781114936,
    },
    {
      chunk: {
        chunk_id: "chunk-2dc9b1bb09ff0e5e6d7f3087",
        text:
          "Conformement aux dispositions de l'article 5 de la loi n°28-07, le present decret fixe les mesures permettant de preserver la qualite...",
        metadata: {
          vertical: "regulation",
          domain: "reglementation_transversale",
          subdomain: "securite_sanitaire",
          document_title: "DEC 2-10-473 FR",
          page_start: 1,
          page_end: 3,
          section: "TITRE PREMIER",
          citation_label: "DEC 2-10-473 FR, TITRE PREMIER, pp. 1-3",
        },
      },
      score: 0.61228883,
      rerank_score: 0.792271316,
    },
  ],
  confidence: "sufficient",
  refused: false,
  request_id: "demo-response",
};

const chatWidget = document.querySelector("#chatWidget");
const chatBody = document.querySelector("#chatBody");
const chatForm = document.querySelector("#chatForm");
const questionInput = document.querySelector("#questionInput");
const backendStatus = document.querySelector("#backendStatus");
const detailsDialog = document.querySelector("#detailsDialog");
const detailsContent = document.querySelector("#detailsContent");

document.querySelector("#chatLauncher").addEventListener("click", openChat);
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
  const pending = appendMessage("assistant", "Recherche des preuves dans Qdrant...");

  const response = await askRag(question);
  pending.remove();
  appendAssistantResponse(response);
});

function openChat() {
  chatWidget.classList.add("open");
  chatWidget.setAttribute("aria-hidden", "false");
  questionInput.focus();
}

function closeChat() {
  chatWidget.classList.remove("open");
  chatWidget.setAttribute("aria-hidden", "true");
}

function appendMessage(type, text) {
  const article = document.createElement("article");
  article.className = `message ${type}`;
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  article.appendChild(paragraph);
  chatBody.appendChild(article);
  chatBody.scrollTop = chatBody.scrollHeight;
  return article;
}

function appendAssistantResponse(response) {
  const article = document.createElement("article");
  article.className = "message assistant";

  const answer = document.createElement("p");
  answer.className = "answer-text";
  answer.textContent = response.answer;
  article.appendChild(answer);

  if (response.citations?.length) {
    const citations = document.createElement("div");
    citations.className = "citation-list";
    response.citations.slice(0, 3).forEach((citation) => {
      const chip = document.createElement("div");
      chip.className = "citation-chip";
      chip.textContent = formatCitation(citation);
      citations.appendChild(chip);
    });
    article.appendChild(citations);
  }

  const tools = document.createElement("div");
  tools.className = "message-tools";

  const detailsButton = document.createElement("button");
  detailsButton.className = "details-button";
  detailsButton.type = "button";
  detailsButton.textContent = "Voir details";
  detailsButton.addEventListener("click", () => openDetails(response));

  const meta = document.createElement("span");
  meta.className = "meta-line";
  meta.textContent = `Confiance: ${response.confidence || "n/a"} · preuves: ${
    response.evidence?.length || 0
  }`;

  tools.append(detailsButton, meta);
  article.appendChild(tools);
  chatBody.appendChild(article);
  chatBody.scrollTop = chatBody.scrollHeight;
}

async function askRag(question) {
  try {
    const result = await fetch(API_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!result.ok) {
      throw new Error(`Backend HTTP ${result.status}`);
    }
    backendStatus.textContent = "Backend connecte";
    return await result.json();
  } catch (error) {
    backendStatus.textContent = "Mode exemple";
    return {
      ...sampleResponse,
      request_id: `sample-${Date.now()}`,
      answer: `${sampleResponse.answer}\n\n[Mode exemple: le backend FastAPI n'a pas repondu depuis cette page.]`,
    };
  }
}

async function checkBackend() {
  try {
    const result = await fetch("/api/health");
    backendStatus.textContent = result.ok ? "Backend connecte" : "Backend non verifie";
  } catch {
    backendStatus.textContent = "Mode exemple";
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

  const list = document.createElement("div");
  list.className = "evidence-list";
  evidence.forEach((item, index) => {
    const metadata = item.chunk?.metadata || {};
    const node = document.createElement("article");
    node.className = "evidence-item";
    node.innerHTML = `
      <span>Preuve ${index + 1}</span>
      <strong>${escapeHtml(metadata.citation_label || metadata.document_title || "Source")}</strong>
      <p>${escapeHtml((item.chunk?.text || "").slice(0, 520))}</p>
      <code>retrieval: ${formatScore(item.score)} · rerank: ${formatScore(
        item.rerank_score
      )} · ${escapeHtml(item.chunk?.chunk_id || "")}</code>
    `;
    list.appendChild(node);
  });

  detailsContent.append(stats, list);
  detailsDialog.showModal();
}

function statBlock(label, value) {
  const node = document.createElement("div");
  node.className = "detail-stat";
  node.innerHTML = `<span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong>`;
  return node;
}

function formatCitation(citation) {
  const parts = [citation.document_title, citation.article, citation.section, citation.page && `p. ${citation.page}`];
  return parts.filter(Boolean).join(" · ");
}

function formatScore(value) {
  return typeof value === "number" ? value.toFixed(3) : "n/a";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

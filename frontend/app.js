const form = document.getElementById("analyze-form");
const repoInput = document.getElementById("repo-url");
const apiKeyInput = document.getElementById("api-key");
const modelInput = document.getElementById("model");
const statusMessage = document.getElementById("status-message");
const repoInfo = document.getElementById("repo-info");
const analysisContent = document.getElementById("analysis-content");
const downloadButton = document.getElementById("download-pdf");
const presentationButton = document.getElementById("start-presentation");
const aiStatus = document.getElementById("ai-status");
const submitButton = document.getElementById("submit-btn");

const overlay = document.getElementById("presentation-overlay");
const closeOverlayButton = document.getElementById("close-presentation");
const prevSlideButton = document.getElementById("prev-slide");
const nextSlideButton = document.getElementById("next-slide");
const presentationTitle = document.getElementById("presentation-title");
const presentationText = document.getElementById("presentation-text");
const presentationList = document.getElementById("presentation-list");
const presentationProgress = document.getElementById("presentation-progress");

let latestAnalysis = null;
let latestRepository = null;
let slides = [];
let currentSlideIndex = 0;

const formatDate = (value) => {
  if (!value) return "Date unavailable";
  const date = new Date(value);
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};

const createElement = (tag, className, text) => {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
};

const renderRepositoryInfo = (repository) => {
  repoInfo.classList.remove("empty");
  repoInfo.innerHTML = "";

  const title = createElement("h3", null, repository.full_name || repository.name);
  repoInfo.appendChild(title);

  const description = createElement(
    "p",
    null,
    repository.description || "No project description provided on GitHub."
  );
  repoInfo.appendChild(description);

  const stats = createElement("div", "list-grid");
  stats.innerHTML = `
    <p><strong>Stars:</strong> ${repository.stars}</p>
    <p><strong>Forks:</strong> ${repository.forks}</p>
    <p><strong>Open issues:</strong> ${repository.open_issues}</p>
    <p><strong>Watchers:</strong> ${repository.watchers}</p>
  `;
  repoInfo.appendChild(stats);

  if (repository.topics?.length) {
    const topics = createElement("p");
    topics.innerHTML = `<strong>Topics:</strong> ${repository.topics.join(", ")}`;
    repoInfo.appendChild(topics);
  }

  const languagesContainer = createElement("div");
  languagesContainer.innerHTML = `<strong>Languages:</strong>`;
  if (repository.languages && Object.keys(repository.languages).length > 0) {
    const wrapper = createElement("div");
    Object.entries(repository.languages).forEach(([name, score]) => {
      const chip = createElement(
        "span",
        "language-chip",
        `${name} · ${score.toLocaleString()}`
      );
      wrapper.appendChild(chip);
    });
    languagesContainer.appendChild(wrapper);
  } else {
    languagesContainer.append(" Unknown");
  }
  repoInfo.appendChild(languagesContainer);

  if (repository.readme_excerpt) {
    const readmeSection = createElement("div");
    readmeSection.innerHTML = "<h3>README highlight</h3>";
    const readmeText = createElement("p");
    const excerpt = repository.readme_excerpt.slice(0, 600);
    readmeText.textContent = excerpt + (repository.readme_excerpt.length > 600 ? "…" : "");
    readmeSection.appendChild(readmeText);
    repoInfo.appendChild(readmeSection);
  }

  if (repository.recent_commits?.length) {
    const commitSection = createElement("div");
    commitSection.innerHTML = "<h3>Recent commits</h3>";
    const list = createElement("ul", "commit-list");
    repository.recent_commits.forEach((commit) => {
      const item = createElement("li");
      const message = createElement("span", null, commit.message || "No commit message");
      const date = createElement("span", "commit-date", formatDate(commit.date));
      item.appendChild(message);
      item.appendChild(date);
      list.appendChild(item);
    });
    commitSection.appendChild(list);
    repoInfo.appendChild(commitSection);
  }

  const link = createElement("a");
  link.href = repository.html_url;
  link.target = "_blank";
  link.rel = "noopener";
  link.textContent = "View on GitHub";
  repoInfo.appendChild(link);
};

const renderAnalysis = (analysis) => {
  analysisContent.classList.remove("empty");
  analysisContent.innerHTML = "";

  const addParagraph = (title, text) => {
    if (!text) return;
    const container = createElement("div");
    container.appendChild(createElement("h3", null, title));
    container.appendChild(createElement("p", null, text));
    analysisContent.appendChild(container);
  };

  const addList = (title, items) => {
    if (!items || items.length === 0) return;
    const container = createElement("div");
    container.appendChild(createElement("h3", null, title));
    const list = createElement("ul");
    items.forEach((item) => {
      const li = createElement("li");
      li.textContent = item;
      list.appendChild(li);
    });
    container.appendChild(list);
    analysisContent.appendChild(container);
  };

  addParagraph("Project summary", analysis.project_summary);
  addParagraph("How it helps people", analysis.how_it_helps_people);
  addList("Main features", analysis.main_features);
  addList("How it works", analysis.how_it_works);
  addList("Tech explained simply", analysis.tech_stack);
  addList("Getting started", analysis.getting_started);
  addList("Next steps", analysis.next_steps);

  if (analysis.glossary?.length) {
    const container = createElement("div");
    container.appendChild(createElement("h3", null, "Glossary"));
    const list = createElement("ul", "glossary-list");
    analysis.glossary.forEach((entry) => {
      const item = createElement("li");
      item.innerHTML = `<span class="glossary-term">${entry.term}:</span> ${entry.definition}`;
      list.appendChild(item);
    });
    container.appendChild(list);
    analysisContent.appendChild(container);
  }
};

const updateStatusBadge = (usedAI) => {
  if (usedAI) {
    aiStatus.textContent = "AI-generated";
    aiStatus.className = "badge badge--success";
  } else {
    aiStatus.textContent = "Using quick fallback";
    aiStatus.className = "badge badge--warning";
  }
};

const buildSlides = (analysis) => {
  const slides = [];
  slides.push({ title: "Project summary", type: "text", content: analysis.project_summary });
  slides.push({
    title: "Why it matters",
    type: "text",
    content: analysis.how_it_helps_people,
  });
  if (analysis.main_features?.length) {
    slides.push({ title: "Main features", type: "list", items: analysis.main_features });
  }
  if (analysis.how_it_works?.length) {
    slides.push({ title: "How it works", type: "list", items: analysis.how_it_works });
  }
  if (analysis.tech_stack?.length) {
    slides.push({ title: "Tech explained", type: "list", items: analysis.tech_stack });
  }
  if (analysis.getting_started?.length) {
    slides.push({ title: "Getting started", type: "list", items: analysis.getting_started });
  }
  if (analysis.next_steps?.length) {
    slides.push({ title: "Next steps", type: "list", items: analysis.next_steps });
  }
  if (analysis.glossary?.length) {
    const glossaryItems = analysis.glossary.map((entry) => `${entry.term}: ${entry.definition}`);
    slides.push({ title: "Glossary", type: "list", items: glossaryItems });
  }
  return slides;
};

const showSlide = (index) => {
  const slide = slides[index];
  presentationTitle.textContent = slide.title;
  presentationText.textContent = "";
  presentationList.innerHTML = "";

  if (slide.type === "text") {
    presentationText.textContent = slide.content;
  } else if (slide.type === "list") {
    slide.items.forEach((item) => {
      const li = createElement("li");
      li.textContent = item;
      presentationList.appendChild(li);
    });
  }

  presentationProgress.textContent = `${index + 1} / ${slides.length}`;
  prevSlideButton.disabled = index === 0;
  nextSlideButton.textContent = index === slides.length - 1 ? "Finish" : "Next";
};

const openPresentation = () => {
  if (!slides.length) return;
  overlay.classList.remove("hidden");
  overlay.setAttribute("aria-hidden", "false");
  currentSlideIndex = 0;
  showSlide(currentSlideIndex);
};

const closePresentation = () => {
  overlay.classList.add("hidden");
  overlay.setAttribute("aria-hidden", "true");
};

prevSlideButton.addEventListener("click", () => {
  if (currentSlideIndex === 0) return;
  currentSlideIndex -= 1;
  showSlide(currentSlideIndex);
});

nextSlideButton.addEventListener("click", () => {
  if (currentSlideIndex >= slides.length - 1) {
    closePresentation();
    return;
  }
  currentSlideIndex += 1;
  showSlide(currentSlideIndex);
});

closeOverlayButton.addEventListener("click", closePresentation);

presentationButton.addEventListener("click", openPresentation);

downloadButton.addEventListener("click", async () => {
  if (!latestAnalysis || !latestRepository) return;
  downloadButton.disabled = true;
  downloadButton.textContent = "Preparing...";
  try {
    const response = await fetch("/api/generate-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        repo_name: latestRepository.full_name || latestRepository.name || "repository",
        analysis: latestAnalysis,
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to create PDF");
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${latestRepository.name || "repository"}-gitalyzer.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    statusMessage.textContent = error.message;
  } finally {
    downloadButton.disabled = false;
    downloadButton.textContent = "Download PDF";
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const repoUrl = repoInput.value.trim();
  const apiKey = apiKeyInput.value.trim();
  const model = modelInput.value.trim();

  if (!repoUrl) {
    statusMessage.textContent = "Please paste a GitHub repository URL.";
    return;
  }

  statusMessage.textContent = "Fetching repository details...";
  submitButton.disabled = true;
  aiStatus.textContent = "Working...";
  aiStatus.className = "badge badge--neutral";
  analysisContent.classList.add("empty");
  analysisContent.innerHTML = "<p>Waiting for the AI to finish...</p>";

  try {
    const payload = { repo_url: repoUrl };
    if (apiKey) payload.api_key = apiKey;
    if (model) payload.model = model;

    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      const message = errorPayload.detail || "Failed to analyze repository.";
      throw new Error(message);
    }

    const data = await response.json();
    latestAnalysis = data.analysis;
    latestRepository = data.repository;
    slides = buildSlides(latestAnalysis);
    renderRepositoryInfo(data.repository);
    renderAnalysis(latestAnalysis);
    updateStatusBadge(data.used_ai);

    downloadButton.disabled = false;
    presentationButton.disabled = slides.length === 0;
    statusMessage.textContent = data.used_ai
      ? "Analysis ready!"
      : "Fallback summary ready. Add an OpenAI API key for a richer explanation.";
  } catch (error) {
    statusMessage.textContent = error.message;
    analysisContent.classList.add("empty");
    analysisContent.innerHTML = "<p>We hit a snag. Double-check the URL or try again later.</p>";
  } finally {
    submitButton.disabled = false;
  }
});

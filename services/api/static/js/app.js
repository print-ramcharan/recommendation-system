document.addEventListener("DOMContentLoaded", () => {
  const userIdInput = document.getElementById("userIdInput");
  const limitSelect = document.getElementById("limitSelect");
  const getRecsBtn = document.getElementById("getRecsBtn");
  const recStats = document.getElementById("recStats");
  const experimentBadge = document.getElementById("experimentBadge");
  const responseTimeVal = document.getElementById("responseTimeVal");
  const recsList = document.getElementById("recsList");

  const searchQueryInput = document.getElementById("searchQueryInput");
  const searchBtn = document.getElementById("searchBtn");
  const searchResultsSection = document.getElementById("searchResultsSection");
  const searchResultsList = document.getElementById("searchResultsList");

  // Fetch Personalized Recommendations
  getRecsBtn.addEventListener("click", async () => {
    const userId = userIdInput.value.trim();
    const limit = limitSelect.value;
    if (!userId) return;

    recsList.innerHTML = `<div style="padding: 1rem; color: var(--text-secondary);">Generating...</div>`;
    recStats.style.display = "block";

    const startTime = performance.now();
    try {
      const response = await fetch(`/recommendations/personalized/${userId}?k=${limit}`);
      const duration = (performance.now() - startTime).toFixed(2);
      
      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }
      
      const articles = await response.json();
      const experimentGroup = response.headers.get("X-Experiment-Group") || "unknown";
      
      // Update Stats
      experimentBadge.textContent = experimentGroup;
      experimentBadge.className = `badge badge-${experimentGroup}`;
      responseTimeVal.textContent = `${duration}ms`;

      // Render Recommendations
      if (articles.length === 0) {
        recsList.innerHTML = `<div style="padding: 1rem; color: var(--text-secondary);">No recommendations found.</div>`;
      } else {
        recsList.innerHTML = articles.map(art => `
          <div class="list-item" onclick="triggerClickEvent(${userId}, ${art.article_id})">
            <div>
              <div style="font-weight: 700; font-size: 0.95rem;">${art.title}</div>
              <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">Category: ${art.category}</div>
            </div>
            <span class="badge badge-group-b" style="cursor: pointer;">Click Event</span>
          </div>
        `).join("");
      }
    } catch (err) {
      recsList.innerHTML = `<div style="padding: 1rem; color: #ef4444;">Failed: ${err.message}</div>`;
    }
  });

  // Execute Semantic Search
  searchBtn.addEventListener("click", async () => {
    const query = searchQueryInput.value.trim();
    if (!query) return;

    searchResultsList.innerHTML = `<div style="padding: 1rem; color: var(--text-secondary);">Searching...</div>`;
    searchResultsSection.style.display = "block";

    try {
      const response = await fetch(`/articles/search?query=${encodeURIComponent(query)}&k=5`);
      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }
      const articles = await response.json();

      if (articles.length === 0) {
        searchResultsList.innerHTML = `<div style="padding: 1rem; color: var(--text-secondary);">No matching articles found.</div>`;
      } else {
        searchResultsList.innerHTML = articles.map(art => `
          <div class="list-item">
            <div>
              <div style="font-weight: 700; font-size: 0.95rem;">${art.title}</div>
              <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">Category: ${art.category}</div>
            </div>
          </div>
        `).join("");
      }
    } catch (err) {
      searchResultsList.innerHTML = `<div style="padding: 1rem; color: #ef4444;">Search failed: ${err.message}</div>`;
    }
  });
});

// Trigger Click Event
async function triggerClickEvent(userId, articleId) {
  try {
    const response = await fetch(`/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        article_id: articleId,
        event_type: "click"
      })
    });
    if (response.ok) {
      alert(`💥 Click event logged successfully for user ${userId} on article ${articleId}! Cache invalidated.`);
    } else {
      alert(`❌ Failed to log click event.`);
    }
  } catch (err) {
    alert(`❌ Error logging click: ${err.message}`);
  }
}

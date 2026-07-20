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

  // Profile Interests Elements
  const profileUserIdInput = document.getElementById("profileUserIdInput");
  const currentInterestsText = document.getElementById("currentInterestsText");
  const newInterestsInput = document.getElementById("newInterestsInput");
  const updateInterestsBtn = document.getElementById("updateInterestsBtn");

  // Health Status Elements
  const postgresStatus = document.getElementById("postgresStatus");
  const redisStatus = document.getElementById("redisStatus");
  const qdrantStatus = document.getElementById("qdrantStatus");
  const activityLog = document.getElementById("activityLog");

  function logActivity(message) {
    const timestamp = new Date().toLocaleTimeString();
    activityLog.innerHTML += `<br>[${timestamp}] ${message}`;
    activityLog.scrollTop = activityLog.scrollHeight;
  }

  // Expose logActivity globally so that inline click handler can use it
  window.logActivity = logActivity;

  async function checkSystemHealth() {
    try {
      const response = await fetch("/health");
      const data = await response.json();
      const services = data.services || {};
      
      updateStatusBadge(postgresStatus, services.postgres);
      updateStatusBadge(redisStatus, services.redis);
      updateStatusBadge(qdrantStatus, services.qdrant);
      logActivity(`[Health Check] PostgreSQL: ${services.postgres}, Redis: ${services.redis}, Qdrant: ${services.qdrant}`);
    } catch (err) {
      updateStatusBadge(postgresStatus, "offline");
      updateStatusBadge(redisStatus, "offline");
      updateStatusBadge(qdrantStatus, "offline");
      logActivity(`[Health Check] Failed to query system health: ${err.message}`);
    }
  }

  function updateStatusBadge(element, status) {
    if (status === "online" || (status && status.startsWith("online"))) {
      element.textContent = "ONLINE";
      element.style.backgroundColor = "var(--accent-green)";
    } else {
      element.textContent = "OFFLINE";
      element.style.backgroundColor = "#ef4444";
    }
  }

  // Run on load
  checkSystemHealth();

  async function loadUserInterests() {
    const userId = profileUserIdInput.value.trim();
    if (!userId) return;
    try {
      const response = await fetch(`/users/${userId}/interests`);
      if (!response.ok) throw new Error("Not found");
      const data = await response.json();
      currentInterestsText.textContent = data.preferred_topics.join(", ") || "None";
    } catch (err) {
      currentInterestsText.textContent = "Error loading / Not found";
    }
  }

  profileUserIdInput.addEventListener("change", loadUserInterests);
  profileUserIdInput.addEventListener("keyup", loadUserInterests);

  updateInterestsBtn.addEventListener("click", async () => {
    const userId = profileUserIdInput.value.trim();
    const topicsRaw = newInterestsInput.value.trim();
    if (!userId || !topicsRaw) return;
    
    const topics = topicsRaw.split(",").map(t => t.trim()).filter(t => t.length > 0);
    logActivity(`[Profile Editor] Updating user ${userId} preferred topics to: ${topics.join(", ")}...`);
    
    try {
      const res = await fetch(`/users/${userId}/interests`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preferred_topics: topics })
      });
      if (!res.ok) throw new Error(`Status: ${res.statusText}`);
      const data = await res.json();
      logActivity(`[Profile Editor] User interests updated successfully! Redis cached user embeddings invalidated.`);
      loadUserInterests();
      alert("💥 User interests saved successfully! Cache cleared.");
    } catch (err) {
      logActivity(`[Profile Editor] Update failed: ${err.message}`);
      alert(`❌ Failed to update interests: ${err.message}`);
    }
  });

  // Call loadUserInterests on load
  loadUserInterests();

  // Initialize Chart.js
  const ctx = document.getElementById("latencyChart").getContext("2d");
  const latencyData = [];
  const latencyLabels = [];
  
  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: latencyLabels,
      datasets: [{
        label: 'Latency (ms)',
        data: latencyData,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { display: false },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9ca3af' }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });

  function addLatencyRecord(val) {
    if (latencyData.length >= 10) {
      latencyData.shift();
      latencyLabels.shift();
    }
    latencyData.push(parseFloat(val));
    latencyLabels.push(new Date().toLocaleTimeString());
    chart.update();
  }

  // Fetch Personalized Recommendations
  getRecsBtn.addEventListener("click", async () => {
    const userId = userIdInput.value.trim();
    const limit = limitSelect.value;
    if (!userId) return;

    recsList.innerHTML = `<div style="padding: 1rem; color: var(--text-secondary);">Generating...</div>`;
    recStats.style.display = "block";
    logActivity(`[Simulator] Fetching personalized recommendations for user ${userId} (k=${limit})...`);

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
      addLatencyRecord(duration);
      logActivity(`[Simulator] Mapped ${articles.length} recommendations in ${duration}ms via ${experimentGroup.toUpperCase()}`);

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
      logActivity(`[Simulator] Failed to generate recommendations: ${err.message}`);
    }
  });

  // Execute Semantic Search
  searchBtn.addEventListener("click", async () => {
    const query = searchQueryInput.value.trim();
    if (!query) return;

    searchResultsList.innerHTML = `<div style="padding: 1rem; color: var(--text-secondary);">Searching...</div>`;
    searchResultsSection.style.display = "block";
    logActivity(`[Search] Querying Vector database for matches to: "${query}"...`);

    try {
      const response = await fetch(`/articles/search?query=${encodeURIComponent(query)}&k=5`);
      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }
      const articles = await response.json();
      logActivity(`[Search] Vector DB returned ${articles.length} semantically matching documents.`);

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
      logActivity(`[Search] Semantic search execution failed: ${err.message}`);
    }
  });

  // NCF Training Panel elements
  const trainModelBtn = document.getElementById("trainModelBtn");
  const trainStatusText = document.getElementById("trainStatusText");
  const trainMessageText = document.getElementById("trainMessageText");
  let pollInterval = null;

  async function checkTrainingStatus() {
    try {
      const res = await fetch("/ml/status");
      const status = await res.json();
      
      trainStatusText.textContent = status.status.toUpperCase();
      trainMessageText.textContent = status.message || "";
      
      if (status.status === "training") {
        trainStatusText.style.color = "var(--accent-purple)";
        trainModelBtn.disabled = true;
        trainModelBtn.textContent = "Training...";
        if (!pollInterval) {
          pollInterval = setInterval(checkTrainingStatus, 2000);
        }
      } else {
        if (status.status === "failed") {
          trainStatusText.style.color = "#ef4444";
        } else {
          trainStatusText.style.color = "var(--accent-green)";
        }
        trainModelBtn.disabled = false;
        trainModelBtn.textContent = "Trigger Retraining";
        if (pollInterval) {
          clearInterval(pollInterval);
          pollInterval = null;
        }
      }
    } catch (err) {
      console.error("Failed to check training status:", err);
    }
  }

  trainModelBtn.addEventListener("click", async () => {
    logActivity("[Model Retrainer] Triggering NCF model training pipeline...");
    try {
      const res = await fetch("/ml/train", { method: "POST" });
      if (res.status === 409) {
        alert("NCF model training is already in progress!");
        return;
      }
      const data = await res.json();
      logActivity(`[Model Retrainer] ${data.message}`);
      checkTrainingStatus();
    } catch (err) {
      logActivity(`[Model Retrainer] Failed to trigger: ${err.message}`);
    }
  });

  // Initial check
  checkTrainingStatus();
});

// Trigger Click Event
async function triggerClickEvent(userId, articleId) {
  window.logActivity(`[Event Engine] Dispatching user click event: user=${userId}, article=${articleId}...`);
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
      window.logActivity(`[Event Engine] Click interaction logged successfully. Redis user profile embedding cache cleared.`);
      alert(`💥 Click event logged successfully for user ${userId} on article ${articleId}! Cache invalidated.`);
    } else {
      window.logActivity(`[Event Engine] Failed to dispatch event to Kafka topic broker.`);
      alert(`❌ Failed to log click event.`);
    }
  } catch (err) {
    window.logActivity(`[Event Engine] Event server connection failed: ${err.message}`);
    alert(`❌ Error logging click: ${err.message}`);
  }
}

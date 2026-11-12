(() => {
  const dropZone = document.getElementById("drop-zone");
  const imageInput = document.getElementById("image-input");
  const uploadPlaceholder = document.getElementById("upload-placeholder");
  const previewWrapper = document.getElementById("preview-wrapper");
  const imagePreview = document.getElementById("image-preview");
  const clearImageBtn = document.getElementById("clear-image-btn");
  const oshiHintInput = document.getElementById("oshi-hint");
  const targetDateInput = document.getElementById("target-date");
  const locationInput = document.getElementById("location-input");
  const budgetSelect = document.getElementById("budget-select");
  const coordForm = document.getElementById("coord-form");
  const submitBtn = document.getElementById("submit-btn");
  const resultsSection = document.getElementById("results-section");
  const reproposeBtn = document.getElementById("repropose-btn");
  const scrollToFormBtn = document.getElementById("scroll-to-form-btn");
  const editVibeSelect = document.getElementById("edit-vibe-select");

  // Settings Modal
  const settingsModal = document.getElementById("settings-modal");
  const openSettingsBtn = document.getElementById("open-settings-btn");
  const closeSettingsBtn = document.getElementById("close-settings-btn");
  const saveSettingsBtn = document.getElementById("save-settings-btn");
  const geminiKeyInput = document.getElementById("gemini-key");
  const weatherKeyInput = document.getElementById("weather-key");
  const affiliateIdInput = document.getElementById("affiliate-id");

  let currentImageBase64 = null;
  let currentDominantHexes = ["#2B2D42", "#8D99AE", "#EF233C"];

  // Set default date to tomorrow
  const tomorrow = new Date(Date.now() + 86400 * 1000);
  targetDateInput.value = tomorrow.toISOString().split("T")[0];

  // Restore session settings
  geminiKeyInput.value = sessionStorage.getItem("oshi_gemini_key") || "";
  weatherKeyInput.value = sessionStorage.getItem("oshi_weather_key") || "";
  affiliateIdInput.value = sessionStorage.getItem("oshi_affiliate_id") || "";

  openSettingsBtn.addEventListener("click", () => settingsModal.classList.remove("hidden"));
  closeSettingsBtn.addEventListener("click", () => settingsModal.classList.add("hidden"));
  saveSettingsBtn.addEventListener("click", () => {
    sessionStorage.setItem("oshi_gemini_key", geminiKeyInput.value.trim());
    sessionStorage.setItem("oshi_weather_key", weatherKeyInput.value.trim());
    sessionStorage.setItem("oshi_affiliate_id", affiliateIdInput.value.trim());
    settingsModal.classList.add("hidden");
  });

  // Image Upload & Drag/Drop
  dropZone.addEventListener("click", (e) => {
    if (e.target !== clearImageBtn) {
      imageInput.click();
    }
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
      loadImageFile(file);
    }
  });

  imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];
    if (file) {
      loadImageFile(file);
    }
  });

  clearImageBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    currentImageBase64 = null;
    imageInput.value = "";
    imagePreview.src = "";
    previewWrapper.classList.add("hidden");
    uploadPlaceholder.classList.remove("hidden");
  });

  function loadImageFile(file) {
    const reader = new FileReader();
    reader.onload = (ev) => {
      setPreviewImage(ev.target.result);
    };
    reader.readAsDataURL(file);
  }

  function setPreviewImage(dataUrl) {
    currentImageBase64 = dataUrl;
    imagePreview.src = dataUrl;
    uploadPlaceholder.classList.add("hidden");
    previewWrapper.classList.remove("hidden");

    const img = new Image();
    img.onload = () => {
      currentDominantHexes = extractTop3Colors(img);
    };
    img.src = dataUrl;
  }

  // Extract 3 distinct dominant hex colors via Canvas quantization
  function extractTop3Colors(img) {
    const canvas = document.createElement("canvas");
    const size = 64;
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0, size, size);
    const data = ctx.getImageData(0, 0, size, size).data;

    const buckets = new Map();
    for (let i = 0; i < data.length; i += 4) {
      const a = data[i + 3];
      if (a < 128) continue;
      const r = Math.round(data[i] / 32) * 32;
      const g = Math.round(data[i + 1] / 32) * 32;
      const b = Math.round(data[i + 2] / 32) * 32;
      const key = `${Math.min(r, 255)},${Math.min(g, 255)},${Math.min(b, 255)}`;
      buckets.set(key, (buckets.get(key) || 0) + 1);
    }

    const sorted = Array.from(buckets.entries()).sort((a, b) => b[1] - a[1]);
    const picked = [];
    for (const [key] of sorted) {
      const [r, g, b] = key.split(",").map(Number);
      const tooClose = picked.some(([pr, pg, pb]) => {
        return Math.hypot(r - pr, g - pg, b - pb) < 70;
      });
      if (!tooClose) {
        picked.push([r, g, b]);
      }
      if (picked.length >= 3) break;
    }

    while (picked.length < 3 && sorted.length > picked.length) {
      const [r, g, b] = sorted[picked.length][0].split(",").map(Number);
      picked.push([r, g, b]);
    }

    return picked.map(([r, g, b]) =>
      "#" + [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("").toUpperCase()
    );
  }

  // Sample Oshi Presets
  const PRESETS = {
    crimson: {
      colors: ["#1C1B22", "#C92A3E", "#E8E8EE"],
      hint: "クール系・紅黒ダークファンタジー",
    },
    pastel: {
      colors: ["#F8BBD0", "#E1BEE7", "#FFFDF9"],
      hint: "甘めガーリー・アイドル衣装",
    },
    cyber: {
      colors: ["#7B2CBF", "#181824", "#4CC9F0"],
      hint: "サイバー・サブカルネオン",
    },
  };

  document.querySelectorAll(".preset-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = btn.dataset.preset;
      const preset = PRESETS[key];
      if (!preset) return;

      const canvas = document.createElement("canvas");
      canvas.width = 240;
      canvas.height = 160;
      const ctx = canvas.getContext("2d");

      const grad = ctx.createLinearGradient(0, 0, 240, 160);
      grad.addColorStop(0, preset.colors[0]);
      grad.addColorStop(0.55, preset.colors[1]);
      grad.addColorStop(1, preset.colors[2]);
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, 240, 160);

      ctx.fillStyle = "rgba(255,255,255,0.88)";
      ctx.font = "bold 16px sans-serif";
      ctx.fillText("OSHI CONCEPT SAMPLE", 22, 76);
      ctx.font = "13px sans-serif";
      ctx.fillText(preset.hint, 22, 102);

      oshiHintInput.value = preset.hint;
      setPreviewImage(canvas.toDataURL("image/png"));
      currentDominantHexes = preset.colors;
    });
  });

  // Form Submit & Re-propose
  coordForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    await runAnalysis(false);
  });

  reproposeBtn.addEventListener("click", async () => {
    await runAnalysis(true);
  });

  scrollToFormBtn.addEventListener("click", () => {
    coordForm.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  async function runAnalysis(useManualOverride) {
    const skeletonEl = document.querySelector('input[name="skeleton_type"]:checked');
    const skeletonType = skeletonEl ? skeletonEl.value : "wave";
    const genderEl = document.querySelector('input[name="gender"]:checked');
    const gender = genderEl ? genderEl.value : "women";

    let overrideColors = null;
    let overrideVibe = null;
    if (useManualOverride) {
      const colorInputs = Array.from(document.querySelectorAll(".swatch-color-input"));
      if (colorInputs.length > 0) {
        overrideColors = colorInputs.map((el) => el.value.toUpperCase());
        currentDominantHexes = overrideColors;
      }
      overrideVibe = editVibeSelect.value || null;
    }

    submitBtn.disabled = true;
    reproposeBtn.disabled = true;
    submitBtn.textContent = "⏳ AIが推し概念・天気・骨格を解析中...";
    reproposeBtn.textContent = "⏳ 再提案中...";

    try {
      const payload = {
        image_base64: currentImageBase64,
        dominant_hexes: currentDominantHexes,
        override_colors: overrideColors,
        override_vibe: overrideVibe,
        oshi_hint: oshiHintInput.value.trim(),
        target_date: targetDateInput.value,
        location: locationInput.value.trim() || "東京",
        gender: gender,
        skeleton_type: skeletonType,
        budget_yen: Number(budgetSelect.value),
        gemini_api_key: geminiKeyInput.value.trim() || null,
        openweather_api_key: weatherKeyInput.value.trim() || null,
        affiliate_id: affiliateIdInput.value.trim() || null,
      };

      const resp = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }
      const data = await resp.json();
      renderResults(data);
    } catch (err) {
      alert(`解析中にエラーが発生しました: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      reproposeBtn.disabled = false;
      submitBtn.textContent = "✨ AIで全身コーディネートを提案する";
      reproposeBtn.textContent = "🔄 この色・条件で再提案する";
    }
  }

  function renderResults(data) {
    const { vision, weather, recommendation } = data;

    // Vision
    const visionLabels = {
      gemini_vision: "Gemini Vision API",
      manual_edit: "手動カラー編集",
      local_canvas: "Local Canvas解析",
    };
    document.getElementById("vision-source-badge").textContent =
      visionLabels[vision.source] || "Local Canvas解析";

    const swatchesEl = document.getElementById("color-swatches");
    swatchesEl.innerHTML = vision.colors
      .map((c, idx) => {
        const safeHex = /^#[0-9A-Fa-f]{6}$/.test(c.hex) ? c.hex : "#181820";
        return `
      <label class="swatch-item" title="クリックして色を変更">
        <input type="color" class="swatch-color-input" data-idx="${idx}" value="${escapeHtml(safeHex)}" />
        <div class="swatch-text">
          <strong>${escapeHtml(c.name)}</strong>
          <span class="swatch-hex-label">${escapeHtml(safeHex.toUpperCase())}</span>
        </div>
      </label>`;
      })
      .join("");

    swatchesEl.querySelectorAll(".swatch-color-input").forEach((input) => {
      input.addEventListener("input", () => {
        const label = input.parentElement.querySelector(".swatch-hex-label");
        if (label) label.textContent = input.value.toUpperCase();
      });
    });

    editVibeSelect.value = vision.vibe;
    document.getElementById("materials-label").textContent = vision.materials.join(" / ");

    // Weather
    const weatherSourceLabels = {
      openweathermap: "OpenWeatherMap API",
      "open-meteo": "Open-Meteo 気象予報",
      simulation: "気象シミュレーション",
    };
    document.getElementById("weather-source-badge").textContent =
      weatherSourceLabels[weather.source] || "気象シミュレーション";
    document.getElementById("weather-temp").textContent = weather.temp_c;
    document.getElementById("weather-loc-date").textContent = `${weather.location}（${weather.target_date}）`;
    document.getElementById("weather-cond").textContent =
      `${weather.condition} / 最高 ${weather.temp_max}℃・最低 ${weather.temp_min}℃`;
    document.getElementById("weather-advice").textContent = weather.advice;

    // Skeleton Banner
    const genderLabel = recommendation.gender === "men" ? "メンズ" : "レディース";
    document.getElementById("excluded-count-badge").textContent =
      `${genderLabel}・${recommendation.skeleton_rule.label}に不向きな ${recommendation.excluded_by_skeleton_count} 点を自動除外`;
    document.getElementById("skeleton-rule-desc").textContent =
      recommendation.skeleton_rule.description;

    // Outfit Total
    document.getElementById("total-price").textContent =
      `¥${recommendation.total_price.toLocaleString()}`;
    const budgetStatusEl = document.getElementById("budget-status");
    if (recommendation.within_budget) {
      budgetStatusEl.textContent = "✓ 予算上限内";
      budgetStatusEl.className = "budget-status ok";
    } else {
      budgetStatusEl.textContent = "※ 予算を少し超過（最安構成）";
      budgetStatusEl.className = "budget-status over";
    }

    // Outfit Cards
    const itemsEl = document.getElementById("outfit-items");
    itemsEl.innerHTML = recommendation.items
      .map((item) => {
        const ecClass = item.ec_platform === "SHEIN" ? "shein" : "zozo";
        const itemHex = /^#[0-9A-Fa-f]{6}$/.test(item.matched_color_hex || "")
          ? item.matched_color_hex
          : "#333745";
        return `
        <article class="item-card">
          <div>
            <div class="item-top">
              <span class="cat-badge">${escapeHtml(item.category_label)}</span>
              <span class="ec-badge ${ecClass}">${escapeHtml(item.ec_platform)}</span>
            </div>
            <div class="item-thumb">
              ${buildItemSvg(item.category, itemHex, item.name)}
            </div>
            <h4 class="item-name">${escapeHtml(item.name)}</h4>
            <div class="item-meta">
              推し色マッチ: <strong>${escapeHtml(item.matched_color)}</strong> ／ 素材: ${escapeHtml(item.materials.join("・"))}
            </div>
            <div class="item-reason">
              🦴 ${escapeHtml(item.skeleton_note)}
            </div>
          </div>
          <div class="item-bottom">
            <span class="item-price">¥${item.price.toLocaleString()}</span>
            <div class="buy-actions">
              <a class="buy-btn zozo-btn" href="${escapeHtml(item.zozotown_url)}" target="_blank" rel="noopener noreferrer">
                ZOZOTOWN ↗
              </a>
              <a class="buy-btn shein-btn" href="${escapeHtml(item.shein_url)}" target="_blank" rel="noopener noreferrer">
                SHEIN ↗
              </a>
            </div>
          </div>
        </article>`;
      })
      .join("");

    // EC Photo Showcase (3 ZOZOTOWN + 3 SHEIN = 6 items)
    if (data.ec_showcase) {
      renderShowcaseGrid("zozo-showcase-grid", data.ec_showcase.zozotown || [], "zozo-btn");
      renderShowcaseGrid("shein-showcase-grid", data.ec_showcase.shein || [], "shein-btn");
    }

    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderShowcaseGrid(containerId, picks, btnClass) {
    const grid = document.getElementById(containerId);
    if (!grid) return;
    grid.innerHTML = picks
      .map((pick) => {
        const hex = /^#[0-9A-Fa-f]{6}$/.test(pick.matched_color_hex || "")
          ? pick.matched_color_hex
          : "#333745";
        const fallbackSvg = buildItemSvg(pick.category, hex, pick.title);
        const mediaHtml = pick.image_url
          ? `<img src="${escapeHtml(pick.image_url)}" alt="${escapeHtml(pick.title)}" referrerpolicy="no-referrer" loading="lazy" />`
          : fallbackSvg;

        return `
        <article class="showcase-card">
          <div class="showcase-photo" data-fallback-cat="${escapeHtml(pick.category)}" data-fallback-hex="${escapeHtml(hex)}" data-fallback-title="${escapeHtml(pick.title)}">
            ${mediaHtml}
            <span class="showcase-cat-pill">${escapeHtml(pick.category_label)}</span>
          </div>
          <div class="showcase-body">
            <h4 class="showcase-title">${escapeHtml(pick.title)}</h4>
            <div class="showcase-footer">
              <span class="item-price">¥${Number(pick.price || 0).toLocaleString()}</span>
              <a class="buy-btn ${btnClass}" href="${escapeHtml(pick.url)}" target="_blank" rel="noopener noreferrer">
                ${escapeHtml(pick.platform)}で見る ↗
              </a>
            </div>
          </div>
        </article>`;
      })
      .join("");

    grid.querySelectorAll(".showcase-photo img").forEach((img) => {
      img.addEventListener("error", () => {
        const parent = img.parentElement;
        if (!parent) return;
        const cat = parent.dataset.fallbackCat || "tops";
        const hex = parent.dataset.fallbackHex || "#333745";
        const title = parent.dataset.fallbackTitle || "";
        img.replaceWith(createSvgElement(cat, hex, title));
      });
    });
  }

  function createSvgElement(category, hex, title) {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = buildItemSvg(category, hex, title);
    return wrapper.firstElementChild;
  }

  function buildItemSvg(category, fillHex, itemName) {
    const stroke = "#222430";
    if (category === "tops") {
      return `<svg viewBox="0 0 100 100" aria-hidden="true">
        <path d="M28 18 L40 14 Q50 22 60 14 L72 18 L88 34 L76 46 L68 38 L68 84 L32 84 L32 38 L24 46 L12 34 Z"
          fill="${escapeHtml(fillHex)}" stroke="${stroke}" stroke-width="3" stroke-linejoin="round"/>
      </svg>`;
    }
    if (category === "bottoms") {
      const isSkirt = itemName.includes("スカート");
      if (isSkirt) {
        return `<svg viewBox="0 0 100 100" aria-hidden="true">
          <path d="M32 16 L68 16 L82 84 L18 84 Z"
            fill="${escapeHtml(fillHex)}" stroke="${stroke}" stroke-width="3" stroke-linejoin="round"/>
          <line x1="34" y1="26" x2="66" y2="26" stroke="${stroke}" stroke-width="2"/>
        </svg>`;
      }
      return `<svg viewBox="0 0 100 100" aria-hidden="true">
        <path d="M30 14 L70 14 L76 86 L54 86 L50 44 L46 86 L24 86 Z"
          fill="${escapeHtml(fillHex)}" stroke="${stroke}" stroke-width="3" stroke-linejoin="round"/>
      </svg>`;
    }
    if (category === "outer") {
      return `<svg viewBox="0 0 100 100" aria-hidden="true">
        <path d="M26 16 L42 12 L50 24 L58 12 L74 16 L90 38 L78 52 L70 42 L70 86 L30 86 L30 42 L22 52 L10 38 Z"
          fill="${escapeHtml(fillHex)}" stroke="${stroke}" stroke-width="3" stroke-linejoin="round"/>
        <line x1="50" y1="24" x2="50" y2="86" stroke="${stroke}" stroke-width="2.5"/>
      </svg>`;
    }
    if (category === "shoes") {
      return `<svg viewBox="0 0 100 100" aria-hidden="true">
        <path d="M22 30 L44 30 L48 56 L78 64 Q86 68 84 78 L18 78 L18 42 Z"
          fill="${escapeHtml(fillHex)}" stroke="${stroke}" stroke-width="3" stroke-linejoin="round"/>
        <rect x="18" y="74" width="66" height="8" rx="3" fill="#2b2d38"/>
      </svg>`;
    }
    // accessories (bag)
    return `<svg viewBox="0 0 100 100" aria-hidden="true">
      <path d="M34 36 Q50 12 66 36" fill="none" stroke="${stroke}" stroke-width="3.5"/>
      <rect x="22" y="36" width="56" height="44" rx="8"
        fill="${escapeHtml(fillHex)}" stroke="${stroke}" stroke-width="3"/>
      <path d="M22 50 L50 62 L78 50" fill="none" stroke="${stroke}" stroke-width="2.5"/>
    </svg>`;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
})();

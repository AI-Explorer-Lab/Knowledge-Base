const state = { options: null, items: [], editingId: null, sectionDrafts: {} };
let messageFadeTimer = null;
let messageHideTimer = null;

const $ = (id) => document.getElementById(id);
const splitLines = (value) => value.split("\n").map((item) => item.trim()).filter(Boolean);
const splitComma = (value) => value.split(",").map((item) => item.trim()).filter(Boolean);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));

function autoGrow(field) {
  field.style.height = "auto";
  field.style.height = `${Math.max(field.scrollHeight, 74)}px`;
}

function refreshAutoGrow(container = document) {
  container.querySelectorAll("textarea").forEach(autoGrow);
}

async function api(path, options = {}) {
  const response = await fetch(path, {headers: {"Content-Type": "application/json", ...(options.headers || {})}, ...options});
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(payload.detail) ? payload.detail.map((item) => item.msg).join("；") : payload.detail;
    throw new Error(payload.message || detail || `请求失败（${response.status}）`);
  }
  return payload;
}

function notify(message, error = false) {
  const box = $("message");
  clearTimeout(messageFadeTimer);
  clearTimeout(messageHideTimer);
  box.textContent = message;
  box.classList.remove("hidden", "error", "fading");
  if (error) box.classList.add("error");
  messageFadeTimer = setTimeout(() => {
    box.classList.add("fading");
    messageHideTimer = setTimeout(() => box.classList.add("hidden"), 450);
  }, 3000);
}

function switchTab(name) {
  document.querySelectorAll(".tab").forEach((button) => button.classList.toggle("active", button.dataset.tab === name));
  document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.id === `tab-${name}`));
  if (name === "lifecycle") loadLifecycle();
}

function fillSelect(element, values, keepFirst = false) {
  const first = keepFirst ? element.options[0]?.outerHTML || "" : "";
  element.innerHTML = first + values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join("");
}

async function init() {
  try {
    const [health, options] = await Promise.all([api("/health"), api("/api/meta/form-options")]);
    state.options = options;
    $("health").textContent = `已连接 · ${health.environment}`;
    fillSelect($("filterType"), options.knowledge_types, true);
    fillSelect($("filterScope"), options.scopes, true);
    fillSelect($("filterStatus"), options.statuses, true);
    fillSelect($("knowledgeType"), options.knowledge_types);
    fillSelect($("knowledgeScope"), options.scopes);
    fillSelect($("knowledgeRisk"), options.risk_levels);
    fillSelect($("knowledgePolarity"), options.polarities);
    fillSelect($("eventType"), options.event_types);
    $("phaseOptions").innerHTML = options.phases.map((phase) => `<label class="check-item"><input type="checkbox" value="${phase}">${phase}</label>`).join("");
    resetEditor();
    toggleValidationFields();
    await loadKnowledge();
  } catch (error) {
    $("health").textContent = "连接失败";
    notify(error.message, true);
  }
}

async function loadKnowledge() {
  const params = new URLSearchParams({q: $("filterQuery").value, type: $("filterType").value, scope: $("filterScope").value, status: $("filterStatus").value});
  const data = await api(`/api/knowledge?${params}`);
  state.items = data.items;
  $("knowledgeRows").innerHTML = data.items.length ? data.items.map((item) => `
    <tr>
      <td class="id-title"><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.id)}</span></td>
      <td><span class="badge">${escapeHtml(item.type)}</span> <span class="badge">${escapeHtml(item.scope)}</span><br><small>${escapeHtml(item.domain)}</small></td>
      <td><span class="badge ${escapeHtml(item.maturity)}">${escapeHtml(item.maturity)}</span></td>
      <td><span class="badge ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span></td>
      <td>${escapeHtml(item.owner)}</td>
      <td>${escapeHtml(item.derived.next_review_at)}</td>
      <td><button class="button ghost" onclick="editKnowledge('${escapeHtml(item.id)}')">编辑</button></td>
    </tr>`).join("") : `<tr><td colspan="7" class="empty">没有符合条件的知识</td></tr>`;
  $("evidenceKnowledge").innerHTML = data.items.map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.id)} · ${escapeHtml(item.title)}</option>`).join("");
}

function saveSectionDrafts() {
  document.querySelectorAll("[data-section]").forEach((field) => state.sectionDrafts[field.dataset.section] = field.value);
}

function renderSections(values = {}) {
  saveSectionDrafts();
  state.sectionDrafts = {...state.sectionDrafts, ...values};
  const type = $("knowledgeType").value;
  const names = [...state.options.common_sections, ...(state.options.type_sections[type] || [])];
  $("sectionFields").innerHTML = names.map((name) => `
    <label class="${name === "详细说明" ? "wide" : ""}">${escapeHtml(name)} <span>必填</span>
      <textarea class="auto-grow" rows="2" data-section="${escapeHtml(name)}" required>${escapeHtml(state.sectionDrafts[name] || "")}</textarea>
    </label>`).join("");
  $("polarityLabel").classList.toggle("hidden", type !== "guideline");
  refreshAutoGrow($("sectionFields"));
}

async function suggestId() {
  if (state.editingId) return;
  const params = new URLSearchParams({scope: $("knowledgeScope").value, type: $("knowledgeType").value});
  const data = await api(`/api/knowledge/suggest-id?${params}`);
  $("knowledgeId").value = data.id;
}

function resetEditor() {
  state.editingId = null;
  state.sectionDrafts = {};
  $("knowledgeForm").reset();
  $("knowledgeType").value = "guideline";
  $("knowledgeScope").value = "tech";
  $("knowledgeRisk").value = state.options.defaults.risk_level;
  $("knowledgeOwner").value = state.options.defaults.owner;
  $("knowledgePolarity").value = "recommend";
  $("editorTitle").textContent = "新建知识";
  $("editorMode").textContent = "保存后自动运行 Lint 并重建 Catalog";
  $("cancelEdit").classList.add("hidden");
  document.querySelectorAll("#phaseOptions input").forEach((item) => item.checked = false);
  renderSections();
  refreshAutoGrow();
  suggestId();
}

function collectKnowledge() {
  const sections = {};
  document.querySelectorAll("[data-section]").forEach((field) => sections[field.dataset.section] = field.value);
  return {
    id: $("knowledgeId").value || null,
    title: $("knowledgeTitle").value,
    type: $("knowledgeType").value,
    scope: $("knowledgeScope").value,
    domain: $("knowledgeDomain").value,
    risk_level: $("knowledgeRisk").value,
    owner: $("knowledgeOwner").value,
    maintainers: splitComma($("knowledgeMaintainers").value),
    applicable_phases: [...document.querySelectorAll("#phaseOptions input:checked")].map((item) => item.value),
    applicable_conditions: splitLines($("applicableConditions").value),
    not_applicable_conditions: splitLines($("notApplicableConditions").value),
    tags: splitComma($("knowledgeTags").value),
    source_references: splitLines($("sourceReferences").value).map((line) => {
      const separator = line.indexOf("|");
      return separator < 0 ? {type: "document", ref: line} : {type: line.slice(0, separator).trim(), ref: line.slice(separator + 1).trim()};
    }),
    polarity: $("knowledgeType").value === "guideline" ? $("knowledgePolarity").value : null,
    sections,
  };
}

async function editKnowledge(id) {
  try {
    const data = await api(`/api/knowledge/${encodeURIComponent(id)}`);
    const meta = data.metadata;
    state.editingId = id;
    state.sectionDrafts = data.sections;
    $("knowledgeId").value = id;
    $("knowledgeTitle").value = meta.title;
    $("knowledgeType").value = meta.type;
    $("knowledgeScope").value = meta.scope;
    $("knowledgeDomain").value = meta.domain;
    $("knowledgeRisk").value = meta.risk_level;
    $("knowledgeOwner").value = meta.owner;
    $("knowledgeMaintainers").value = (meta.maintainers || []).join(", ");
    $("knowledgeTags").value = (meta.tags || []).join(", ");
    $("knowledgePolarity").value = meta.polarity || "recommend";
    $("applicableConditions").value = (meta.applicable_conditions || []).join("\n");
    $("notApplicableConditions").value = (meta.not_applicable_conditions || []).join("\n");
    $("sourceReferences").value = (meta.source_references || []).map((item) => `${item.type} | ${item.ref}`).join("\n");
    document.querySelectorAll("#phaseOptions input").forEach((item) => item.checked = (meta.applicable_phases || []).includes(item.value));
    renderSections(data.sections);
    refreshAutoGrow();
    $("editorTitle").textContent = `编辑 ${id}`;
    $("editorMode").textContent = `保留 maturity=${meta.maturity}、status=${meta.status}；状态变化需走治理提案`;
    $("cancelEdit").classList.remove("hidden");
    switchTab("editor");
  } catch (error) { notify(error.message, true); }
}

async function validateKnowledge() {
  const query = state.editingId ? `?existing_id=${encodeURIComponent(state.editingId)}` : "";
  await api(`/api/knowledge/validate${query}`, {method: "POST", body: JSON.stringify(collectKnowledge())});
  notify("检查通过：字段、正文结构、ID、路径和引用均有效。", false);
}

async function saveKnowledge(event) {
  event.preventDefault();
  try {
    const path = state.editingId ? `/api/knowledge/${encodeURIComponent(state.editingId)}` : "/api/knowledge";
    const method = state.editingId ? "PUT" : "POST";
    const data = await api(path, {method, body: JSON.stringify(collectKnowledge())});
    notify(`${data.id} 已保存，并已重建 Catalog。`);
    await loadKnowledge();
    await editKnowledge(data.id);
  } catch (error) { notify(error.message, true); }
}

function toggleValidationFields() {
  const validation = ["validated_success", "validated_failure"].includes($("eventType").value);
  $("validationFields").classList.toggle("hidden", !validation);
  document.querySelectorAll(".validation-required").forEach((item) => item.textContent = validation ? "验证事件必填" : "可选");
}

async function saveEvidence(event) {
  event.preventDefault();
  const validation = ["validated_success", "validated_failure"].includes($("eventType").value);
  const payload = {
    event_type: $("eventType").value,
    contributor: $("eventContributor").value || null,
    operator: $("eventOperator").value || null,
    project: $("eventProject").value || null,
    reference: $("eventReference").value || null,
    scenario_id: validation ? $("eventScenario").value : null,
    evidence_group_id: validation ? $("eventGroup").value : null,
    validation_method: validation ? $("eventMethod").value : null,
    result_summary: validation ? $("eventSummary").value : null,
  };
  try {
    const id = $("evidenceKnowledge").value;
    const data = await api(`/api/knowledge/${encodeURIComponent(id)}/events`, {method: "POST", body: JSON.stringify(payload)});
    notify(`Evidence 已记录：${data.event.event_id}`);
    $("evidenceForm").reset();
    toggleValidationFields();
    await loadKnowledge();
  } catch (error) { notify(error.message, true); }
}

async function loadLifecycle() {
  try {
    const data = await api("/api/lifecycle/candidates");
    $("lifecycleCards").innerHTML = data.items.length ? data.items.map((item) => `
      <article class="card"><h3>${escapeHtml(item.knowledge_id)} · ${escapeHtml(item.title)}</h3>
      ${item.proposals.map((proposal) => `<p><span class="badge">${escapeHtml(proposal.kind)}</span> ${escapeHtml(proposal.from)} → <strong>${escapeHtml(proposal.to)}</strong></p><p>${escapeHtml(proposal.reasons.join("；"))}</p>`).join("")}
      <p>下次复核：${escapeHtml(item.derived.next_review_at)}</p></article>`).join("") : `<div class="empty">当前没有需要处理的治理建议</div>`;
  } catch (error) { notify(error.message, true); }
}

document.addEventListener("DOMContentLoaded", () => {
  document.addEventListener("input", (event) => {
    if (event.target.matches("textarea")) autoGrow(event.target);
  });
  document.querySelectorAll(".tab").forEach((button) => button.addEventListener("click", () => {
    if (button.dataset.tab === "editor" && state.editingId) resetEditor();
    switchTab(button.dataset.tab);
  }));
  $("searchKnowledge").addEventListener("click", () => loadKnowledge().catch((error) => notify(error.message, true)));
  $("newKnowledge").addEventListener("click", () => { resetEditor(); switchTab("editor"); });
  $("resetEditor").addEventListener("click", resetEditor);
  $("cancelEdit").addEventListener("click", () => {
    resetEditor();
    notify("已取消编辑，当前为新的空白知识表单。");
  });
  $("knowledgeType").addEventListener("change", () => { renderSections(); suggestId(); });
  $("knowledgeScope").addEventListener("change", suggestId);
  $("validateKnowledge").addEventListener("click", () => validateKnowledge().catch((error) => notify(error.message, true)));
  $("knowledgeForm").addEventListener("submit", saveKnowledge);
  $("eventType").addEventListener("change", toggleValidationFields);
  $("evidenceForm").addEventListener("submit", saveEvidence);
  $("refreshLifecycle").addEventListener("click", loadLifecycle);
  $("rebuildCatalog").addEventListener("click", async () => { try { const data = await api("/api/catalog/rebuild", {method: "POST", body: "{}"}); notify(`目录已重建：${data.paths.join("、")}`); } catch (error) { notify(error.message, true); } });
  init();
});

window.editKnowledge = editKnowledge;

/**
 * SmartBill Engine - Client Application Logic
 * Clean, Engineered Interface (No Emojis), Tab Switching,
 * Empty Initial Member Pool, Dynamic Chip Allocation, and Fair-Share Settlement.
 */

const STATE = {
  currentView: "splitter", // 'splitter' | 'benchmark' | 'algorithm'
  currentStep: 1,
  currentBill: null,
  members: [], // Empty by default; user adds participants manually
  assignments: {}, // item_id -> { is_all: bool, assigned_to: Set<string> }
  splitResult: null,
};

const AVATAR_COLORS = [
  "#4338ca", "#0284c7", "#059669", "#d97706", 
  "#db2777", "#7c3aed", "#0d9488", "#ea580c"
];

function getMemberColor(name) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const idx = Math.abs(hash) % AVATAR_COLORS.length;
  return AVATAR_COLORS[idx];
}

document.addEventListener("DOMContentLoaded", () => {
  setupUploadListeners();
  renderMembersList();
});

// ==========================================
// TOP NAVIGATION VIEW SWITCHER
// ==========================================
function switchView(viewName) {
  STATE.currentView = viewName;

  document.getElementById("view-splitter").style.display = viewName === "splitter" ? "block" : "none";
  document.getElementById("view-benchmark").style.display = viewName === "benchmark" ? "block" : "none";
  document.getElementById("view-algorithm").style.display = viewName === "algorithm" ? "block" : "none";

  document.getElementById("tab-btn-splitter").classList.toggle("active", viewName === "splitter");
  document.getElementById("tab-btn-benchmark").classList.toggle("active", viewName === "benchmark");
  document.getElementById("tab-btn-algorithm").classList.toggle("active", viewName === "algorithm");

  if (viewName === "benchmark") {
    loadSampleBills();
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ==========================================
// STEPPER NAVIGATION (SPLITTER WORKFLOW)
// ==========================================
function goToStep(step) {
  if (step > 1 && !STATE.currentBill) {
    alert("Please upload a receipt photo or load a benchmark bill first.");
    return;
  }
  STATE.currentStep = step;
  document.querySelectorAll(".step-section").forEach((sec, idx) => {
    sec.classList.toggle("active", idx + 1 === step);
  });
  document.querySelectorAll(".step-btn").forEach((btn, idx) => {
    btn.classList.toggle("active", idx + 1 === step);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ==========================================
// STEP 1: INGESTION & UPLOAD
// ==========================================
function setupUploadListeners() {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "#4338ca";
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.style.borderColor = "#cbd5e1";
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "#cbd5e1";
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleReceiptFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleReceiptFile(e.target.files[0]);
    }
  });
}

async function handleReceiptFile(file) {
  const statusBox = document.getElementById("upload-status");
  statusBox.textContent = `Extracting structured items from "${file.name || 'capture.jpg'}"...`;
  statusBox.style.color = "#4338ca";

  const formData = new FormData();
  formData.append("file", file, file.name || "capture.jpg");

  try {
    const res = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error("OCR extraction failed");
    const bill = await res.json();
    statusBox.textContent = "Extraction complete. Navigating to verification...";
    statusBox.style.color = "#059669";
    setTimeout(() => {
      setLoadedBill(bill);
      goToStep(2);
    }, 450);
  } catch (err) {
    statusBox.textContent = `Extraction error: ${err.message}`;
    statusBox.style.color = "#dc2626";
  }
}

function setLoadedBill(bill) {
  STATE.currentBill = bill;
  STATE.assignments = {};
  bill.items.forEach((item) => {
    STATE.assignments[item.id] = {
      is_all: STATE.members.length > 0,
      assigned_to: new Set(STATE.members),
    };
  });
  populateReviewScreen();
}

// ==========================================
// CAMERA CAPTURE
// ==========================================
let cameraStream = null;
let capturedBlob = null;

async function openCameraModal() {
  const modal = document.getElementById("camera-modal");
  const video = document.getElementById("camera-video");
  const canvas = document.getElementById("camera-canvas");
  const errBox = document.getElementById("camera-error");
  const btnSnap = document.getElementById("btn-snap");
  const btnRetake = document.getElementById("btn-retake");
  const btnUse = document.getElementById("btn-use-photo");

  modal.style.display = "flex";
  video.style.display = "block";
  canvas.style.display = "none";
  errBox.style.display = "none";
  btnSnap.style.display = "inline-flex";
  btnRetake.style.display = "none";
  btnUse.style.display = "none";
  capturedBlob = null;

  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    video.srcObject = cameraStream;
  } catch (err) {
    console.warn("Could not access environment camera, falling back to default:", err);
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      video.srcObject = cameraStream;
    } catch (fallbackErr) {
      errBox.style.display = "block";
      errBox.textContent = `Camera initialization failed: ${fallbackErr.message}. Ensure camera permissions are granted.`;
      btnSnap.style.display = "none";
    }
  }
}

function captureSnapshot() {
  const video = document.getElementById("camera-video");
  const canvas = document.getElementById("camera-canvas");
  const btnSnap = document.getElementById("btn-snap");
  const btnRetake = document.getElementById("btn-retake");
  const btnUse = document.getElementById("btn-use-photo");

  if (!video.videoWidth) return;

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  video.style.display = "none";
  canvas.style.display = "block";

  btnSnap.style.display = "none";
  btnRetake.style.display = "inline-flex";
  btnUse.style.display = "inline-flex";

  canvas.toBlob((blob) => {
    capturedBlob = blob;
  }, "image/jpeg", 0.95);
}

function retakeSnapshot() {
  const video = document.getElementById("camera-video");
  const canvas = document.getElementById("camera-canvas");
  const btnSnap = document.getElementById("btn-snap");
  const btnRetake = document.getElementById("btn-retake");
  const btnUse = document.getElementById("btn-use-photo");

  video.style.display = "block";
  canvas.style.display = "none";

  btnSnap.style.display = "inline-flex";
  btnRetake.style.display = "none";
  btnUse.style.display = "none";
  capturedBlob = null;
}

function useCapturedPhoto() {
  if (!capturedBlob) return;
  const file = new File([capturedBlob], `receipt_${Date.now()}.jpg`, { type: "image/jpeg" });
  closeCameraModal();
  handleReceiptFile(file);
}

function closeCameraModal() {
  const modal = document.getElementById("camera-modal");
  modal.style.display = "none";
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
  }
}

// ==========================================
// BENCHMARK SUITE (12 TEST BILLS)
// ==========================================
async function loadSampleBills() {
  const grid = document.getElementById("sample-grid");
  grid.innerHTML = "<p>Loading benchmark cases...</p>";

  try {
    const res = await fetch("/api/sample-bills");
    const data = await res.json();
    grid.innerHTML = "";

    data.bills.forEach((bill) => {
      const card = document.createElement("div");
      card.className = "sample-card";
      card.onclick = () => selectBenchmarkBill(bill.bill_id);

      const isFaulty = !bill.is_arithmetically_valid;
      const tagClass = isFaulty ? "sample-tag tag-error" : "sample-tag";

      card.innerHTML = `
        <div class="sample-top">
          <span class="${tagClass}">${bill.condition_tag}</span>
          <span style="font-size: 0.75rem; color: #64748b;">${bill.items_count} items</span>
        </div>
        <div class="sample-name">${bill.bill_name}</div>
        <div class="sample-desc">${bill.challenge_description}</div>
        <div class="sample-footer">
          <span>Printed Total:</span>
          <span class="sample-total">INR ${bill.grand_total.toFixed(2)}</span>
        </div>
      `;
      grid.appendChild(card);
    });
  } catch (err) {
    grid.innerHTML = `<p style="color: red;">Error loading benchmark suite: ${err.message}</p>`;
  }
}

async function selectBenchmarkBill(billId) {
  try {
    const res = await fetch(`/api/bills/${billId}`);
    if (!res.ok) throw new Error("Could not retrieve benchmark data");
    const bill = await res.json();
    setLoadedBill(bill);
    switchView("splitter");
    goToStep(2);
  } catch (err) {
    alert(`Error loading benchmark bill: ${err.message}`);
  }
}

// ==========================================
// STEP 2: VERIFICATION & CONFIDENCE REVIEW
// ==========================================
function populateReviewScreen() {
  const bill = STATE.currentBill;
  if (!bill) return;

  const imgPreview = document.getElementById("bill-img-preview");
  imgPreview.src = bill.image_url || "/test_bills/bill_01_dim_light.jpg";
  document.getElementById("preview-bill-title").textContent = bill.metadata.restaurant_name || "Source Receipt";
  document.getElementById("condition-badge").textContent = bill.condition_tag || "Standard";

  const discBanner = document.getElementById("discrepancy-banner");
  if (!bill.metadata.is_arithmetically_valid) {
    discBanner.style.display = "flex";
    document.getElementById("discrepancy-desc").textContent = 
      `Discrepancy: Printed total is INR ${bill.metadata.grand_total.toFixed(2)}, which differs from calculated line items + taxes by ${bill.metadata.discrepancy_amount > 0 ? "+" : ""}INR ${bill.metadata.discrepancy_amount.toFixed(2)}. Adjust items or override total below.`;
  } else {
    discBanner.style.display = "none";
  }

  renderReviewTable();

  document.getElementById("meta-subtotal").value = bill.metadata.subtotal.toFixed(2);
  document.getElementById("meta-cgst").value = bill.metadata.taxes.cgst.toFixed(2);
  document.getElementById("meta-sgst").value = bill.metadata.taxes.sgst.toFixed(2);
  document.getElementById("meta-vat").value = bill.metadata.taxes.vat.toFixed(2);
  document.getElementById("meta-service-charge").value = bill.metadata.taxes.service_charge.toFixed(2);
  document.getElementById("meta-discount").value = bill.metadata.taxes.discount.toFixed(2);
  document.getElementById("meta-grand-total").value = bill.metadata.grand_total.toFixed(2);
}

function renderReviewTable() {
  const tbody = document.getElementById("review-items-body");
  tbody.innerHTML = "";

  STATE.currentBill.items.forEach((item, index) => {
    const tr = document.createElement("tr");
    const confPct = Math.round((item.confidence || 0.9) * 100);
    const confClass = confPct >= 85 ? "conf-good" : "conf-warn";

    tr.innerHTML = `
      <td>
        <input type="text" value="${item.name}" onchange="updateItemName(${index}, this.value)">
      </td>
      <td>
        <input type="number" step="1" min="1" value="${item.quantity}" onchange="updateItemQty(${index}, this.value)">
      </td>
      <td>
        <input type="number" step="0.01" min="0" value="${item.unit_price.toFixed(2)}" onchange="updateItemUnitPrice(${index}, this.value)">
      </td>
      <td>
        <input type="number" step="0.01" min="0" value="${item.total_price.toFixed(2)}" onchange="updateItemTotal(${index}, this.value)">
      </td>
      <td>
        <span class="conf-badge ${confClass}">${confPct}%</span>
      </td>
      <td>
        <button class="btn-icon-del" onclick="deleteLineItem(${index})" title="Delete item">&times;</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function updateItemName(idx, val) {
  STATE.currentBill.items[idx].name = val;
}

function updateItemQty(idx, val) {
  const qty = parseFloat(val) || 1;
  STATE.currentBill.items[idx].quantity = qty;
  STATE.currentBill.items[idx].total_price = Math.round(qty * STATE.currentBill.items[idx].unit_price * 100) / 100;
  renderReviewTable();
  recalculateReviewTotals();
}

function updateItemUnitPrice(idx, val) {
  const price = parseFloat(val) || 0;
  STATE.currentBill.items[idx].unit_price = price;
  STATE.currentBill.items[idx].total_price = Math.round(STATE.currentBill.items[idx].quantity * price * 100) / 100;
  renderReviewTable();
  recalculateReviewTotals();
}

function updateItemTotal(idx, val) {
  const total = parseFloat(val) || 0;
  STATE.currentBill.items[idx].total_price = total;
  if (STATE.currentBill.items[idx].quantity > 0) {
    STATE.currentBill.items[idx].unit_price = Math.round((total / STATE.currentBill.items[idx].quantity) * 100) / 100;
  }
  recalculateReviewTotals();
}

function deleteLineItem(idx) {
  STATE.currentBill.items.splice(idx, 1);
  renderReviewTable();
  recalculateReviewTotals();
}

function addNewLineItem() {
  const newId = `item_custom_${Date.now()}`;
  STATE.currentBill.items.push({
    id: newId,
    name: "Custom Item",
    quantity: 1.0,
    unit_price: 100.0,
    total_price: 100.0,
    confidence: 1.0,
  });
  STATE.assignments[newId] = {
    is_all: STATE.members.length > 0,
    assigned_to: new Set(STATE.members),
  };
  renderReviewTable();
  recalculateReviewTotals();
}

function recalculateReviewTotals() {
  const itemsSum = STATE.currentBill.items.reduce((sum, item) => sum + (parseFloat(item.total_price) || 0), 0);
  STATE.currentBill.metadata.subtotal = Math.round(itemsSum * 100) / 100;
  document.getElementById("meta-subtotal").value = STATE.currentBill.metadata.subtotal.toFixed(2);

  const cgst = parseFloat(document.getElementById("meta-cgst").value) || 0;
  const sgst = parseFloat(document.getElementById("meta-sgst").value) || 0;
  const vat = parseFloat(document.getElementById("meta-vat").value) || 0;
  const sc = parseFloat(document.getElementById("meta-service-charge").value) || 0;
  const disc = parseFloat(document.getElementById("meta-discount").value) || 0;

  STATE.currentBill.metadata.taxes.cgst = cgst;
  STATE.currentBill.metadata.taxes.sgst = sgst;
  STATE.currentBill.metadata.taxes.vat = vat;
  STATE.currentBill.metadata.taxes.service_charge = sc;
  STATE.currentBill.metadata.taxes.discount = disc;

  const calculatedGrand = Math.round((itemsSum + cgst + sgst + vat + sc - disc) * 100) / 100;
  STATE.currentBill.metadata.grand_total = calculatedGrand;
  document.getElementById("meta-grand-total").value = calculatedGrand.toFixed(2);
}

function proceedToAssignment() {
  STATE.currentBill.metadata.subtotal = parseFloat(document.getElementById("meta-subtotal").value) || 0;
  STATE.currentBill.metadata.taxes.cgst = parseFloat(document.getElementById("meta-cgst").value) || 0;
  STATE.currentBill.metadata.taxes.sgst = parseFloat(document.getElementById("meta-sgst").value) || 0;
  STATE.currentBill.metadata.taxes.vat = parseFloat(document.getElementById("meta-vat").value) || 0;
  STATE.currentBill.metadata.taxes.service_charge = parseFloat(document.getElementById("meta-service-charge").value) || 0;
  STATE.currentBill.metadata.taxes.discount = parseFloat(document.getElementById("meta-discount").value) || 0;
  STATE.currentBill.metadata.grand_total = parseFloat(document.getElementById("meta-grand-total").value) || 0;

  renderAssignmentTable();
  updateLiveSpendTicker();
  goToStep(3);
}

// ==========================================
// STEP 3: PARTICIPANT CHIPS (WAY A)
// ==========================================
function renderMembersList() {
  const container = document.getElementById("members-list");
  const emptyAlert = document.getElementById("empty-members-alert");
  const ticker = document.getElementById("live-spend-ticker");

  container.innerHTML = "";
  document.getElementById("member-count").textContent = STATE.members.length;

  if (STATE.members.length === 0) {
    emptyAlert.style.display = "block";
    ticker.style.display = "none";
    return;
  }

  emptyAlert.style.display = "none";
  ticker.style.display = "flex";

  STATE.members.forEach((m) => {
    const pill = document.createElement("div");
    pill.className = "member-pill";
    const color = getMemberColor(m);
    const initial = m.charAt(0).toUpperCase();

    pill.innerHTML = `
      <span class="member-avatar" style="background-color: ${color};">${initial}</span>
      <span>${m}</span>
      <span class="remove-member" title="Remove participant" onclick="removeMember('${m}')">&times;</span>
    `;
    container.appendChild(pill);
  });
}

function handleMemberInput(e) {
  if (e.key === "Enter") {
    addMemberFromInput();
  }
}

function addMemberFromInput() {
  const input = document.getElementById("new-member-input");
  const name = input.value.trim();
  if (!name) return;
  if (STATE.members.includes(name)) {
    alert("This participant is already registered.");
    return;
  }
  STATE.members.push(name);
  input.value = "";
  renderMembersList();

  // If items are currently shared with all, add the new member
  if (STATE.currentBill) {
    Object.keys(STATE.assignments).forEach((itemId) => {
      if (STATE.assignments[itemId].is_all) {
        STATE.assignments[itemId].assigned_to.add(name);
      }
    });
  }

  if (STATE.currentStep === 3) {
    renderAssignmentTable();
    updateLiveSpendTicker();
  }
}

function removeMember(name) {
  STATE.members = STATE.members.filter((m) => m !== name);
  Object.keys(STATE.assignments).forEach((itemId) => {
    STATE.assignments[itemId].assigned_to.delete(name);
  });
  renderMembersList();
  renderAssignmentTable();
  updateLiveSpendTicker();
}

function renderAssignmentTable() {
  const tbody = document.getElementById("assignment-table-body");
  tbody.innerHTML = "";

  if (!STATE.currentBill) return;

  STATE.currentBill.items.forEach((item) => {
    const tr = document.createElement("tr");

    if (!STATE.assignments[item.id]) {
      STATE.assignments[item.id] = { is_all: true, assigned_to: new Set(STATE.members) };
    }
    const asgn = STATE.assignments[item.id];

    let chipsHtml = `<div class="chips-container">`;

    if (STATE.members.length === 0) {
      chipsHtml += `<span style="font-size:0.8rem; color:#94a3b8;">Add members above to allocate</span>`;
    } else {
      const isAllActive = asgn.is_all;
      chipsHtml += `
        <button class="assign-chip chip-all ${isAllActive ? 'active' : ''}" onclick="toggleAssignAll('${item.id}')">
          All Members
        </button>
      `;

      STATE.members.forEach((m) => {
        const isMemberActive = asgn.assigned_to.has(m);
        chipsHtml += `
          <button class="assign-chip ${isMemberActive ? 'active' : ''}" onclick="toggleAssignMember('${item.id}', '${m}')">
            ${m}
          </button>
        `;
      });
    }
    chipsHtml += `</div>`;

    const activeCount = asgn.assigned_to.size || (STATE.members.length > 0 ? STATE.members.length : 1);
    const perPerson = (item.total_price / activeCount).toFixed(2);

    tr.innerHTML = `
      <td>
        <strong>${item.name}</strong>
        <div style="font-size: 0.78rem; color: #64748b;">Qty: ${item.quantity} &times; INR ${item.unit_price.toFixed(2)}</div>
      </td>
      <td>
        <strong style="font-family: var(--font-mono);">INR ${item.total_price.toFixed(2)}</strong>
      </td>
      <td>${chipsHtml}</td>
      <td>
        <span class="split-cost-badge">INR ${perPerson}/head</span>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function toggleAssignAll(itemId) {
  const asgn = STATE.assignments[itemId];
  asgn.is_all = !asgn.is_all;
  if (asgn.is_all) {
    asgn.assigned_to = new Set(STATE.members);
  } else {
    asgn.assigned_to.clear();
  }
  renderAssignmentTable();
  updateLiveSpendTicker();
}

function toggleAssignMember(itemId, member) {
  const asgn = STATE.assignments[itemId];
  if (asgn.assigned_to.has(member)) {
    asgn.assigned_to.delete(member);
    asgn.is_all = false;
  } else {
    asgn.assigned_to.add(member);
    if (asgn.assigned_to.size === STATE.members.length) {
      asgn.is_all = true;
    }
  }
  renderAssignmentTable();
  updateLiveSpendTicker();
}

function assignAllToEveryone() {
  if (STATE.currentBill) {
    STATE.currentBill.items.forEach((item) => {
      STATE.assignments[item.id] = {
        is_all: true,
        assigned_to: new Set(STATE.members),
      };
    });
    renderAssignmentTable();
    updateLiveSpendTicker();
  }
}

function updateLiveSpendTicker() {
  const ticker = document.getElementById("live-spend-ticker");
  if (STATE.members.length === 0) {
    ticker.style.display = "none";
    return;
  }

  ticker.style.display = "flex";
  ticker.innerHTML = "";

  const memberSpend = {};
  STATE.members.forEach((m) => (memberSpend[m] = 0.0));

  if (STATE.currentBill) {
    STATE.currentBill.items.forEach((item) => {
      const asgn = STATE.assignments[item.id];
      const targets = asgn.assigned_to.size > 0 ? Array.from(asgn.assigned_to) : STATE.members;
      const share = item.total_price / (targets.length || 1);
      targets.forEach((m) => {
        if (memberSpend[m] !== undefined) memberSpend[m] += share;
      });
    });
  }

  STATE.members.forEach((m) => {
    const item = document.createElement("div");
    item.className = "ticker-item";
    const color = getMemberColor(m);
    item.innerHTML = `
      <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${color};"></span>
      <span class="ticker-name">${m}:</span>
      <span class="ticker-val">INR ${memberSpend[m].toFixed(2)}</span>
    `;
    ticker.appendChild(item);
  });
}

// ==========================================
// STEP 4: SETTLEMENT BREAKDOWN
// ==========================================
async function computeFinalSplit() {
  if (STATE.members.length === 0) {
    alert("Please add at least one participant before computing settlement.");
    return;
  }

  const formattedAssignments = STATE.currentBill.items.map((item) => {
    const asgn = STATE.assignments[item.id];
    return {
      item_id: item.id,
      assigned_to: Array.from(asgn.assigned_to),
      is_all: asgn.is_all,
    };
  });

  const payload = {
    bill: STATE.currentBill,
    members: STATE.members,
    assignments: formattedAssignments,
  };

  try {
    const res = await fetch("/api/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Settlement calculation error");
    }

    const result = await res.json();
    STATE.splitResult = result;
    renderFinalBreakdown(result);
    goToStep(4);
  } catch (err) {
    alert(`Settlement Error: ${err.message}`);
  }
}

function renderFinalBreakdown(result) {
  document.getElementById("res-grand-total").textContent = `INR ${result.bill_grand_total.toFixed(2)}`;
  document.getElementById("res-subtotal").textContent = `INR ${STATE.currentBill.metadata.subtotal.toFixed(2)}`;
  
  const taxesObj = STATE.currentBill.metadata.taxes;
  const totalTaxesAndFees = (taxesObj.cgst + taxesObj.sgst + taxesObj.vat + taxesObj.service_charge - taxesObj.discount).toFixed(2);
  document.getElementById("res-taxes").textContent = `INR ${totalTaxesAndFees}`;

  const balanceBadge = document.getElementById("res-balance-badge");
  if (result.is_balanced) {
    balanceBadge.className = "badge badge-success";
    balanceBadge.textContent = "Exact Penny Reconciled";
  } else {
    balanceBadge.className = "badge badge-danger";
    balanceBadge.textContent = "Unbalanced Total";
  }

  const grid = document.getElementById("member-cards-grid");
  grid.innerHTML = "";

  result.members.forEach((member) => {
    const card = document.createElement("div");
    card.className = "member-card";
    const color = getMemberColor(member.member_name);
    const initial = member.member_name.charAt(0).toUpperCase();

    let itemsListHtml = "";
    member.items_consumed.forEach((item) => {
      const sharePct = Math.round(item.split_ratio * 100);
      itemsListHtml += `
        <li>
          <div>
            <span>${item.item_name}</span>
            <span class="item-share-tag">(${sharePct}%)</span>
          </div>
          <span style="font-family: var(--font-mono); font-weight: 600;">INR ${item.member_charge.toFixed(2)}</span>
        </li>
      `;
    });

    card.innerHTML = `
      <div>
        <div class="member-card-header">
          <div class="member-card-user">
            <span class="member-card-avatar" style="background-color: ${color};">${initial}</span>
            <span class="member-card-name">${member.member_name}</span>
          </div>
          <span class="member-card-ratio">${(member.spend_fraction * 100).toFixed(1)}% of subtotal</span>
        </div>

        <ul class="consumed-list">
          ${itemsListHtml}
        </ul>

        <div class="calc-breakdown-box">
          <div class="calc-row">
            <span>Food Subtotal:</span>
            <span>INR ${member.food_subtotal.toFixed(2)}</span>
          </div>
          <div class="calc-row tax-row">
            <span>Proportional GST/VAT:</span>
            <span>+INR ${member.tax_share.toFixed(2)}</span>
          </div>
          ${member.service_charge_share > 0 ? `
            <div class="calc-row">
              <span>Proportional Service Fee:</span>
              <span>+INR ${member.service_charge_share.toFixed(2)}</span>
            </div>
          ` : ''}
          ${member.discount_share > 0 ? `
            <div class="calc-row disc-row">
              <span>Proportional Discount:</span>
              <span>-INR ${member.discount_share.toFixed(2)}</span>
            </div>
          ` : ''}
        </div>
      </div>

      <div class="final-pay-box">
        <span class="final-pay-label">Total Payable:</span>
        <span class="final-pay-amount">INR ${member.final_total.toFixed(2)}</span>
      </div>
    `;
    grid.appendChild(card);
  });
}

function copyWhatsAppFormat() {
  if (!STATE.splitResult) return;
  const result = STATE.splitResult;
  const restName = STATE.currentBill.metadata.restaurant_name || "Receipt";

  let msg = `Bill Settlement: ${restName}\n`;
  msg += `Total Amount: INR ${result.bill_grand_total.toFixed(2)}\n`;
  msg += `------------------------------------\n`;
  result.members.forEach((m) => {
    msg += `• ${m.member_name}: INR ${m.final_total.toFixed(2)} (${(m.spend_fraction * 100).toFixed(0)}% spend ratio)\n`;
  });
  msg += `------------------------------------\n`;
  msg += `Calculated via SmartBill Engine`;

  navigator.clipboard.writeText(msg).then(() => {
    alert("Settlement summary copied to clipboard.");
  });
}

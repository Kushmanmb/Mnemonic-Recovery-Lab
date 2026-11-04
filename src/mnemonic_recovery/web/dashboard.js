import {
  createIcons,
  ShieldCheck,
  RotateCcw,
  Square,
  Check,
  ClipboardList,
  FlaskConical,
  FolderOpen,
  Play,
  LockKeyhole,
  LockKeyholeOpen,
} from "lucide";

const isLoopback =
  window.location.protocol === "http:" &&
  window.location.hostname === "127.0.0.1";

const icons = {
  ShieldCheck,
  RotateCcw,
  Square,
  Check,
  ClipboardList,
  FlaskConical,
  FolderOpen,
  Play,
  LockKeyhole,
  LockKeyholeOpen,
};
const $ = (selector) => document.querySelector(selector);
const grid = $("#word-grid");
let publicPreview = false;
let slots = [];
let dictionary = new Set();
let fixtures = [];
let active = null;
let checks = 0;
let revision = 0;

function paintIcons() {
  createIcons({ icons, attrs: { "aria-hidden": "true" } });
}
function message(text, success = false) {
  $("#result").hidden = false;
  $("#result").textContent = text;
  $("#result").className = `result${success ? " success" : ""}`;
}
function cancelActive() {
  if (active) {
    active.abort();
    active = null;
    $("#progress-status").textContent = "Cancelled";
    $("#progress").value = $("#progress").value || 0;
    message("Cancelled. No word has been confirmed.");
  }
  setBusy(false);
}
function invalidate() {
  revision += 1;
  cancelActive();
  $("#result").hidden = true;
}
function setBusy(busy) {
  $("#cancel").disabled = !busy;
  $("#cancel-fixture").disabled = !busy;
  $("#check").disabled = !isLoopback || busy || !dictionary.size;
  $("#run-fixture").disabled = busy || !fixtures.length;
  $("#load-fixture").disabled = busy || !fixtures.length;
  $("#fixture").disabled = busy || !fixtures.length;
  $("#budget").disabled = busy || !isLoopback;
  for (const id of ["#word-count", "#phrase", "#import"])
    $(id).disabled = !isLoopback;
  for (const id of ["#clear", "#reveal"])
    $(id).disabled = !isLoopback && !publicPreview;
}
function normalized(value) {
  return value.normalize("NFKD").toLowerCase().trim();
}
function update() {
  const missing = [];
  slots.forEach((slot, index) => {
    const word = normalized(slot.input.value);
    const valid = dictionary.has(word);
    slot.root.classList.toggle("is-missing", slot.missing.checked);
    slot.root.classList.toggle("is-locked", slot.locked);
    slot.input.disabled = !isLoopback && !publicPreview;
    slot.input.readOnly = slot.locked;
    slot.missing.disabled = slot.input.disabled || slot.locked;
    slot.lock.disabled = slot.input.disabled || (!valid && !slot.locked);
    slot.lock.setAttribute("aria-pressed", String(slot.locked));
    slot.lock.setAttribute(
      "aria-label",
      `${slot.locked ? "Unlock" : "Lock"} word ${index + 1}`,
    );
    slot.lock.title = `${slot.locked ? "Unlock" : "Lock"} word ${index + 1}`;
    slot.input.setAttribute("aria-invalid", String(Boolean(word) && !valid));
    slot.status.textContent = !word
      ? "Empty"
      : !dictionary.size
        ? "Word list unavailable"
        : !valid
          ? publicPreview
            ? "Use public test words: abandon or about"
            : "Not a BIP-39 English word"
          : slot.locked
            ? "Known word / locked by you"
            : slot.missing.checked
              ? "Candidate / unconfirmed"
              : "BIP-39 word / unlocked";
    slot.status.classList.toggle("invalid", Boolean(word) && !valid);
    if (slot.missing.checked) missing.push(index + 1);
  });
  $("#entered-count").textContent = slots.filter((slot) =>
    slot.input.value.trim(),
  ).length;
  $("#locked-count").textContent = slots.filter((slot) => slot.locked).length;
  $("#missing-count").textContent = missing.length;
  $("#missing-positions").textContent = missing.length
    ? `Missing positions: ${missing.join(", ")}`
    : "No missing positions";
  const estimate = $("#estimate");
  estimate.replaceChildren();
  if (!missing.length) {
    estimate.textContent =
      "No missing positions. Complete candidates can still be checked manually.";
    return;
  }
  const total = 1n << BigInt(11 * missing.length);
  const expected = 1n << BigInt(11 * missing.length - slots.length / 3);
  const counts = document.createElement("p");
  counts.textContent = `${total.toLocaleString()} theoretical combinations; about ${expected.toLocaleString()} checksum-valid combinations expected.`;
  const caveat = document.createElement("p");
  caveat.textContent = `${11 * missing.length - slots.length / 3} effective bits after checksum filtering. An estimate, not a search or proof of correctness.`;
  estimate.append(counts, caveat);
}
function render(length, values = []) {
  grid.replaceChildren();
  slots = Array.from({ length }, (_, index) => {
    const root = document.createElement("div");
    root.className = "word-slot";
    const heading = document.createElement("div");
    heading.className = "slot-heading";
    const number = document.createElement("label");
    number.className = "slot-number";
    number.htmlFor = `word-${index + 1}`;
    number.textContent = String(index + 1).padStart(2, "0");
    const missingLabel = document.createElement("label");
    missingLabel.className = "missing-label";
    const missing = document.createElement("input");
    missing.type = "checkbox";
    missing.checked = !values[index];
    missing.setAttribute("aria-label", `Position ${index + 1} is missing`);
    missingLabel.append(missing, document.createTextNode("Missing"));
    heading.append(number, missingLabel);
    const entry = document.createElement("div");
    entry.className = "word-entry";
    const input = document.createElement("input");
    input.disabled = !isLoopback;
    input.id = `word-${index + 1}`;
    input.type = $("#reveal").checked ? "text" : "password";
    input.value = values[index] || "";
    input.autocomplete = "off";
    input.autocapitalize = "none";
    input.spellcheck = false;
    input.maxLength = 32;
    input.setAttribute("aria-label", `Word ${index + 1}`);
    input.setAttribute("aria-describedby", `status-${index + 1}`);
    input.setAttribute("data-1p-ignore", "");
    input.setAttribute("data-lpignore", "true");
    const lock = document.createElement("button");
    lock.type = "button";
    lock.className = "secondary icon-button";
    lock.innerHTML = '<i data-lucide="lock-keyhole-open"></i>';
    const status = document.createElement("p");
    status.id = `status-${index + 1}`;
    status.className = "word-status";
    entry.append(input, lock);
    root.append(heading, entry, status);
    grid.append(root);
    const slot = { root, input, lock, missing, status, locked: false };
    input.addEventListener("input", () => {
      invalidate();
      update();
    });
    missing.addEventListener("change", () => {
      invalidate();
      update();
    });
    lock.addEventListener("click", () => {
      invalidate();
      slot.locked = !slot.locked;
      if (slot.locked) missing.checked = false;
      lock.innerHTML = `<i data-lucide="${slot.locked ? "lock-keyhole" : "lock-keyhole-open"}"></i>`;
      paintIcons();
      update();
    });
    return slot;
  });
  paintIcons();
  update();
}
function resetProgress() {
  $("#progress").value = 0;
  $("#progress-status").textContent = "Idle";
  $("#progress-count").textContent = "0 checked";
  for (const id of ["#checksum-count", "#match-count", "#rate"])
    $(id).textContent = "0";
}
$("#word-count").addEventListener("change", () => {
  const length = Number($("#word-count").value);
  if (
    length < slots.length &&
    slots.slice(length).some((slot) => slot.input.value || slot.locked) &&
    !window.confirm(
      `Discard positions ${length + 1}-${slots.length} and their locks?`,
    )
  ) {
    $("#word-count").value = String(slots.length);
    return;
  }
  invalidate();
  const values = slots.map((slot) => slot.input.value);
  const states = slots.map((slot) => ({
    locked: slot.locked,
    missing: slot.missing.checked,
  }));
  render(length, values);
  slots.forEach((slot, index) => {
    if (!states[index]) return;
    slot.locked = states[index].locked;
    slot.missing.checked = states[index].missing;
    slot.lock.innerHTML = `<i data-lucide="${slot.locked ? "lock-keyhole" : "lock-keyhole-open"}"></i>`;
  });
  paintIcons();
  update();
  resetProgress();
});
$("#reveal").addEventListener("change", () =>
  slots.forEach((slot) => {
    slot.input.type = $("#reveal").checked ? "text" : "password";
  }),
);
$("#clear").addEventListener("click", () => {
  invalidate();
  $("#phrase").value = "";
  checks = 0;
  $("#candidate-count").textContent = "0 candidates checked";
  $("#reveal").checked = false;
  render(Number($("#word-count").value));
  resetProgress();
});
$("#cancel").addEventListener("click", cancelActive);
$("#cancel-fixture").addEventListener("click", cancelActive);
$("#import").addEventListener("click", () => {
  if (!isLoopback) return;
  const words = normalized($("#phrase").value).split(/\s+/);
  $("#phrase").value = "";
  invalidate();
  if (words.length !== slots.length) {
    message(`Expected ${slots.length} words. No slots were changed.`);
    return;
  }
  slots.forEach((slot, index) => {
    if (!slot.locked) slot.input.value = words[index];
  });
  update();
});
$("#validation-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!isLoopback || active || !dictionary.size) return;
  if (slots.some((slot) => !dictionary.has(normalized(slot.input.value)))) {
    message(
      "Every position needs a BIP-39 English word before checking this candidate.",
    );
    return;
  }
  const controller = new AbortController();
  active = controller;
  const version = revision;
  setBusy(true);
  resetProgress();
  $("#progress-status").textContent = "Checking candidate";
  $("#progress").removeAttribute("value");
  try {
    const response = await fetch("/api/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        phrase: slots.map((slot) => normalized(slot.input.value)).join(" "),
      }),
      cache: "no-store",
      credentials: "same-origin",
      referrerPolicy: "no-referrer",
      signal: controller.signal,
    });
    const data = await response.json();
    if (active !== controller || revision !== version) return;
    if (!response.ok) throw new Error("local validation failed");
    checks += 1;
    $("#candidate-count").textContent =
      `${checks} candidate${checks === 1 ? "" : "s"} checked`;
    $("#progress").max = 1;
    $("#progress").value = 1;
    $("#progress-status").textContent = "Candidate checked";
    $("#progress-count").textContent = "1 checked";
    $("#checksum-count").textContent = data.checksum_valid ? "1" : "0";
    message(
      data.checksum_valid
        ? "Checksum valid. Candidate only: no missing word, phrase correctness, or wallet ownership has been confirmed."
        : "Checksum invalid. This candidate does not satisfy BIP-39.",
      data.checksum_valid === true,
    );
  } catch {
    if (active === controller) {
      $("#progress").value = 0;
      $("#progress-status").textContent = "Interrupted";
      message("Local validation unavailable. No word has been confirmed.");
    }
  } finally {
    if (active === controller) {
      active = null;
      setBusy(false);
    }
  }
});
$("#load-fixture").addEventListener("click", () => {
  const fixture = fixtures.find((item) => item.id === $("#fixture").value);
  if (!fixture) return;
  if (
    slots.some((slot) => slot.input.value || slot.locked) &&
    !window.confirm(
      "Replace the current words and locks with public test material?",
    )
  )
    return;
  invalidate();
  $("#word-count").value = String(fixture.words.length);
  render(fixture.words.length, fixture.words);
  slots.at(-1).missing.checked = true;
  update();
  resetProgress();
});
$("#run-fixture").addEventListener("click", async () => {
  if (!isLoopback) return;
  const fixture = fixtures.find((item) => item.id === $("#fixture").value);
  const positions = slots.flatMap((slot, index) =>
    slot.missing.checked ? [index + 1] : [],
  );
  const budget = Number($("#budget").value);
  if (!fixture || fixture.words.length !== slots.length || !positions.length) {
    message(
      "Select a fixture with this phrase length and at least one missing position.",
    );
    return;
  }
  if (!Number.isInteger(budget) || budget < 1 || budget > 100000) {
    message("Candidate budget must be an integer from 1 to 100,000.");
    return;
  }
  const controller = new AbortController();
  active = controller;
  setBusy(true);
  resetProgress();
  $("#progress").max = Math.min(budget, 2048 ** positions.length);
  $("#progress-status").textContent = "Starting fixture experiment";
  try {
    const response = await fetch("/api/experiment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        fixture: fixture.id,
        missing_positions: positions,
        max_candidates: budget,
      }),
      cache: "no-store",
      credentials: "same-origin",
      referrerPolicy: "no-referrer",
      signal: controller.signal,
    });
    if (!response.ok || !response.body)
      throw new Error("local experiment failed");
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let terminal = false;
    while (true) {
      const { value, done } = await reader.read();
      if (active !== controller) return;
      buffer += decoder.decode(value, { stream: !done });
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines) {
        if (!line) continue;
        const progress = JSON.parse(line);
        $("#progress").value = progress.checked;
        $("#progress-status").textContent = {
          running: "Running public fixture",
          completed: "Completed",
          limit_reached: "Budget reached / partial search",
          cancelled: "Cancelled",
        }[progress.status];
        $("#progress-count").textContent =
          `${progress.checked.toLocaleString()} / ${Math.min(budget, progress.total_candidates).toLocaleString()} checked`;
        $("#checksum-count").textContent = progress.checksum_valid;
        $("#match-count").textContent = progress.fixture_matches;
        $("#rate").textContent = Math.round(
          progress.elapsed_seconds > 0
            ? progress.checked / progress.elapsed_seconds
            : 0,
        ).toLocaleString();
        terminal = progress.status !== "running";
      }
      if (done) break;
    }
    if (!terminal) throw new Error("incomplete run");
    message(
      "Fixture experiment finished. Results apply only to the built-in public fixture; your entered words were not searched or confirmed.",
    );
  } catch {
    if (active === controller) {
      $("#progress-status").textContent = "Interrupted";
      message(
        "Local fixture experiment unavailable or interrupted. No word has been confirmed.",
      );
    }
  } finally {
    if (active === controller) {
      active = null;
      setBusy(false);
    }
  }
});
window.addEventListener("pagehide", () => {
  cancelActive();
  $("#phrase").value = "";
  slots.forEach((slot) => {
    slot.input.value = "";
    slot.locked = false;
  });
});
window.addEventListener("pageshow", (event) => {
  if (event.persisted) {
    invalidate();
    $("#reveal").checked = false;
    render(Number($("#word-count").value));
    checks = 0;
    $("#candidate-count").textContent = "0 candidates checked";
    resetProgress();
  }
});
render(12);
paintIcons();
$("#public-preview").hidden = isLoopback;
$("#start-preview").addEventListener("click", () => {
  if (isLoopback) return;
  publicPreview = true;
  // Public zero-entropy BIP-39 vector vocabulary; no hosted reference/API calls.
  dictionary = new Set(["abandon", "about"]);
  $("#start-preview").hidden = true;
  $("#reference-status").textContent = "Public test vocabulary only";
  $(".local-status").textContent = "PUBLIC TEST PREVIEW";
  invalidate();
  update();
  message(
    "Public test preview ready. Use abandon in positions 1-11 and about in position 12. Checks, imports, and experiments remain disabled; no words are sent.",
  );
});
if (isLoopback) {
  fetch("/api/reference", {
    cache: "no-store",
    credentials: "same-origin",
    referrerPolicy: "no-referrer",
  })
    .then((response) => {
      if (!response.ok) throw new Error("local word list unavailable");
      return response.json();
    })
    .then((data) => {
      dictionary = new Set(data.wordlist);
      fixtures = data.fixtures;
      for (const fixture of fixtures) {
        const option = document.createElement("option");
        option.value = fixture.id;
        option.textContent = `${fixture.id} / ${fixture.words.length} words`;
        $("#fixture").append(option);
      }
      $("#reference-status").textContent = "2,048 English words / local";
      setBusy(false);
      update();
    })
    .catch(() => {
      $("#reference-status").textContent = "Local word list unavailable";
      message(
        "Local reference data could not be loaded. Candidate checks are disabled.",
      );
    });
} else {
  setBusy(false);
  $("#reference-status").textContent = "Non-loopback origin blocked";
  message(
    "Recovery input is disabled on hosted or forwarded origins. Use HTTP loopback on a trusted offline device, or start the public-test-only preview above.",
  );
  $(".local-status").textContent = "RECOVERY INPUT BLOCKED";
  update();
}

"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  if (location.protocol !== "file:") {
    $("workspace").hidden = true;
    $("blocked").hidden = false;
    return;
  }
  const words = BIP39_WORDS;
  if (words.length !== 2048 || new Set(words).size !== 2048) throw Error("Invalid bundled BIP-39 wordlist");
  const indices = new Map(words.map((word, i) => [word, i]));
  let slots = [];
  let visible = false;
  const normalize = (s) => s.normalize("NFKD").toLowerCase().trim();
  const result = (message, kind = "") => {
    $("result").textContent = message;
    $("result").className = kind;
  };
  function update() {
    let entered = 0, locked = 0, missing = 0;
    for (const s of slots) {
      const word = normalize(s.input.value);
      if (word) entered++;
      if (s.locked) locked++;
      if (s.missing.checked) missing++;
      s.root.classList.toggle("missing", s.missing.checked);
      s.root.classList.toggle("locked", s.locked);
      s.input.readOnly = s.locked;
      s.missing.disabled = s.locked;
      s.lock.textContent = s.locked ? "Unlock" : "Lock";
      s.lock.disabled = !s.locked && !indices.has(word);
      s.input.setAttribute("aria-invalid", String(Boolean(word) && !indices.has(word)));
    }
    $("entered").textContent = entered + " entered";
    $("locked").textContent = locked + " locked";
    $("missing").textContent = missing + " missing";
    if (missing) {
      const total = 1n << BigInt(11 * missing);
      const checksumBits = slots.length / 3;
      const valid = total >> BigInt(checksumBits);
      $("estimate").textContent = total.toLocaleString() + " theoretical combinations; approximately " + valid.toLocaleString() + " checksum-valid combinations expected. This is not a search or proof of recovery.";
    } else $("estimate").textContent = "Mark missing positions to see the search-space estimate.";
  }
  function build(length) {
    slots = [];
    $("slots").replaceChildren();
    for (let i = 0; i < length; i++) {
      const root = document.createElement("div");
      root.className = "slot";
      const label = document.createElement("label");
      label.textContent = "WORD " + (i + 1);
      const input = document.createElement("input");
      input.type = visible ? "text" : "password";
      input.autocomplete = "off";
      input.autocapitalize = "none";
      input.spellcheck = false;
      input.id = "word-" + (i + 1);
      label.htmlFor = input.id;
      const controls = document.createElement("div");
      controls.className = "slot-controls";
      const missingLabel = document.createElement("label");
      const missing = document.createElement("input");
      missing.type = "checkbox";
      missingLabel.append(missing, document.createTextNode("Missing"));
      const lock = document.createElement("button");
      lock.type = "button";
      lock.textContent = "Lock";
      const slot = { root, input, missing, lock, locked: false };
      input.addEventListener("input", () => { result(""); update(); });
      missing.addEventListener("change", () => { result(""); update(); });
      lock.addEventListener("click", () => { slot.locked = !slot.locked; result(""); update(); });
      controls.append(missingLabel, lock);
      root.append(label, input, controls);
      $("slots").append(root);
      slots.push(slot);
    }
    update();
    result("");
  }
  function clear() {
    for (const slot of slots) {
      slot.input.value = "";
      slot.locked = false;
      slot.missing.checked = false;
    }
    update();
    result("Session cleared.");
  }
  async function check() {
    const candidate = slots.map(s => normalize(s.input.value));
    const invalid = candidate.map((w,i) => !indices.has(w) ? i+1 : null).filter(Boolean);
    if (invalid.length) { result("Enter a valid BIP-39 English word in every position. Check positions: " + invalid.join(", ") + ".", "bad"); return; }
    if (!globalThis.crypto?.subtle) { result("Secure local cryptography is unavailable in this browser. Use a modern browser with a local file.", "bad"); return; }
    const length = candidate.length;
    const bits = length * 11;
    const entropyBits = bits - length / 3;
    const packed = new Uint8Array(Math.ceil(bits / 8));
    for (let i = 0; i < length; i++) {
      const index = indices.get(candidate[i]);
      for (let bit = 0; bit < 11; bit++) {
        if (index & (1 << (10 - bit))) {
          const position = i * 11 + bit;
          packed[position >> 3] |= 1 << (7 - (position & 7));
        }
      }
    }
    const entropy = packed.slice(0, entropyBits / 8);
    const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", entropy));
    let match = true;
    for (let bit = 0; bit < length / 3; bit++) {
      const position = entropyBits + bit;
      const actual = (packed[position >> 3] >> (7 - (position & 7))) & 1;
      const expected = (digest[bit >> 3] >> (7 - (bit & 7))) & 1;
      if (actual !== expected) match = false;
    }
    packed.fill(0); entropy.fill(0); digest.fill(0);
    result(match ? "BIP-39 checksum valid. This does not confirm wallet ownership or identify missing words." : "BIP-39 checksum invalid. Check the entered words and their order.", match ? "ok" : "bad");
  }
  $("length").addEventListener("change", (event) => {
    if (slots.some(s => s.input.value || s.locked || s.missing.checked) && !confirm("Changing length clears this session. Continue?")) {
      event.target.value = String(slots.length);
      return;
    }
    build(Number(event.target.value));
  });
  $("toggle").addEventListener("click", () => {
    visible = !visible;
    slots.forEach(s => { s.input.type = visible ? "text" : "password"; });
    $("toggle").textContent = visible ? "Hide words" : "Reveal words";
  });
  $("clear").addEventListener("click", () => {
    if (slots.some(s => s.input.value) && !confirm("Clear all entered words?")) return;
    clear();
  });
  $("validate").addEventListener("click", () => { check().catch(() => result("Local validation failed. No words were transmitted.", "bad")); });
  addEventListener("pagehide", () => { for (const s of slots) s.input.value = ""; });
  build(12);
})();
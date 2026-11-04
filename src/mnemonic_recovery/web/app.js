"use strict";

const form = document.querySelector("#validation-form");
const phraseField = document.querySelector("#phrase");
const resultPanel = document.querySelector("#result");
const wordCountField = document.querySelector("#word-count");
const positionGrid = document.querySelector("#position-grid");
const estimatePanel = document.querySelector("#estimate");

function showResult(message, isValid) {
  resultPanel.replaceChildren();
  resultPanel.hidden = false;
  resultPanel.className = `result ${isValid ? "success" : "failure"}`;
  const heading = document.createElement("strong");
  heading.textContent = message;
  resultPanel.append(heading);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const phrase = phraseField.value;
  phraseField.value = "";
  resultPanel.hidden = true;

  if (!phrase.trim()) {
    showResult("Enter a phrase to validate.", false);
    return;
  }

  try {
    const response = await fetch("/api/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phrase }),
      cache: "no-store",
      credentials: "same-origin",
      referrerPolicy: "no-referrer",
    });
    const data = await response.json();
    if (!response.ok) {
      showResult("Validation request was rejected.", false);
      return;
    }

    const invalid = data.invalid_words || [];
    if (invalid.length > 0) {
      showResult(
        `Unknown English words: ${invalid.map((item) => `${item.word} (position ${item.position})`).join(", ")}`,
        false,
      );
    } else if (data.checksum_valid) {
      showResult(
        `${data.word_count} words · checksum valid. This does not confirm wallet ownership or correctness.`,
        true,
      );
    } else if (data.checksum_valid === false) {
      showResult(`${data.word_count} words · checksum invalid.`, false);
    } else {
      showResult(`${data.word_count} words · unsupported phrase length.`, false);
    }
  } catch {
    showResult("Could not reach the local service. The phrase field was cleared.", false);
  }
});

function renderPositions() {
  positionGrid.replaceChildren();
  const wordCount = Number(wordCountField.value);
  for (let position = 1; position <= wordCount; position += 1) {
    const label = document.createElement("label");
    label.className = "position";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = String(position);
    checkbox.setAttribute("aria-label", `Position ${position} is missing`);
    const number = document.createElement("span");
    number.textContent = String(position).padStart(2, "0");
    label.append(checkbox, number);
    positionGrid.append(label);
  }
  updateEstimate();
}

function updateEstimate() {
  const wordCount = Number(wordCountField.value);
  const missingCount = positionGrid.querySelectorAll("input:checked").length;
  if (missingCount === 0) {
    estimatePanel.textContent = "Select at least one missing position to see an estimate.";
    return;
  }

  const checksumBits = wordCount / 3;
  const possible = 1n << BigInt(11 * missingCount);
  const expectedValid = 1n << BigInt(11 * missingCount - checksumBits);
  const formatter = new Intl.NumberFormat();
  estimatePanel.replaceChildren();
  const details = document.createElement("p");
  details.textContent =
    `${missingCount} missing · ${formatter.format(possible)} theoretical combinations · ` +
    `about ${formatter.format(expectedValid)} checksum-valid combinations expected`;
  const complexity = document.createElement("span");
  complexity.textContent = `${11 * missingCount - checksumBits} effective bits after checksum filtering`;
  estimatePanel.append(details, complexity);
}

wordCountField.addEventListener("change", renderPositions);
positionGrid.addEventListener("change", updateEstimate);
renderPositions();

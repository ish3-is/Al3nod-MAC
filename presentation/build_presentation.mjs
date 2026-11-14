import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "file:///C:/Program%20Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1112-737-0_26.1112.737.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const workspaceDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const buildDir = path.join(workspaceDir, ".presentation-build");
const previewDir = path.join(buildDir, "previews");
const outputDir = path.join(workspaceDir, "presentation");
const finalPath = path.join(outputDir, "ISHARA_Presentation.pptx");
const skillDir = "C:/Users/hp/.codex/plugins/cache/openai-primary-runtime/presentations/26.1112.11217/skills/presentations";
const pythonExecutable = "C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1112-737-0_26.1112.737.0_x64__3k8sg7r9htsxt/dependencies/python/python.exe";

const C = { navy: "#07111F", surface: "#101D2D", surface2: "#16263A", teal: "#13D8C3", white: "#F5F7FA", muted: "#91A3B8", line: "#29435E", yellow: "#F6C85F", green: "#4ADE80", red: "#FF6B7A" };
const FONT = "Arial";
const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

function shape(slide, geometry, left, top, width, height, fill = "none", line = "none", radius) {
  return slide.shapes.add({ geometry, position: { left, top, width, height }, fill, line: { style: "solid", fill: line, width: line === "none" ? 0 : 1 }, ...(radius ? { borderRadius: radius } : {}) });
}

function text(slide, value, left, top, width, height, size = 24, color = C.white, bold = false, align = "left") {
  const box = shape(slide, "textbox", left, top, width, height);
  box.text = value;
  box.text.style = { fontFamily: FONT, fontSize: size, color, bold, alignment: align, verticalAlignment: "middle" };
  return box;
}

function baseSlide(title, number) {
  const slide = presentation.slides.add();
  slide.background.fill = C.navy;
  shape(slide, "rect", 0, 0, 1280, 8, C.teal);
  text(slide, "ISHARA", 58, 30, 180, 32, 16, C.teal, true);
  text(slide, title, 58, 72, 1160, 56, 34, C.white, true);
  shape(slide, "rect", 58, 670, 1160, 1, C.line);
  text(slide, "Advanced Software Engineering  |  501446-3", 58, 678, 510, 24, 12, C.muted);
  text(slide, String(number).padStart(2, "0"), 1148, 678, 70, 24, 12, C.muted, false, "right");
  return slide;
}

function addImage(slide, file, left, top, width, height, alt) {
  return fs.readFile(file).then(bytes => slide.images.add({ blob: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), contentType: "image/png", alt, fit: "contain", position: { left, top, width, height }, geometry: "roundRect", borderRadius: "rounded-xl" }));
}

function stat(slide, value, label, left, top, width, color = C.teal) {
  text(slide, value, left, top, width, 58, 38, color, true);
  text(slide, label, left, top + 58, width, 52, 17, C.muted);
}

// 1 Cover and student team
{
  const s = presentation.slides.add();
  s.background.fill = C.navy;
  shape(s, "rect", 0, 0, 18, 720, C.teal);
  text(s, "ISHARA", 72, 64, 310, 52, 28, C.teal, true);
  text(s, "Neural Translation Architecture for Sign Language-Based Cashier Communication", 72, 132, 585, 194, 42, C.white, true);
  text(s, "Advanced Software Engineering  |  501446-3", 74, 344, 540, 34, 18, C.muted);
  text(s, "Dr. Azhar Al-Sufyani", 74, 386, 540, 34, 17, C.white);
  text(s, "Submission: Sunday, November 15, 2026", 74, 432, 540, 30, 15, C.muted);
  shape(s, "roundRect", 716, 66, 500, 570, C.surface, C.line, "rounded-2xl");
  text(s, "STUDENT TEAM", 754, 96, 420, 32, 16, C.teal, true);
  const team = [
    ["السبيعي فاصل العنود", "44501823"], ["السبيعي مفرح عهود", "44501331"], ["الدوسري محمد ابراهيم سارة", "44508026"],
    ["السبيعي مطلق غلا", "44554025"], ["السبيعي بداح رغد", "44502746"], ["الدوسري عامر عبدالرحمن اروى", "44505324"], ["السبيعي مسفر بدراء", "44506241"],
  ];
  team.forEach(([name,id], i) => {
    const y = 148 + i * 65;
    text(s, name, 754, y, 305, 31, 18, C.white, false, "right");
    text(s, id, 1074, y, 100, 31, 16, C.muted, false, "right");
    if (i < team.length - 1) shape(s, "rect", 754, y + 46, 420, 1, C.line);
  });
}

// 2 Problem
{
  const s = baseSlide("Problem Statement", 2);
  text(s, "A cashier interaction often depends on speech, typing, or help from another person.", 70, 166, 720, 96, 32, C.white, true);
  text(s, "For customers who use sign language, this can delay a simple question and create uncertainty at the point of payment.", 70, 282, 720, 92, 23, C.muted);
  shape(s, "roundRect", 870, 170, 330, 380, C.surface, C.line, "rounded-2xl");
  stat(s, "4", "Target cashier phrases", 915, 214, 245);
  stat(s, "1", "Visible Arabic result", 915, 342, 245);
  text(s, "Unknown input stays unknown", 915, 476, 245, 56, 18, C.yellow, true);
}

// 3 Solution
{
  const s = baseSlide("Proposed Solution", 3);
  text(s, "A desktop translation surface beside the cashier workflow", 70, 160, 1110, 52, 30, C.white, true);
  const items = [
    ["01", "Capture", "OpenCV reads live frames without blocking the interface."],
    ["02", "Understand", "Optional hand landmarks form a time sequence for classification."],
    ["03", "Communicate", "A confirmed phrase appears in Arabic; uncertain input is rejected."],
  ];
  items.forEach(([n,h,b], i) => {
    const y = 252 + i * 104;
    text(s, n, 76, y, 70, 62, 28, C.teal, true);
    text(s, h, 168, y, 190, 34, 22, C.white, true);
    text(s, b, 360, y, 800, 54, 19, C.muted);
    shape(s, "rect", 168, y + 75, 992, 1, C.line);
  });
}

// 4 Objectives
{
  const s = baseSlide("System Objectives", 4);
  const objectives = [
    "Secure cashier access with hashed credentials",
    "Responsive live video and optional hand landmarks",
    "Replaceable neural model adapter for verified data",
    "Explicit rejection of low-confidence or unknown input",
    "Clear separation between simulation and real inference",
  ];
  objectives.forEach((item, i) => {
    const y = 164 + i * 86;
    shape(s, "roundRect", 70, y, 58, 58, i === 4 ? C.yellow : C.teal, "none", "rounded-xl");
    text(s, String(i + 1), 70, y, 58, 58, 22, C.navy, true, "center");
    text(s, item, 156, y, 990, 58, 23, C.white, i === 4);
  });
}

// 5 Functional requirements
{
  const s = baseSlide("Functional Requirements", 5);
  const left = ["FR-01 / 02  Login and access guard", "FR-03 / 04  Camera start, stop, live frame", "FR-05 / 06  Landmarks and motion sequence", "FR-07 / 08  Arabic result or unknown"];
  const right = ["FR-09  Reset translation state", "FR-10  Logout and resource cleanup", "FR-11  Project and student information", "FR-12  Missing camera or model handling"];
  [left, right].forEach((items, col) => items.forEach((item, i) => {
    const x = 70 + col * 585;
    const y = 168 + i * 104;
    shape(s, "roundRect", x, y, 535, 76, C.surface, C.line, "rounded-xl");
    text(s, item, x + 24, y + 8, 487, 60, 20, C.white, true);
  }));
}

// 6 Architecture
{
  const s = baseSlide("Neural Translation Architecture", 6);
  const labels = ["Camera\nInput", "Frame\nProcessing", "Landmark\nDetection", "Sequence\nNormalization", "Neural\nClassifier", "Arabic Phrase\nMapping", "Translation\nResult"];
  labels.forEach((label, i) => {
    const x = 40 + i * 174;
    shape(s, "roundRect", x, 235, 148, 112, C.surface, i === 4 ? C.yellow : C.teal, "rounded-xl");
    text(s, label, x + 10, 250, 128, 82, 15, C.white, true, "center");
    if (i < labels.length - 1) shape(s, "rect", x + 148, 290, 26, 3, C.teal);
  });
  shape(s, "roundRect", 390, 430, 500, 112, "#2A2612", C.yellow, "rounded-xl");
  text(s, "Demo Simulation", 420, 447, 440, 36, 22, C.yellow, true, "center");
  text(s, "UI test only. It does not define Saudi Sign Language gestures and has no confidence score.", 430, 488, 420, 44, 16, C.white, false, "center");
}

// 7 Technologies
{
  const s = baseSlide("Technology Stack", 7);
  const rows = [
    ["Python 3.11 / 3.12", "Application language"], ["PySide6", "Primary desktop UI with QThread"], ["OpenCV", "Camera capture and frame conversion"],
    ["MediaPipe", "Optional hand landmarks"], ["TensorFlow / Keras", "Optional LSTM model adapter"], ["SQLite + PBKDF2", "Credential storage"], ["NumPy", "Landmark sequences"], ["unittest / pytest", "Automated verification"],
  ];
  rows.forEach(([tech,role], i) => {
    const col = i % 2, row = Math.floor(i / 2), x = 70 + col * 585, y = 160 + row * 112;
    text(s, tech, x, y, 235, 34, 20, C.teal, true);
    text(s, role, x + 245, y, 290, 48, 18, C.white);
    shape(s, "rect", x, y + 67, 535, 1, C.line);
  });
}

// 8 UI screens
{
  const s = baseSlide("UI Screens from the Running Application", 8);
  await addImage(s, path.join(workspaceDir, "assets/screenshots/01_login.png"), 62, 156, 548, 335, "Actual login screen");
  await addImage(s, path.join(workspaceDir, "assets/screenshots/02_translation.png"), 670, 156, 548, 335, "Actual live translation screen");
  text(s, "Login", 62, 510, 548, 32, 18, C.teal, true, "center");
  text(s, "Live Translation", 670, 510, 548, 32, 18, C.teal, true, "center");
  text(s, "Captured from the functional fallback because package downloads were blocked on the verification host.", 120, 578, 1040, 42, 16, C.muted, false, "center");
}

// 9 Implementation
{
  const s = baseSlide("Implementation", 9);
  await addImage(s, path.join(workspaceDir, "assets/screenshots/03_result.png"), 70, 165, 470, 287, "Actual result screen");
  await addImage(s, path.join(workspaceDir, "assets/screenshots/04_about.png"), 70, 470, 470, 180, "Actual About Project screen");
  text(s, "Module boundaries", 610, 166, 540, 34, 22, C.teal, true);
  const modules = ["core/auth.py   SQLite and password hashing", "core/camera.py   Injectable OpenCV adapter", "ai/hand_tracker.py   Optional MediaPipe landmarks", "ai/translator.py   Model and demo boundaries", "ui/pyside_app.py   Four screens and QThread", "ui/tk_fallback.py   Restricted-environment fallback"];
  modules.forEach((m,i) => {
    text(s, m, 610, 216 + i * 60, 570, 42, 18, i === 3 ? C.yellow : C.white, i === 3);
    shape(s, "rect", 610, 262 + i * 60, 570, 1, C.line);
  });
}

// 10 Testing
{
  const s = baseSlide("Testing and Actual Results", 10);
  stat(s, "13 / 13", "Automated tests passed", 70, 162, 300, C.green);
  stat(s, "PASS", "Timed launch and shutdown", 410, 162, 330, C.green);
  stat(s, "N/A", "Neural metrics: no trained model", 790, 162, 390, C.yellow);
  text(s, "Verified", 72, 332, 200, 34, 22, C.teal, true);
  text(s, "Correct and wrong login\nPBKDF2 password storage\nCamera adapter start, read, stop, and failure\nDemo labeling and unknown-sign behavior\nSession logout and exact student data", 72, 380, 560, 210, 20, C.white);
  text(s, "Environment limit", 700, 332, 260, 34, 22, C.yellow, true);
  text(s, "No physical webcam was exposed to the execution host. Camera behavior passed with injected OpenCV-compatible captures. A real-device check remains required before presentation.", 700, 380, 470, 170, 20, C.white);
}

// 11 Limitations
{
  const s = baseSlide("Limitations and Future Work", 11);
  text(s, "Current limitation", 70, 160, 500, 42, 24, C.yellow, true);
  text(s, "No verified Saudi Sign Language dataset or trained model is included. No accuracy, precision, recall, or F1 score is claimed.", 70, 214, 500, 130, 24, C.white, true);
  text(s, "Next implementation steps", 670, 160, 500, 42, 24, C.teal, true);
  const steps = ["Collect consented, expert-verified recordings", "Split data by person or recording session", "Train and evaluate the LSTM on a held-out test set", "Version the model, labels, preprocessing, and split manifest"];
  steps.forEach((step,i) => {
    text(s, String(i+1).padStart(2,"0"), 670, 224 + i*82, 54, 45, 20, C.teal, true);
    text(s, step, 742, 218 + i*82, 430, 58, 19, C.white);
  });
}

// 12 Conclusion
{
  const s = baseSlide("Conclusion", 12);
  text(s, "ISHARA establishes a working software architecture from secure login and live camera capture to a replaceable neural classifier.", 112, 178, 1056, 136, 34, C.white, true, "center");
  text(s, "The submitted build demonstrates the full desktop workflow without fabricating sign definitions, model accuracy, or hardware results.", 178, 350, 924, 92, 24, C.muted, false, "center");
  shape(s, "roundRect", 438, 500, 404, 72, C.teal, "none", "rounded-xl");
  text(s, "ISHARA  |  إشارة", 438, 500, 404, 72, 25, C.navy, true, "center");
}

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });
for (const [index, slide] of presentation.slides.items.entries()) {
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(previewDir, `slide-${String(index + 1).padStart(2,"0")}.png`), new Uint8Array(await png.arrayBuffer()));
}
const montage = await presentation.export({ format: "webp", montage: true });
await fs.writeFile(path.join(buildDir, "montage.webp"), new Uint8Array(await montage.arrayBuffer()));

const stagingDir = path.join(workspaceDir, ".codex-finalizer");
await fs.mkdir(stagingDir, { recursive: true });
const candidatePath = path.join(stagingDir, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href);
await finalizePresentation({
  explicitTotalSlideCount: 12,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable,
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-heading-fit"],
  fontPolicy: { basis: "design", families: [FONT] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "ISHARA_Presentation.validation.json"),
});
console.log(`Created ${finalPath}`);

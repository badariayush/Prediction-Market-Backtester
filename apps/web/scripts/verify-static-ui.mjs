import { access, readFile } from "node:fs/promises";

const requiredFiles = ["index.html", "styles.css", "app.js"];
for (const file of requiredFiles) {
  await access(file);
}

const html = await readFile("index.html", "utf8");
const js = await readFile("app.js", "utf8");
for (const endpoint of ["/datasets", "/strategies/migrate", "/backtests/run-demo"]) {
  if (!js.includes(endpoint)) {
    throw new Error(`UI is missing API endpoint ${endpoint}`);
  }
}
if (!html.includes("Kalshi Strategy Backtester")) {
  throw new Error("UI title is missing");
}
console.log("static UI verified");

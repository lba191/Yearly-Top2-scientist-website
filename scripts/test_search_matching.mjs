import fs from "node:fs";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../dist/assets/app.js", import.meta.url), "utf8");
const context = {
  console,
  document: { addEventListener() {}, querySelector() { return null; }, querySelectorAll() { return []; } },
  window: {},
};
vm.createContext(context);
vm.runInContext(source, context);

const cases = [
  ["Jian Lei Niu", "Jian Lei Niu"],
  ["Niu Jian Lei", "Jian Lei Niu"],
  ["Jian Lei", "Jianlei Niu"],
  ["Niu Jian", "Jian Lei Niu"],
  ["Jianlei Niu", "Jian Lei Niu"],
  ["Ling Tim Wong", "Ling Tim Wong"],
  ["LT Wong", "Ling Tim Wong"],
  ["L.T. Wong", "Ling Tim Wong"],
  ["Wong LT", "Ling Tim Wong"],
];

for (const [query, candidate] of cases) {
  const score = context.nameMatchScore(query, candidate);
  if (!(score > 0)) throw new Error(`${query} did not match ${candidate}`);
  console.log(`${query} -> ${candidate}: ${score}`);
}

if (context.nameMatchScore("John Smith", "Ling Tim Wong") !== 0) {
  throw new Error("An unrelated name produced a match.");
}

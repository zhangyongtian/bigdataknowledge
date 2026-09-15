
const fs = require('fs');
const path = require('path');

const base = 'd:/datawork/build/en/docs/算法/强化学习';
const files = fs.readdirSync(base, {withFileTypes:true})
  .filter(d => d.isDirectory())
  .map(d => path.join(base, d.name, 'index.html'));

let totalKatex = 0;
let totalAnn = 0;
let totalDisplay = 0;

for (const file of files) {
  const html = fs.readFileSync(file, 'utf8');
  const katex = (html.match(/class="katex"/g) || []).length;
  const ann = (html.match(/application\/x-tex/g) || []).length;
  const display = (html.match(/class="katex-display"/g) || []).length;
  totalKatex += katex; totalAnn += ann; totalDisplay += display;
  const dirName = path.basename(path.dirname(file));
  console.log(`${dirName.padEnd(42)} | katex=${String(katex).padStart(4)} | display=${String(display).padStart(3)} | annotations=${String(ann).padStart(4)}`);
}
console.log('-'.repeat(100));
console.log(`${'TOTAL'.padEnd(42)} | katex=${String(totalKatex).padStart(4)} | display=${String(totalDisplay).padStart(3)} | annotations=${String(totalAnn).padStart(4)}`);
console.log('\n==== 检查关键公式在策略梯度法文档中是否真的渲染为 KaTeX 节点 ====');
const pgDoc = fs.readFileSync(path.join(base, '策略梯度法公式推导', 'index.html'), 'utf8');

// 找"可采样的期望形式"之后 3000 字符
const key = '可采样的期望形式';
const idx = pgDoc.indexOf(key);
const snippet = pgDoc.slice(idx, idx + 4000);
// 统计这段里的 katex / katex-display / 裸露 \nabla 字样
const sKatex = (snippet.match(/class="katex"/g) || []).length;
const sDisplay = (snippet.match(/class="katex-display"/g) || []).length;
const sNablaPlain = (snippet.match(/\\nabla[^_]|\\mathbb\{|\\tag\{2\}|\\Big\[|\\Big\]/g) || []).length;
console.log(`「可采样的期望形式」后 4000 字：katex=${sKatex}，katex-display=${sDisplay}，裸露 LaTeX 命令数（应=0）=${sNablaPlain}`);

console.log('\n==== 检查"本身就是在轨迹分布下"段落 3000 字符 ====');
const p1 = pgDoc.indexOf('本身就是');
const snippet2 = pgDoc.slice(Math.max(0, p1 - 200), p1 + 3000);
const s2Inline = (snippet2.match(/class="math math-inline"/g) || []).length;
const s2Display = (snippet2.match(/class="math math-display"/g) || []).length;
const s2PlainTex = (snippet2.match(/class="[^"]*">\s*\\(nabla|mathbb|sum|prod|Big|E_|tau|P_|pi_|G_|A_)/g) || []).length;
console.log(`段落：math-inline=${s2Inline}，math-display=${s2Display}，裸露反斜杠命令=${s2PlainTex}`);

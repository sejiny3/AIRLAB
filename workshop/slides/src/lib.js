// Shared theme, layouts and slide helpers for the UNBOLT lecture deck (pptxgenjs).
const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');
const React = require('react');
const RDS = require('react-dom/server');
const sharp = require('sharp');
const JSZip = require('jszip');
const fa = require('react-icons/fa');

const REPO = path.resolve(__dirname, '..', '..', '..');
const IMG_DIRS = [path.join(REPO, 'docs'), path.join(__dirname, 'assets')];

const THEME = {
  name: 'UNBOLT Workshop',
  font: 'Malgun Gothic',
  colors: {
    dk1: '1B2430', lt1: 'FFFFFF', dk2: '4A5668', lt2: 'F1F3F6',
    accent1: 'F2711C', accent2: '2A9D8F', accent3: '3D5A80', accent4: 'E9C46A',
    accent5: 'C9D1DC', accent6: 'D62839', hlink: '2A9D8F', folHlink: '3D5A80',
  },
};
const HEX = THEME.colors;
const MONO = 'Consolas';

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE'; // 13.33 x 7.5 in
pres.title = 'UNBOLT 강습회: ROS 2 + MuJoCo로 만드는 주행형 양팔로봇';
pres.author = 'UNBOLT';
pres.theme = { headFontFace: THEME.font, bodyFontFace: THEME.font };
const C = pres.SchemeColor;
const S = pres.shapes;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: 'TITLE',
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: 0.8, y: 1.9, w: 8.6, h: 1.9, fontSize: 40, bold: true, color: C.background1, valign: 'bottom', align: 'left', margin: 0 }, text: '' } },
    { placeholder: { options: { name: 'body', type: 'body', x: 0.8, y: 4.1, w: 8.6, h: 1.6, fontSize: 20, color: C.accent5, valign: 'top', margin: 0 }, text: '' } },
  ],
});
pres.defineSlideMaster({
  title: 'SECTION',
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: 'kicker', type: 'body', x: 0.8, y: 1.2, w: 8.2, h: 0.5, fontSize: 20, bold: true, color: C.accent1, margin: 0 }, text: '' } },
    { placeholder: { options: { name: 'title', type: 'title', x: 0.8, y: 1.8, w: 8.2, h: 1.8, fontSize: 40, bold: true, color: C.background1, valign: 'top', align: 'left', margin: 0 }, text: '' } },
    { placeholder: { options: { name: 'body', type: 'body', x: 0.8, y: 3.9, w: 8.2, h: 2.8, fontSize: 16, color: C.accent5, valign: 'top', margin: 0 }, text: '' } },
  ],
  slideNumber: { x: 12.2, y: 6.95, w: 0.6, h: 0.3, fontSize: 10, color: C.accent5, align: 'right' },
});
pres.defineSlideMaster({
  title: 'CONTENT',
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: 0.6, y: 0.35, w: 10.0, h: 0.85, fontSize: 30, bold: true, color: C.text1, valign: 'middle', align: 'left', margin: 0 }, text: '' } },
    { text: { text: 'UNBOLT 강습회', options: { x: 0.6, y: 6.95, w: 4.0, h: 0.3, fontSize: 10, color: C.text2, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 6.95, w: 0.6, h: 0.3, fontSize: 10, color: C.text2, align: 'right' },
});

// ------------------------------------------------------------------ assets
const ICONS = {};
const ICON_NAMES = ['FaRobot', 'FaClock', 'FaSitemap', 'FaSatelliteDish', 'FaMap', 'FaRoute', 'FaHandPaper', 'FaQrcode',
  'FaBrain', 'FaComments', 'FaGlobe', 'FaCheckCircle', 'FaExclamationTriangle', 'FaTerminal', 'FaLaptop', 'FaCogs',
  'FaLayerGroup', 'FaUndo', 'FaStopCircle', 'FaQuestionCircle', 'FaFlagCheckered', 'FaUsers', 'FaBook', 'FaWrench',
  'FaCube', 'FaEye', 'FaCamera', 'FaMemory', 'FaHdd', 'FaMicrochip', 'FaDollarSign', 'FaKeyboard', 'FaLightbulb',
  'FaSearch', 'FaListOl', 'FaPencilAlt', 'FaCompass', 'FaArrowsAlt', 'FaBox', 'FaTable', 'FaPlay', 'FaHome',
  'FaShieldAlt', 'FaGraduationCap', 'FaLink', 'FaBolt', 'FaRedo', 'FaCrosshairs', 'FaWifi', 'FaFileCode'];
const IMG = {};

async function loadAssets() {
  for (const n of ICON_NAMES) {
    if (!fa[n]) throw new Error('unknown icon ' + n);
    const svg = RDS.renderToStaticMarkup(React.createElement(fa[n], { color: '#FFFFFF', size: 256 }));
    ICONS[n] = 'image/png;base64,' + (await sharp(Buffer.from(svg)).resize(256, 256).png().toBuffer()).toString('base64');
  }
  for (const dir of IMG_DIRS) {
    for (const f of fs.readdirSync(dir)) {
      if (!/\.(png|jpe?g)$/i.test(f)) continue;
      const meta = await sharp(path.join(dir, f)).metadata();
      IMG[f] = { path: path.join(dir, f), w: meta.width, h: meta.height };
    }
  }
}

// ------------------------------------------------------------------ helpers
let objN = 0;
const nm = (p) => `${p}_${++objN}`;
let currentSection = '';

function section(sectionTitle, kicker, title, goals, notes) {
  currentSection = sectionTitle;
  pres.addSection({ title: sectionTitle });
  const s = pres.addSlide({ masterName: 'SECTION', sectionTitle });
  s.addText(kicker, { placeholder: 'kicker' });
  s.addText(title, { placeholder: 'title' });
  s.addText(goals.map((b, i) => ({ text: b, options: { bullet: { indent: 18 }, paraSpaceAfter: 8, breakLine: i < goals.length - 1 } })), { placeholder: 'body' });
  s.addNotes(notes);
  return s;
}
// A content slide; `tag` is the small label at the top right (where in the course this is).
function content(title, tag, notes) {
  const s = pres.addSlide({ masterName: 'CONTENT', sectionTitle: currentSection });
  s.addText(title, { placeholder: 'title' });
  if (tag) pill(s, tag, 10.9, 0.6, 1.8, C.background2, C.text2, 12);
  if (notes) s.addNotes(notes);
  return s;
}
function titleSlide(sectionTitle, title, body, iconName, notes) {
  if (sectionTitle !== currentSection) { currentSection = sectionTitle; pres.addSection({ title: sectionTitle }); }
  const s = pres.addSlide({ masterName: 'TITLE', sectionTitle });
  s.addText(title, { placeholder: 'title' });
  s.addText(body, { placeholder: 'body' });
  circleIcon(s, iconName, 9.9, 2.2, 2.6, C.accent1);
  s.addNotes(notes);
  return s;
}
function text(s, t, o) {
  s.addText(t, Object.assign({ isTextBox: true, fontSize: 16, color: C.text1, valign: 'top', margin: 0.05, objectName: nm('text') }, o));
}
function box(s, x, y, w, h, fill, o = {}) {
  s.addShape(S.ROUNDED_RECTANGLE, Object.assign({ x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: nm('box') }, o));
}
function circleIcon(s, name, x, y, d, fill) {
  s.addShape(S.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: nm('iconbg') });
  const p = d * 0.22;
  s.addImage({ data: ICONS[name], x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, altText: name.replace('Fa', '') + ' 아이콘', objectName: nm('icon') });
}
function pill(s, t, x, y, w, fill, color = C.background1, fontSize = 13) {
  s.addShape(S.ROUNDED_RECTANGLE, { x, y, w, h: 0.36, rectRadius: 0.18, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: nm('pill') });
  text(s, t, { x, y, w, h: 0.36, fontSize, bold: true, color, align: 'center', valign: 'middle', margin: 0 });
}
// Card: tinted box, optional icon, bold heading, body text.
function card(s, { x, y, w, h, head, body, iconName, fill = C.background2, accent = C.accent1, headSize = 18, bodySize = 15, headColor = C.text1, bodyColor = C.text1 }) {
  box(s, x, y, w, h, fill);
  // short cards (callout strips) put the body right under a slimmer heading
  const compact = head && body && h < 1.5;
  const d = compact ? 0.45 : 0.6, top = compact ? 0.12 : 0.25;
  let tx = x + 0.25;
  if (iconName) { circleIcon(s, iconName, x + 0.25, y + top, d, accent); tx = x + 0.4 + d; }
  if (head) text(s, head, { x: tx, y: y + top - (compact ? 0.02 : 0.03), w: x + w - 0.25 - tx, h: d + 0.05, fontSize: compact ? Math.min(headSize, 15) : headSize, bold: true, color: headColor, valign: 'middle' });
  if (body) {
    const by = head ? y + top + d + (compact ? 0.05 : 0.1) : y + 0.25;
    text(s, body, { x: x + 0.25, y: by, w: w - 0.5, h: Math.max(0.35, y + h - by - 0.08), fontSize: bodySize, color: bodyColor });
  }
}
// Callout boxes students learn to recognise: 비유 / 왜? / 주의 / 성공 / 안 되면.
const CALLOUT = {
  analogy: { icon: 'FaLightbulb', accent: C.accent4, head: '비유로 이해하기' },
  why: { icon: 'FaQuestionCircle', accent: C.accent3, head: '왜 그럴까?' },
  warn: { icon: 'FaExclamationTriangle', accent: C.accent6, head: '주의' },
  ok: { icon: 'FaCheckCircle', accent: C.accent2, head: '이렇게 나오면 성공' },
  fail: { icon: 'FaWrench', accent: C.accent6, head: '안 되면' },
  tip: { icon: 'FaBolt', accent: C.accent1, head: '팁' },
};
function callout(s, kind, x, y, w, h, body, head) {
  const k = CALLOUT[kind];
  card(s, { x, y, w, h, head: head || k.head, body, iconName: k.icon, accent: k.accent, headSize: 16, bodySize: 14 });
}
function code(s, src, x, y, w, h, fontSize = 13) {
  box(s, x, y, w, h, C.text1);
  s.addText(src, { isTextBox: true, x: x + 0.2, y: y + 0.15, w: w - 0.4, h: h - 0.3, fontFace: MONO, fontSize, color: 'E8EEF4', valign: 'top', margin: 0, paraSpaceAfter: 2, objectName: nm('code') });
}
function bullets(s, items, x, y, w, h, fontSize = 16, color = C.text1) {
  const arr = items.map((it, i) => {
    const runs = typeof it === 'string' ? { text: it } : it;
    return Object.assign({}, runs, { options: Object.assign({ bullet: { indent: 18 }, paraSpaceAfter: 8, breakLine: i < items.length - 1 }, runs.options || {}) });
  });
  s.addText(arr, { isTextBox: true, x, y, w, h, fontSize, color, valign: 'top', margin: 0.05, objectName: nm('list') });
}
function arrow(s, x1, y1, x2, y2, color = C.text2) {
  const o = { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), line: { color, width: 2, endArrowType: 'triangle' }, objectName: nm('arrow') };
  if (x2 < x1) o.flipH = true;
  if (y2 < y1) o.flipV = true;
  s.addShape(S.LINE, o);
}
function img(s, file, x, y, w, h, alt) {
  const im = IMG[file];
  if (!im) throw new Error('missing image ' + file);
  const k = Math.min(w / im.w, h / im.h);
  const dw = im.w * k, dh = im.h * k;
  s.addImage({ path: im.path, x: x + (w - dw) / 2, y: y + (h - dh) / 2, w: dw, h: dh, altText: alt, objectName: nm('img') });
  return { x: x + (w - dw) / 2, y: y + (h - dh) / 2, w: dw, h: dh };
}
// Numbered label placed on top of a picture (for "this part is ...").
function marker(s, n, x, y) {
  s.addShape(S.OVAL, { x: x - 0.2, y: y - 0.2, w: 0.4, h: 0.4, fill: { color: C.accent1 }, line: { color: C.background1, width: 1.5 }, objectName: nm('mark') });
  text(s, String(n), { x: x - 0.2, y: y - 0.2, w: 0.4, h: 0.4, fontSize: 13, bold: true, color: C.background1, align: 'center', valign: 'middle', margin: 0 });
}
function table(s, rows, x, y, w, colW, fontSize = 14) {
  const head = rows[0].map((t) => ({ text: t, options: { bold: true, color: C.background1, fill: { color: C.text1 } } }));
  const body = rows.slice(1).map((r, i) => r.map((t) => ({ text: t, options: { fill: { color: i % 2 ? C.background1 : C.background2 } } })));
  s.addTable([head, ...body], { x, y, w, colW, fontSize, color: C.text1, valign: 'middle', margin: [0.06, 0.12, 0.06, 0.12], border: { type: 'solid', pt: 0.75, color: HEX.accent5 }, objectName: nm('table') });
}
function step(s, n, head, body, x, y, w, bodyH = 0.75) {
  s.addShape(S.OVAL, { x, y, w: 0.5, h: 0.5, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, objectName: nm('num') });
  text(s, String(n), { x, y, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: C.background1, align: 'center', valign: 'middle', margin: 0 });
  text(s, head, { x: x + 0.7, y: y - 0.02, w: w - 0.7, h: 0.5, fontSize: 17, bold: true, valign: 'middle' });
  if (body) text(s, body, { x: x + 0.7, y: y + 0.5, w: w - 0.7, h: bodyH, fontSize: 14, color: C.text2 });
}
// Row of boxes joined by arrows (a pipeline).
function flow(s, items, x, y, w, h, gap = 0.35, fontSize = 14) {
  const bw = (w - gap * (items.length - 1)) / items.length;
  items.forEach((it, i) => {
    const [label, fill, color] = Array.isArray(it) ? it : [it, C.background2, C.text1];
    const bx = x + i * (bw + gap);
    box(s, bx, y, bw, h, fill);
    text(s, label, { x: bx + 0.05, y, w: bw - 0.1, h, fontSize, bold: true, color, align: 'center', valign: 'middle', margin: 0 });
    if (i < items.length - 1) arrow(s, bx + bw + 0.03, y + h / 2, bx + bw + gap - 0.03, y + h / 2);
  });
}
// "따라 하기" slide body: commands on the left, what you should see on the right.
function lab(s, { cmd, cmdH = 3.4, cmdSize = 13, explain, ok, fail, rightW = 4.5 }) {
  const lw = 12.1 - rightW - 0.3;
  code(s, cmd, 0.6, 1.5, lw, cmdH, cmdSize);
  if (explain) bullets(s, explain, 0.6, 1.5 + cmdH + 0.25, lw, 6.75 - (1.5 + cmdH + 0.25), 15);
  const rx = 0.6 + lw + 0.3;
  const okH = fail ? 2.75 : 5.25;
  if (ok) callout(s, 'ok', rx, 1.5, rightW, okH, ok);
  if (fail) callout(s, 'fail', rx, 1.5 + okH + 0.2, rightW, 5.25 - okH - 0.2, fail);
}
function glossary(s, rows, colW = [2.4, 5.6, 4.1], fontSize = 14) {
  table(s, [['용어', '뜻', '비유'], ...rows], 0.6, 1.5, 12.1, colW, fontSize);
}
// Quiz: questions on the slide, answers in the notes.
function quiz(title, tag, qa, intro) {
  const s = content(title, tag, '정답과 해설\n' + qa.map((q, i) => `${i + 1}. ${q[1]}`).join('\n'));
  if (intro) text(s, intro, { x: 0.6, y: 1.4, w: 12.1, h: 0.45, fontSize: 15, color: C.text2 });
  const y0 = intro ? 2.0 : 1.5;
  const rowH = Math.min(1.1, (6.7 - y0) / qa.length);
  qa.forEach(([q], i) => {
    const y = y0 + i * rowH;
    box(s, 0.6, y, 12.1, rowH - 0.15, C.background2);
    text(s, `Q${i + 1}`, { x: 0.8, y, w: 0.8, h: rowH - 0.15, fontSize: 18, bold: true, color: C.accent1, valign: 'middle' });
    text(s, q, { x: 1.6, y, w: 10.9, h: rowH - 0.15, fontSize: 16, valign: 'middle' });
  });
  return s;
}
// One-slide summary: icon rows.
function summary(title, tag, rows, notes) {
  const s = content(title, tag, notes);
  const rowH = Math.min(1.25, 5.3 / rows.length);
  rows.forEach(([ic, h, b], i) => {
    const y = 1.5 + i * rowH;
    circleIcon(s, ic, 0.6, y + 0.05, 0.7, [C.accent1, C.accent2, C.accent3, C.text1, C.accent6][i % 5]);
    text(s, h, { x: 1.55, y, w: 11.1, h: 0.45, fontSize: 18, bold: true });
    text(s, b, { x: 1.55, y: y + 0.45, w: 11.1, h: rowH - 0.5, fontSize: 15, color: C.text2 });
  });
  return s;
}

// ------------------------------------------------------------------ output
// pptxgenjs writes Office's stock palette into the theme; put ours (and the Korean
// font for East Asian text) in place.
function themeXml(xml) {
  const c = THEME.colors;
  const scheme = `<a:clrScheme name="${THEME.name}">` + Object.keys(c).map((k) => `<a:${k}><a:srgbClr val="${c[k]}"/></a:${k}>`).join('') + '</a:clrScheme>';
  return xml.replace(/<a:clrScheme[\s\S]*?<\/a:clrScheme>/, scheme)
    .replace(/<a:ea typeface="[^"]*"\/>/g, `<a:ea typeface="${THEME.font}"/>`);
}
// PowerPoint breaks Korean text between any two syllables by default. Korean-tagged runs
// (lang ko-KR) plus eaLnBrk="0" on every paragraph make it wrap at spaces instead.
function slideXml(xml) {
  return xml.replace(/<a:pPr(?![^>]*eaLnBrk)(\s|>|\/>)/g, (m, tail) => `<a:pPr eaLnBrk="0"${tail === '>' || tail === '/>' ? tail : ' '}`)
    .replace(/<a:p>(?!<a:pPr)/g, '<a:p><a:pPr eaLnBrk="0"/>')
    .replace(/lang="en-US"(?! altLang)/g, 'lang="ko-KR" altLang="en-US"');
}
async function write(file) {
  await pres.writeFile({ fileName: file });
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  for (const n of Object.keys(zip.files)) {
    if (/^ppt\/theme\/theme\d+\.xml$/.test(n)) zip.file(n, themeXml(await zip.file(n).async('string')));
    else if (/^ppt\/(slides|slideLayouts|slideMasters)\/[^/]+\.xml$/.test(n)) {
      const xml = slideXml(await zip.file(n).async('string'));
      // PowerPoint refuses the whole file for one negative size (the XSD check lets it through)
      const bad = xml.match(/<a:ext cx="-\d+"|<a:ext cx="\d+" cy="-\d+"/);
      if (bad) throw new Error(`${n}: negative shape size ${bad[0]}`);
      zip.file(n, xml);
    }
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' }));
}

module.exports = {
  pres, C, S, HEX, MONO, loadAssets, write,
  section, content, titleSlide, text, box, circleIcon, pill, card, callout, code, bullets, arrow, img, marker,
  table, step, flow, lab, glossary, quiz, summary,
};

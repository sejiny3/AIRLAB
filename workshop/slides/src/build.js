// Build the lecture deck:  cd workshop/slides/src && npm install && node build.js [out.pptx]
const path = require('path');
const L = require('./lib');

const SECTIONS = ['./s0_intro', './s0b_install', './s1_bridge', './s2_nav', './s3_manip', './s4_llm', './s5_end'];
const OUT = process.argv[2] || path.join(__dirname, '..', 'UNBOLT_workshop.pptx');

(async () => {
  await L.loadAssets();
  for (const m of SECTIONS) {
    try { require.resolve(m); } catch { console.warn('skip', m); continue; }
    require(m)();
  }
  await L.write(OUT);
  console.log('wrote', OUT, '-', L.pres.slides.length, 'slides');
})().catch((e) => { console.error(e); process.exit(1); });

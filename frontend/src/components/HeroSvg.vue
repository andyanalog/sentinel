<script setup>
defineProps({
  variant: { type: String, required: true }, // 'home' | 'services' | 'cases' | 'contact'
});

const ticks = Array.from({ length: 12 }, (_, i) => {
  const deg = i * 30;
  const rad = (deg * Math.PI) / 180;
  return {
    x1: 200 + 130 * Math.cos(rad),
    y1: 160 + 130 * Math.sin(rad),
    x2: 200 + 143 * Math.cos(rad),
    y2: 160 + 143 * Math.sin(rad),
  };
});
</script>

<template>
  <div class="hero-svg">
    <!-- HOME: concentric rings + score line -->
    <svg
      v-if="variant === 'home'"
      viewBox="0 0 400 320"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid meet"
      aria-hidden="true"
    >
      <circle class="hc1" cx="200" cy="160" r="130" fill="none" stroke="#ffffff" stroke-width="1" />
      <circle class="hc2" cx="200" cy="160" r="96"  fill="none" stroke="#ffffff" stroke-width="1" />
      <circle class="hc3" cx="200" cy="160" r="62"  fill="none" stroke="#ffffff" stroke-width="1" />
      <circle class="hc4" cx="200" cy="160" r="28"  fill="none" stroke="#ffffff" stroke-width="1" />
      <line
        v-for="(t, i) in ticks"
        :key="i"
        class="htick"
        :x1="t.x1" :y1="t.y1" :x2="t.x2" :y2="t.y2"
        stroke="#ffffff" stroke-opacity="0.22" stroke-width="1"
      />
      <line class="hline" x1="44" y1="160" x2="356" y2="160" stroke="#ffffff" stroke-opacity="0.85" stroke-width="2.5" />
      <g class="hdot">
        <circle class="hdotcircle" cx="269" cy="160" r="5" fill="#ffffff" />
        <text x="278" y="154" fill="#ffffff" fill-opacity="0.45" font-size="10" font-family="monospace">78</text>
        <text x="278" y="167" fill="#ffffff" fill-opacity="0.28" font-size="8"  font-family="monospace">BLOCK</text>
      </g>
    </svg>

    <!-- SERVICES: nested brackets / API frame -->
    <svg
      v-else-if="variant === 'services'"
      viewBox="0 0 400 320"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid meet"
      aria-hidden="true"
    >
      <circle class="sdata" cx="160" cy="160" r="2" fill="#ffffff" fill-opacity="0.5" />
      <g fill="none" stroke="#ffffff" stroke-width="1">
        <polyline class="sb1l" points="80,56 56,56 56,264 80,264"    stroke-opacity="0.14" />
        <polyline class="sb1r" points="320,56 344,56 344,264 320,264" stroke-opacity="0.14" />
        <polyline class="sb2l" points="104,80 80,80 80,240 104,240"   stroke-opacity="0.24" />
        <polyline class="sb2r" points="296,80 320,80 320,240 296,240" stroke-opacity="0.24" />
        <polyline class="sb3l" points="128,104 104,104 104,216 128,216" stroke-opacity="0.37" />
        <polyline class="sb3r" points="272,104 296,104 296,216 272,216" stroke-opacity="0.37" />
        <polyline class="sb4l" points="152,128 128,128 128,192 152,192" stroke-opacity="0.55" />
        <polyline class="sb4r" points="248,128 272,128 272,192 248,192" stroke-opacity="0.55" />
      </g>
      <line class="sline" x1="56" y1="160" x2="344" y2="160" stroke="#ffffff" stroke-opacity="0.85" stroke-width="2.5" />
      <g class="sdot">
        <circle class="sdotc" cx="200" cy="160" r="5" fill="#ffffff" />
      </g>
      <text class="slabel" x="212" y="154" fill="#ffffff" fill-opacity="0.4" font-size="9" font-family="monospace">/v1/evaluate</text>
    </svg>

    <!-- CASES: reputation network graph -->
    <svg
      v-else-if="variant === 'cases'"
      viewBox="0 0 400 320"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid meet"
      aria-hidden="true"
    >
      <g fill="none" stroke="#ffffff" stroke-width="1">
        <line class="ns1" x1="200" y1="160" x2="104" y2="72"  stroke-opacity="0.32" />
        <line class="ns2" x1="200" y1="160" x2="296" y2="72"  stroke-opacity="0.32" />
        <line class="ns3" x1="200" y1="160" x2="68"  y2="200" stroke-opacity="0.32" />
        <line class="ns4" x1="200" y1="160" x2="332" y2="200" stroke-opacity="0.32" />
        <line class="ns5" x1="200" y1="160" x2="148" y2="272" stroke-opacity="0.32" />
        <line class="ns6" x1="200" y1="160" x2="252" y2="272" stroke-opacity="0.32" />
        <g class="ncross">
          <line x1="104" y1="72"  x2="296" y2="72"  stroke-opacity="0.14" />
          <line x1="68"  y1="200" x2="332" y2="200" stroke-opacity="0.14" />
          <line x1="104" y1="72"  x2="68"  y2="200" stroke-opacity="0.10" />
          <line x1="296" y1="72"  x2="332" y2="200" stroke-opacity="0.10" />
          <line x1="148" y1="272" x2="252" y2="272" stroke-opacity="0.14" />
        </g>
      </g>
      <g class="ncross">
        <circle class="nnode1" cx="104" cy="72"  r="4" fill="#ffffff" fill-opacity="0.55" />
        <circle class="nnode1" cx="296" cy="72"  r="4" fill="#ffffff" fill-opacity="0.55" />
        <circle class="nnode1" cx="68"  cy="200" r="4" fill="#ffffff" fill-opacity="0.50" />
        <circle class="nnode1" cx="332" cy="200" r="4" fill="#ffffff" fill-opacity="0.50" />
        <circle class="nnode1" cx="148" cy="272" r="3" fill="#ffffff" fill-opacity="0.40" />
        <circle class="nnode1" cx="252" cy="272" r="3" fill="#ffffff" fill-opacity="0.40" />
      </g>
      <line class="nline" x1="44" y1="160" x2="356" y2="160" stroke="#ffffff" stroke-opacity="0.82" stroke-width="2.5" />
      <circle class="nping" cx="200" cy="160" r="6" fill="none" stroke="#ffffff" stroke-width="1" />
      <circle class="nhub" cx="200" cy="160" r="6" fill="#ffffff" />
    </svg>

    <!-- CONTACT: nested diamonds + cardinal lines -->
    <svg
      v-else-if="variant === 'contact'"
      viewBox="0 0 400 320"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid meet"
      aria-hidden="true"
    >
      <g fill="none" stroke="#ffffff" stroke-width="1">
        <polygon class="dd1" points="200,36 352,160 200,284 48,160"    stroke-opacity="0.10" />
        <polygon class="dd2" points="200,68 320,160 200,252 80,160"    stroke-opacity="0.20" />
        <polygon class="dd3" points="200,100 288,160 200,220 112,160"  stroke-opacity="0.32" />
        <polygon class="dd4" points="200,132 256,160 200,188 144,160"  stroke-opacity="0.50" />
      </g>
      <line class="dlh" x1="44" y1="160" x2="356" y2="160" stroke="#ffffff" stroke-opacity="0.85" stroke-width="2.5" />
      <line class="dlv" x1="200" y1="36" x2="200" y2="284" stroke="#ffffff" stroke-opacity="0.22" stroke-width="1" />
      <g class="ddot">
        <circle cx="200" cy="36"  r="3" fill="#ffffff" fill-opacity="0.35" />
        <circle cx="200" cy="284" r="3" fill="#ffffff" fill-opacity="0.35" />
        <circle cx="48"  cy="160" r="3" fill="#ffffff" fill-opacity="0.35" />
        <circle cx="352" cy="160" r="3" fill="#ffffff" fill-opacity="0.35" />
      </g>
      <circle class="dring" cx="200" cy="160" r="5" fill="none" stroke="#ffffff" stroke-width="1" />
      <circle class="dhub" cx="200" cy="160" r="5" fill="#ffffff" />
    </svg>
  </div>
</template>

<style scoped>
.hero-svg {
  background: #080808;
  border-radius: 20px;
  overflow: hidden;
  aspect-ratio: 4 / 3;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ── HOME ── */
@keyframes hCircleDraw { to { stroke-dashoffset: 0; } }
@keyframes hBreath1 { 0%,100%{opacity:.10} 50%{opacity:.04} }
@keyframes hBreath2 { 0%,100%{opacity:.18} 50%{opacity:.08} }
@keyframes hBreath3 { 0%,100%{opacity:.30} 50%{opacity:.13} }
@keyframes hBreath4 { 0%,100%{opacity:.48} 50%{opacity:.20} }
@keyframes hTickIn  { to { opacity: 1; } }
@keyframes hLineDraw{ to { stroke-dashoffset: 0; } }
@keyframes hDotIn   { to { opacity: 1; } }
@keyframes hDotPulse{ 0%,100%{r:5;opacity:1} 50%{r:7.5;opacity:.6} }
.hc1{stroke-dasharray:820;stroke-dashoffset:820;animation:hCircleDraw 1.4s cubic-bezier(.4,0,.2,1) 0s forwards, hBreath1 5s ease-in-out 1.4s infinite}
.hc2{stroke-dasharray:604;stroke-dashoffset:604;animation:hCircleDraw 1.2s cubic-bezier(.4,0,.2,1) .18s forwards, hBreath2 5s ease-in-out 1.6s infinite}
.hc3{stroke-dasharray:390;stroke-dashoffset:390;animation:hCircleDraw 1.0s cubic-bezier(.4,0,.2,1) .34s forwards, hBreath3 5s ease-in-out 1.8s infinite}
.hc4{stroke-dasharray:176;stroke-dashoffset:176;animation:hCircleDraw 0.7s cubic-bezier(.4,0,.2,1) .48s forwards, hBreath4 5s ease-in-out 2.0s infinite}
.htick{opacity:0;animation:hTickIn .4s ease .85s forwards}
.hline{stroke-dasharray:320;stroke-dashoffset:320;animation:hLineDraw .9s ease .95s forwards}
.hdot{opacity:0;animation:hDotIn .5s ease 1.6s forwards}
.hdotcircle{animation:hDotPulse 2.8s ease-in-out 2.1s infinite}

/* ── SERVICES ── */
@keyframes sBracketDraw { to { stroke-dashoffset: 0; } }
@keyframes sLineDraw   { to { stroke-dashoffset: 0; } }
@keyframes sDotIn      { to { opacity: 1; } }
@keyframes sDotPulse   { 0%,100%{r:5;opacity:1} 50%{r:8;opacity:.55} }
@keyframes sLabelIn    { to { opacity: 1; } }
@keyframes sDataFlash  { 0%{opacity:0;transform:translateX(-8px)} 20%{opacity:.55} 80%{opacity:.55} 100%{opacity:0;transform:translateX(8px)} }
.sb1l{stroke-dasharray:256;stroke-dashoffset:256;animation:sBracketDraw .9s ease 0s forwards}
.sb1r{stroke-dasharray:256;stroke-dashoffset:256;animation:sBracketDraw .9s ease .06s forwards}
.sb2l{stroke-dasharray:208;stroke-dashoffset:208;animation:sBracketDraw .8s ease .18s forwards}
.sb2r{stroke-dasharray:208;stroke-dashoffset:208;animation:sBracketDraw .8s ease .22s forwards}
.sb3l{stroke-dasharray:160;stroke-dashoffset:160;animation:sBracketDraw .7s ease .34s forwards}
.sb3r{stroke-dasharray:160;stroke-dashoffset:160;animation:sBracketDraw .7s ease .38s forwards}
.sb4l{stroke-dasharray:112;stroke-dashoffset:112;animation:sBracketDraw .5s ease .50s forwards}
.sb4r{stroke-dasharray:112;stroke-dashoffset:112;animation:sBracketDraw .5s ease .54s forwards}
.sline{stroke-dasharray:290;stroke-dashoffset:290;animation:sLineDraw .7s ease .85s forwards}
.sdot{opacity:0;animation:sDotIn .4s ease 1.3s forwards}
.sdotc{animation:sDotPulse 2.6s ease-in-out 1.7s infinite}
.slabel{opacity:0;animation:sLabelIn .5s ease 1.5s forwards}
.sdata{animation:sDataFlash 2.4s ease-in-out 2s infinite}

/* ── CASES ── */
@keyframes nSpoke  { from{stroke-dashoffset:160} to{stroke-dashoffset:0} }
@keyframes nCross  { to{opacity:1} }
@keyframes nLine   { to{stroke-dashoffset:0} }
@keyframes nHub    { 0%,100%{r:6;opacity:1} 50%{r:9;opacity:.5} }
@keyframes nPing   { 0%{r:6;opacity:.6} 100%{r:22;opacity:0} }
@keyframes nNodePulse { 0%,100%{opacity:.55} 50%{opacity:.2} }
.ns1{stroke-dasharray:160;stroke-dashoffset:160;animation:nSpoke .6s ease 0s forwards}
.ns2{stroke-dasharray:160;stroke-dashoffset:160;animation:nSpoke .6s ease .12s forwards}
.ns3{stroke-dasharray:140;stroke-dashoffset:140;animation:nSpoke .5s ease .22s forwards}
.ns4{stroke-dasharray:140;stroke-dashoffset:140;animation:nSpoke .5s ease .32s forwards}
.ns5{stroke-dasharray:130;stroke-dashoffset:130;animation:nSpoke .5s ease .42s forwards}
.ns6{stroke-dasharray:130;stroke-dashoffset:130;animation:nSpoke .5s ease .50s forwards}
.ncross{opacity:0;animation:nCross .5s ease .85s forwards}
.nnode1{animation:nNodePulse 3.5s ease-in-out 1.2s infinite}
.nhub{animation:nHub 2.8s ease-in-out 1.5s infinite}
.nping{animation:nPing 2.8s ease-out 1.5s infinite}
.nline{stroke-dasharray:320;stroke-dashoffset:320;animation:nLine .8s ease .9s forwards}

/* ── CONTACT ── */
@keyframes dDiamondIn { to { stroke-dashoffset: 0; } }
@keyframes dDiamondBreath1 { 0%,100%{opacity:.10} 50%{opacity:.04} }
@keyframes dDiamondBreath2 { 0%,100%{opacity:.20} 50%{opacity:.08} }
@keyframes dDiamondBreath3 { 0%,100%{opacity:.32} 50%{opacity:.14} }
@keyframes dDiamondBreath4 { 0%,100%{opacity:.50} 50%{opacity:.22} }
@keyframes dLineH  { to { stroke-dashoffset: 0; } }
@keyframes dLineV  { to { stroke-dashoffset: 0; } }
@keyframes dDotIn  { to { opacity: 1; } }
@keyframes dHubPulse { 0%,100%{r:5;opacity:1} 50%{r:8;opacity:.5} }
@keyframes dRing   { 0%{r:5;opacity:.7} 100%{r:28;opacity:0} }
.dd1{stroke-dasharray:790;stroke-dashoffset:790;animation:dDiamondIn 1.2s ease 0s forwards, dDiamondBreath1 5s ease-in-out 1.4s infinite}
.dd2{stroke-dasharray:606;stroke-dashoffset:606;animation:dDiamondIn 1.0s ease .18s forwards, dDiamondBreath2 5s ease-in-out 1.6s infinite}
.dd3{stroke-dasharray:426;stroke-dashoffset:426;animation:dDiamondIn 0.8s ease .34s forwards, dDiamondBreath3 5s ease-in-out 1.8s infinite}
.dd4{stroke-dasharray:250;stroke-dashoffset:250;animation:dDiamondIn 0.6s ease .50s forwards, dDiamondBreath4 5s ease-in-out 2.0s infinite}
.dlh{stroke-dasharray:315;stroke-dashoffset:315;animation:dLineH .7s ease .85s forwards}
.dlv{stroke-dasharray:250;stroke-dashoffset:250;animation:dLineV .6s ease 1.0s forwards}
.ddot{opacity:0;animation:dDotIn .4s ease 1.3s forwards}
.dhub{animation:dHubPulse 3s ease-in-out 1.8s infinite}
.dring{animation:dRing 3s ease-out 1.8s infinite}

@media (max-width: 900px) {
  .hero-svg { aspect-ratio: 16 / 10; }
}
</style>

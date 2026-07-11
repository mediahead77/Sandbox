// ══════════════════════════════════════════════
//  DATA  –  All 68 irregular verbs
// ══════════════════════════════════════════════
const VERBS = [
  { inf:'babysit',      sp:'babysat',       pp:'babysat',       de:'babysitten' },
  { inf:'be',           sp:'was / were',    pp:'been',          de:'sein' },
  { inf:'become',       sp:'became',        pp:'become',        de:'werden' },
  { inf:'begin',        sp:'began',         pp:'begun',         de:'anfangen, beginnen' },
  { inf:'blow',         sp:'blew',          pp:'blown',         de:'pusten, blasen; wehen' },
  { inf:'break',        sp:'broke',         pp:'broken',        de:'zerbrechen' },
  { inf:'bring',        sp:'brought',       pp:'brought',       de:'(mit)bringen' },
  { inf:'build',        sp:'built',         pp:'built',         de:'bauen' },
  { inf:'buy',          sp:'bought',        pp:'bought',        de:'kaufen' },
  { inf:'choose',       sp:'chose',         pp:'chosen',        de:'(aus)wählen' },
  { inf:'come',         sp:'came',          pp:'come',          de:'(an)kommen' },
  { inf:'cost',         sp:'cost',          pp:'cost',          de:'kosten' },
  { inf:'cut',          sp:'cut',           pp:'cut',           de:'(aus)schneiden' },
  { inf:'do',           sp:'did',           pp:'done',          de:'tun, machen' },
  { inf:'draw',         sp:'drew',          pp:'drawn',         de:'zeichnen' },
  { inf:'drink',        sp:'drank',         pp:'drunk',         de:'trinken' },
  { inf:'drive',        sp:'drove',         pp:'driven',        de:'fahren' },
  { inf:'eat',          sp:'ate',           pp:'eaten',         de:'essen; fressen' },
  { inf:'fall',         sp:'fell',          pp:'fallen',        de:'(hin)fallen' },
  { inf:'feed',         sp:'fed',           pp:'fed',           de:'füttern; ernähren' },
  { inf:'feel',         sp:'felt',          pp:'felt',          de:'fühlen, sich fühlen' },
  { inf:'fight',        sp:'fought',        pp:'fought',        de:'(be)kämpfen' },
  { inf:'find',         sp:'found',         pp:'found',         de:'finden' },
  { inf:'fly',          sp:'flew',          pp:'flown',         de:'fliegen' },
  { inf:'forget',       sp:'forgot',        pp:'forgotten',     de:'vergessen' },
  { inf:'get',          sp:'got',           pp:'got',           de:'bekommen; holen; werden' },
  { inf:'give',         sp:'gave',          pp:'given',         de:'geben' },
  { inf:'go',           sp:'went',          pp:'gone',          de:'gehen, fahren' },
  { inf:'grow (up)',    sp:'grew (up)',      pp:'grown (up)',    de:'(auf)wachsen' },
  { inf:'hang out',     sp:'hung out',      pp:'hung out',      de:'rumhängen, abhängen' },
  { inf:'have',         sp:'had',           pp:'had',           de:'haben; etw. essen' },
  { inf:'hear',         sp:'heard',         pp:'heard',         de:'hören' },
  { inf:'hit',          sp:'hit',           pp:'hit',           de:'treffen, schlagen' },
  { inf:'hurt',         sp:'hurt',          pp:'hurt',          de:'verletzen; wehtun' },
  { inf:'keep',         sp:'kept',          pp:'kept',          de:'behalten; aufbewahren' },
  { inf:'know',         sp:'knew',          pp:'known',         de:'wissen; kennen' },
  { inf:'leave',        sp:'left',          pp:'left',          de:'lassen, verlassen' },
  { inf:'lose',         sp:'lost',          pp:'lost',          de:'verlieren' },
  { inf:'make',         sp:'made',          pp:'made',          de:'machen, herstellen' },
  { inf:'mean',         sp:'meant',         pp:'meant',         de:'bedeuten, meinen' },
  { inf:'meet',         sp:'met',           pp:'met',           de:'(sich) treffen' },
  { inf:'pay',          sp:'paid',          pp:'paid',          de:'(be)zahlen' },
  { inf:'put',          sp:'put',           pp:'put',           de:'legen, stellen, stecken' },
  { inf:'read',         sp:'read',          pp:'read',          de:'lesen' },
  { inf:'ride',         sp:'rode',          pp:'ridden',        de:'reiten; (Rad) fahren' },
  { inf:'run',          sp:'ran',           pp:'run',           de:'rennen, laufen' },
  { inf:'say',          sp:'said',          pp:'said',          de:'sagen' },
  { inf:'see',          sp:'saw',           pp:'seen',          de:'sehen' },
  { inf:'sell',         sp:'sold',          pp:'sold',          de:'verkaufen' },
  { inf:'send',         sp:'sent',          pp:'sent',          de:'senden, schicken' },
  { inf:'set',          sp:'set',           pp:'set',           de:'stellen, legen, setzen' },
  { inf:'show',         sp:'showed',        pp:'shown',         de:'zeigen' },
  { inf:'sing',         sp:'sang',          pp:'sung',          de:'singen' },
  { inf:'sit',          sp:'sat',           pp:'sat',           de:'sitzen; sich setzen' },
  { inf:'sleep',        sp:'slept',         pp:'slept',         de:'schlafen' },
  { inf:'speak',        sp:'spoke',         pp:'spoken',        de:'sprechen' },
  { inf:'spend',        sp:'spent',         pp:'spent',         de:'(Geld) ausgeben' },
  { inf:'stand',        sp:'stood',         pp:'stood',         de:'stehen' },
  { inf:'steal',        sp:'stole',         pp:'stolen',        de:'stehlen, rauben' },
  { inf:'swim',         sp:'swam',          pp:'swum',          de:'schwimmen' },
  { inf:'take',         sp:'took',          pp:'taken',         de:'(mit)nehmen; bringen' },
  { inf:'teach',        sp:'taught',        pp:'taught',        de:'lehren, unterrichten' },
  { inf:'tell',         sp:'told',          pp:'told',          de:'sagen; erzählen, berichten' },
  { inf:'think',        sp:'thought',       pp:'thought',       de:'denken, glauben, meinen' },
  { inf:'understand',   sp:'understood',    pp:'understood',    de:'verstehen' },
  { inf:'upset',        sp:'upset',         pp:'upset',         de:'jn. aufregen, ärgern' },
  { inf:'wear',         sp:'wore',          pp:'worn',          de:'tragen, anhaben (Kleidung)' },
  { inf:'win',          sp:'won',           pp:'won',           de:'gewinnen' },
  { inf:'write',        sp:'wrote',         pp:'written',       de:'schreiben' },
];

// ══════════════════════════════════════════════
//  GLOBAL STATE
// ══════════════════════════════════════════════
let totalScore = 0;
let globalStreak = 0;
let learnedSet = new Set(JSON.parse(localStorage.getItem('verbhero_learned') || '[]'));

function saveState() {
  localStorage.setItem('verbhero_learned', JSON.stringify([...learnedSet]));
}

function updateHeader() {
  document.getElementById('hdr-score').textContent = totalScore;
  document.getElementById('hdr-streak').textContent = globalStreak;
  document.getElementById('hdr-learned').textContent = learnedSet.size;
  const pct = Math.round(learnedSet.size / VERBS.length * 100);
  document.getElementById('home-progress-bar').style.width = pct + '%';
  document.getElementById('home-progress-label').textContent =
    `${learnedSet.size} von ${VERBS.length} Verben gelernt`;
}

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function goHome() {
  updateHeader();
  showScreen('home');
}

// ══════════════════════════════════════════════
//  HELPERS
// ══════════════════════════════════════════════
function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function normalize(s) {
  return s.trim().toLowerCase().replace(/\s+/g, ' ');
}

// ══════════════════════════════════════════════
//  FLASHCARDS
// ══════════════════════════════════════════════
let fcDeck = [];
let fcIdx = 0;
let fcFlipped = false;
let fcSeen = new Set();

function startFlashcards() {
  fcDeck = [...VERBS];
  fcIdx = 0;
  fcSeen = new Set();
  fcFlipped = false;
  buildDots();
  renderFlashcard();
  showScreen('flashcard');
}

function buildDots() {
  const dots = document.getElementById('fc-dots');
  dots.innerHTML = fcDeck.map((_, i) => `<div class="dot" id="dot-${i}"></div>`).join('');
}

function renderFlashcard() {
  const v = fcDeck[fcIdx];
  document.getElementById('fc-front-verb').textContent = v.inf;
  document.getElementById('fc-front-de').textContent = v.de;
  document.getElementById('fc-b-inf').textContent = v.inf;
  document.getElementById('fc-b-sp').textContent = v.sp;
  document.getElementById('fc-b-pp').textContent = v.pp;
  document.getElementById('fc-back-de').textContent = v.de;
  document.getElementById('fc-counter').textContent = `${fcIdx + 1} / ${fcDeck.length}`;
  const card = document.getElementById('fc-card');
  if (fcFlipped) { card.classList.add('flipped'); } else { card.classList.remove('flipped'); }
  // dots
  document.querySelectorAll('#fc-dots .dot').forEach((d, i) => {
    d.className = 'dot' + (fcSeen.has(i) ? ' seen' : '') + (i === fcIdx ? ' current' : '');
  });
}

function flipCard() {
  fcFlipped = !fcFlipped;
  if (fcFlipped) fcSeen.add(fcIdx);
  renderFlashcard();
}

function fcMove(dir) {
  fcFlipped = false;
  fcIdx = (fcIdx + dir + fcDeck.length) % fcDeck.length;
  renderFlashcard();
}

function fcShuffle() {
  fcDeck = shuffle(VERBS);
  fcIdx = 0;
  fcFlipped = false;
  fcSeen = new Set();
  buildDots();
  renderFlashcard();
}

// ══════════════════════════════════════════════
//  QUIZ
// ══════════════════════════════════════════════
let qDeck = [];
let qIdx = 0;
let qCorrect = 0;
let qWrong = 0;
let qStreak = 0;
let qChecked = false;
let qGivenField = ''; // 'inf' | 'sp' | 'pp'
let qAskFields = []; // fields to fill in

function startQuiz() {
  qDeck = shuffle(VERBS);
  qIdx = 0;
  qCorrect = 0;
  qWrong = 0;
  qStreak = 0;
  qChecked = false;
  updateQuizScores();
  renderQuiz();
  showScreen('quiz');
}

function updateQuizScores() {
  document.getElementById('q-correct').textContent = qCorrect;
  document.getElementById('q-wrong').textContent = qWrong;
  document.getElementById('q-streak').innerHTML = `<span class="streak-fire">🔥</span>${qStreak}`;
}

function renderQuiz() {
  if (qIdx >= qDeck.length) { showResult('quiz'); return; }
  qChecked = false;
  const v = qDeck[qIdx];
  // Randomly pick which form to show
  const fields = ['inf','sp','pp'];
  const given = fields[Math.floor(Math.random() * 3)];
  qGivenField = given;
  qAskFields = fields.filter(f => f !== given);
  const labels = { inf:'Infinitive', sp:'Simple Past', pp:'Past Participle' };
  document.getElementById('q-given-label').textContent = labels[given];
  document.getElementById('q-given-word').textContent = v[given];
  document.getElementById('q-german').textContent = '🇩🇪 ' + v.de;
  document.getElementById('quiz-counter').textContent = `${qIdx + 1} / ${qDeck.length}`;
  const inp = document.getElementById('q-inputs');
  inp.innerHTML = qAskFields.map(f => `
    <div class="input-group">
      <label>${labels[f]}</label>
      <input type="text" id="q-inp-${f}" placeholder="…" autocomplete="off" autocorrect="off" spellcheck="false"
             onkeydown="if(event.key==='Enter') checkAnswer()">
      <div class="answer-hint" id="q-hint-${f}"></div>
    </div>
  `).join('');
  document.getElementById('q-check-btn').textContent = 'Prüfen ✓';
  document.getElementById('q-check-btn').disabled = false;
  document.getElementById('q-reveal-btn').disabled = false;
  // focus first input
  setTimeout(() => { const first = document.getElementById(`q-inp-${qAskFields[0]}`); if (first) first.focus(); }, 50);
}

function checkAnswer() {
  if (qChecked) { nextQuiz(); return; }
  const v = qDeck[qIdx];
  let allCorrect = true;
  qAskFields.forEach(f => {
    const inp = document.getElementById(`q-inp-${f}`);
    const hint = document.getElementById(`q-hint-${f}`);
    const userVal = normalize(inp.value);
    const correct = v[f].split('/').map(s => normalize(s));
    const ok = correct.some(c => userVal === c);
    inp.classList.remove('correct','wrong','revealed');
    hint.className = 'answer-hint';
    if (ok) {
      inp.classList.add('correct');
      hint.classList.add('correct');
      hint.textContent = '✓ Richtig!';
    } else {
      inp.classList.add('wrong');
      hint.classList.add('wrong');
      hint.textContent = `✗ Richtig: ${v[f]}`;
      allCorrect = false;
      inp.parentElement.classList.add('shake');
      setTimeout(() => inp.parentElement.classList.remove('shake'), 400);
    }
  });
  qChecked = true;
  if (allCorrect) {
    qCorrect++;
    qStreak++;
    if (qStreak > globalStreak) globalStreak = qStreak;
    totalScore += 10 + (qStreak > 2 ? 5 : 0);
    learnedSet.add(v.inf);
    saveState();
    document.getElementById('quiz-counter').classList.add('glow-green');
    setTimeout(() => document.getElementById('quiz-counter').classList.remove('glow-green'), 400);
  } else {
    qWrong++;
    qStreak = 0;
  }
  updateQuizScores();
  updateHeader();
  document.getElementById('q-check-btn').textContent = 'Weiter →';
}

function revealAnswer() {
  if (qChecked) return;
  const v = qDeck[qIdx];
  qAskFields.forEach(f => {
    const inp = document.getElementById(`q-inp-${f}`);
    const hint = document.getElementById(`q-hint-${f}`);
    inp.value = v[f];
    inp.classList.remove('correct','wrong');
    inp.classList.add('revealed');
    hint.className = 'answer-hint revealed';
    hint.textContent = `→ ${v[f]}`;
  });
  qChecked = true;
  qWrong++;
  qStreak = 0;
  updateQuizScores();
  document.getElementById('q-check-btn').textContent = 'Weiter →';
  document.getElementById('q-reveal-btn').disabled = true;
}

function nextQuiz() {
  qIdx++;
  renderQuiz();
}

// ══════════════════════════════════════════════
//  MULTIPLE CHOICE
// ══════════════════════════════════════════════
let mcDeck = [];
let mcIdx = 0;
let mcCorrect = 0;
let mcWrong = 0;
let mcStreak = 0;
let mcAnswered = false;
let mcAskField = '';

function startMChoice() {
  mcDeck = shuffle(VERBS);
  mcIdx = 0;
  mcCorrect = 0;
  mcWrong = 0;
  mcStreak = 0;
  mcAnswered = false;
  updateMCScores();
  renderMC();
  showScreen('mchoice');
}

function updateMCScores() {
  document.getElementById('mc-correct').textContent = mcCorrect;
  document.getElementById('mc-wrong').textContent = mcWrong;
  document.getElementById('mc-streak').innerHTML = `<span class="streak-fire">🔥</span>${mcStreak}`;
}

function renderMC() {
  if (mcIdx >= mcDeck.length) { showResult('mchoice'); return; }
  mcAnswered = false;
  const v = mcDeck[mcIdx];
  document.getElementById('mc-counter').textContent = `${mcIdx + 1} / ${mcDeck.length}`;
  // pick given field and ask field
  const fields = ['inf','sp','pp'];
  const givenField = fields[Math.floor(Math.random() * 3)];
  mcAskField = fields.filter(f => f !== givenField)[Math.floor(Math.random() * 2)];
  const labels = { inf:'Infinitive', sp:'Simple Past', pp:'Past Participle' };
  document.getElementById('mc-given-label').textContent = labels[givenField];
  document.getElementById('mc-given-word').textContent = v[givenField];
  document.getElementById('mc-given-de').textContent = '🇩🇪 ' + v.de;
  document.getElementById('mc-ask-form').textContent = labels[mcAskField];
  // build 4 options: 1 correct + 3 wrong
  const correctAnswer = v[mcAskField];
  const distractors = shuffle(VERBS.filter(x => x.inf !== v.inf))
    .slice(0, 3)
    .map(x => x[mcAskField]);
  const opts = shuffle([correctAnswer, ...distractors]);
  const optContainer = document.getElementById('mc-options');
  optContainer.innerHTML = opts.map(o => `
    <div class="mc-option" onclick="mcSelect(this, '${escHtml(o)}', '${escHtml(correctAnswer)}')">${escHtml(o)}</div>
  `).join('');
}

function escHtml(s) { return s.replace(/'/g, "\\'").replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function mcSelect(el, chosen, correct) {
  if (mcAnswered) { mcIdx++; renderMC(); return; }
  mcAnswered = true;
  document.querySelectorAll('.mc-option').forEach(o => o.classList.add('disabled'));
  if (chosen === correct) {
    el.classList.add('correct');
    mcCorrect++;
    mcStreak++;
    if (mcStreak > globalStreak) globalStreak = mcStreak;
    totalScore += 5 + (mcStreak > 2 ? 3 : 0);
    learnedSet.add(mcDeck[mcIdx].inf);
    saveState();
  } else {
    el.classList.add('wrong');
    el.classList.add('shake');
    // highlight correct
    document.querySelectorAll('.mc-option').forEach(o => {
      if (o.textContent === correct) o.classList.add('correct');
    });
    mcWrong++;
    mcStreak = 0;
  }
  updateMCScores();
  updateHeader();
  // auto-advance after 1.2s
  setTimeout(() => { mcIdx++; renderMC(); }, 1200);
}

// ══════════════════════════════════════════════
//  VERB LIST
// ══════════════════════════════════════════════
function buildVerbList() {
  const items = document.getElementById('verb-list-body');
  items.innerHTML = VERBS.map(v => `
    <div class="verb-row-item">
      <span class="inf">${learnedSet.has(v.inf) ? '<span class="learned-badge"></span>' : ''}${v.inf}</span>
      <span class="sp">${v.sp}</span>
      <span class="pp">${v.pp}</span>
      <span class="de">${v.de}</span>
    </div>
  `).join('');
}

function filterVerbs() {
  const q = document.getElementById('search-input').value.toLowerCase();
  const rows = document.querySelectorAll('.verb-row-item');
  rows.forEach((row, i) => {
    const v = VERBS[i];
    const match = v.inf.includes(q) || v.sp.includes(q) || v.pp.includes(q) || v.de.toLowerCase().includes(q);
    row.style.display = match ? '' : 'none';
  });
}

// Rebuild on screen open
const origShowScreen = showScreen;
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  if (id === 'verblist') buildVerbList();
}

// ══════════════════════════════════════════════
//  RESULTS
// ══════════════════════════════════════════════
function showResult(mode) {
  let c, w;
  if (mode === 'quiz') { c = qCorrect; w = qWrong; }
  else { c = mcCorrect; w = mcWrong; }
  const total = c + w;
  const pct = total > 0 ? Math.round(c / total * 100) : 0;
  let emoji, title;
  if (pct >= 90)      { emoji = '🏆'; title = 'Excellent!'; }
  else if (pct >= 70) { emoji = '🎉'; title = 'Super gemacht!'; }
  else if (pct >= 50) { emoji = '💪'; title = 'Gut versucht!'; }
  else                { emoji = '📚'; title = 'Üben, üben, üben!'; }
  document.getElementById('res-emoji').textContent = emoji;
  document.getElementById('res-title').textContent = title;
  document.getElementById('res-sub').textContent = `${pct}% der Verben richtig beantwortet`;
  document.getElementById('res-correct').textContent = c;
  document.getElementById('res-wrong').textContent = w;
  document.getElementById('res-pct').textContent = pct + '%';
  document.getElementById('result-overlay').classList.remove('hidden');
  document.getElementById('result-overlay')._mode = mode;
}

function closeResult() {
  document.getElementById('result-overlay').classList.add('hidden');
  const mode = document.getElementById('result-overlay')._mode;
  if (mode === 'quiz') startQuiz();
  else startMChoice();
}

// ══════════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════════
updateHeader();
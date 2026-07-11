# Graph Report - /home/user/Sandbox  (2026-07-11)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 35 nodes · 70 edges · 6 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dc35bd8f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5

## God Nodes (most connected - your core abstractions)
1. `showScreen()` - 6 edges
2. `startQuiz()` - 6 edges
3. `checkAnswer()` - 6 edges
4. `startMChoice()` - 6 edges
5. `renderMC()` - 6 edges
6. `shuffle()` - 5 edges
7. `renderFlashcard()` - 5 edges
8. `mcSelect()` - 5 edges
9. `updateHeader()` - 4 edges
10. `startFlashcards()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `goHome()` --calls--> `showScreen()`  [EXTRACTED]
  _app_script.js → _app_script.js  _Bridges community 4 → community 1_
- `startMChoice()` --calls--> `showScreen()`  [EXTRACTED]
  _app_script.js → _app_script.js  _Bridges community 4 → community 2_
- `startQuiz()` --calls--> `showScreen()`  [EXTRACTED]
  _app_script.js → _app_script.js  _Bridges community 4 → community 3_
- `startQuiz()` --calls--> `shuffle()`  [EXTRACTED]
  _app_script.js → _app_script.js  _Bridges community 2 → community 3_
- `startFlashcards()` --calls--> `renderFlashcard()`  [EXTRACTED]
  _app_script.js → _app_script.js  _Bridges community 4 → community 5_

## Import Cycles
- None detected.

## Communities (6 total, 0 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.22
Nodes (7): fcDeck, fcSeen, learnedSet, mcDeck, qAskFields, qDeck, VERBS

### Community 1 - "Community 1"
Cohesion: 0.33
Nodes (7): checkAnswer(), goHome(), mcSelect(), normalize(), saveState(), updateHeader(), updateMCScores()

### Community 2 - "Community 2"
Cohesion: 0.40
Nodes (6): closeResult(), escHtml(), fcShuffle(), renderMC(), shuffle(), startMChoice()

### Community 3 - "Community 3"
Cohesion: 0.33
Nodes (6): nextQuiz(), renderQuiz(), revealAnswer(), showResult(), startQuiz(), updateQuizScores()

### Community 4 - "Community 4"
Cohesion: 0.50
Nodes (4): buildDots(), buildVerbList(), showScreen(), startFlashcards()

### Community 5 - "Community 5"
Cohesion: 0.67
Nodes (3): fcMove(), flipCard(), renderFlashcard()

## Knowledge Gaps
- **7 isolated node(s):** `VERBS`, `learnedSet`, `fcDeck`, `fcSeen`, `qDeck` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `checkAnswer()` connect `Community 1` to `Community 0`, `Community 3`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Why does `showScreen()` connect `Community 4` to `Community 0`, `Community 1`, `Community 2`, `Community 3`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Why does `startQuiz()` connect `Community 3` to `Community 0`, `Community 2`, `Community 4`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **What connects `VERBS`, `learnedSet`, `fcDeck` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._
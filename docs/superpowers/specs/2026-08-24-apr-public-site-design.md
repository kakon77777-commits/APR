# APR Public Site Design

Date: 2026-08-24

Status: Approved by the user

## 1. Objective

Build a public, bilingual, static APR research site at `https://apr.evemisslab.com/` and add an APR entry to the existing `https://evemisslab.com/` index.

The site explains Adaptive Perceptual Reading, exposes a deterministic browser-only educational lab, indexes the theory and runtime evidence, and documents the planned local MCP boundary. It does not host APR Runtime, accept user data, call a model Provider, or expose the user's local computer.

## 2. Approved scope

This design covers only the public website and its parent-index entry.

Included:

- English pages at the root and Traditional Chinese pages under `/zh-TW/`;
- a static overview, runtime guide, paper index, status/evidence page and MCP architecture guide;
- an offline deterministic APR decision lab generated from bounded APR fixtures;
- machine-readable discovery files;
- an assets-only Cloudflare deployment for `apr.evemisslab.com`;
- one bilingual APR entry on `evemisslab.com`.

Deferred:

- the local MCP server implementation;
- desktop, browser or window-control tests;
- any remote APR Runtime API;
- any OpenAI, Anthropic, Google Vertex or other paid Provider integration;
- account, login, analytics, cookies, comments, uploads or server-side persistence.

The user's existing computer must not be foregrounded or controlled during the website-only implementation. Interactive browser acceptance and production deployment occur only when the user later says testing may begin.

## 3. Repository and release boundaries

The canonical runtime checkout is `D:\Ai\work together\APR`.

The approved website design is based on commit `d1722ec`, which contains the hosted semantic and Google Vertex image-generation work currently proposed by Draft PR #1. The site must not be deployed from an unmerged feature branch. Before production publication, one of these equivalent conditions must be true:

1. Draft PR #1 is validated, reviewed and merged, then the website branch is rebased or rebuilt from the resulting `main`; or
2. the website PR contains the same reviewed runtime commits and is merged as one explicitly accepted release.

The parent-index checkout is `D:\Ai\網站群\evemisslab`, remote `kakon77777-commits/evemisslab-com`. It remains a separate repository and receives only the minimal bilingual index entry and APR tone token.

The APR repository does not currently grant an open-source licence. Publishing the website or repository does not silently add reuse rights. Site copy must describe the runtime as public research infrastructure, not as licensed open-source software, until the owner deliberately adds a `LICENSE`.

## 4. Chosen architecture

The site lives inside the APR repository under `site/` and uses a standard-library Python build plus static HTML, CSS and JavaScript.

```text
APR repository
├── apr_runtime/                  canonical Python runtime
├── papers/                       APR-01 through APR-07
├── docs/                         runtime, theory and evidence
├── site/
│   ├── build.py                  deterministic static-site compiler
│   ├── src/
│   │   ├── content.py            bilingual curated copy and navigation
│   │   ├── demo_export.py        bounded fixture exporter using APR core
│   │   └── assets/
│   │       ├── styles.css        APR-specific visual system
│   │       └── app.js            navigation and offline lab interaction
│   ├── package.json              pinned Wrangler deploy dependency only
│   ├── wrangler.jsonc            assets-only Worker and custom domain
│   └── dist/                     generated, ignored output
└── tests/
    └── test_site_build.py        static build and fixture-contract tests
```

No frontend framework, remote font, CDN asset, client package, Worker API handler or server-side rendering is introduced. Node is used only to run a pinned Wrangler release for deployment.

The Worker delegates every request to static assets. It has no environment variables, secrets, D1, KV, R2, Durable Objects, service bindings or outbound fetch path.

## 5. Information architecture

Every human-facing page has an English and Traditional Chinese form with equivalent navigation and factual content.

| English | Traditional Chinese | Purpose |
|---|---|---|
| `/` | `/zh-TW/` | Concise APR introduction, closed loop, current status and entry points |
| `/runtime/` | `/zh-TW/runtime/` | Evidence, belief, need, budget, observation, action gate, verification and recovery |
| `/lab/` | `/zh-TW/lab/` | Offline deterministic APR decision lab |
| `/papers/` | `/zh-TW/papers/` | APR-01–APR-07, unified whitepaper and ACR roots |
| `/mcp/` | `/zh-TW/mcp/` | Approved local-only MCP architecture and explicit not-yet-implemented status |
| `/status/` | `/zh-TW/status/` | Version, tests, measured evidence, limitations, provenance and licence status |

Shared machine surfaces:

- `/llms.txt`: short AI-readable overview, canonical links and scope boundaries;
- `/ai/site.json`: versioned structured index of pages, papers, runtime status and non-claims;
- `/sitemap.xml`: every public human-facing URL;
- `/robots.txt`: public indexing policy and sitemap location;
- `/404.html`: bilingual recovery page with links to both locale roots.

The site links to the GitHub repository and to source documents rather than copying the complete theory corpus into a second canonical store.

## 6. Offline APR decision lab

The lab is an educational projection of bounded APR fixtures, not a second implementation of APR policy in JavaScript.

At build time, `site/src/demo_export.py` imports the installed checkout's `apr_runtime` modules and executes a finite scenario matrix through the real Python runtime. The compiler emits only sanitized fixture inputs, decisions, reason codes, budget changes and evidence summaries into a static JSON data block. It emits no local path, credential, raw Provider response, private evidence, object handle or generated media.

The browser presents discrete controls whose complete combinations were exported at build time:

- evidence freshness: fresh or stale;
- uncertainty: low or high;
- risk: low or high;
- evidence conflict: absent or present;
- observation budget: available or exhausted;
- goal satisfaction: unresolved or satisfied.

Changing a control performs a local lookup in the exported matrix and renders:

- selected APR disposition;
- reason and unmet evidence need;
- selected observation depth/channel class;
- before/after budget;
- whether action readiness remains blocked;
- the corresponding segment of the APR closed loop.

The build fails if a control combination has no exported result, two results share the same key, output contains a forbidden sensitive field, or English and Chinese reason labels are incomplete. The browser never evaluates Python, sends a request, stores a profile or contacts the local MCP server.

## 7. Visual and interaction system

The APR site belongs to the EveMissLab family but does not copy the root index or another child site's template.

Visual intent: a calm perceptual instrument rather than a marketing landing page.

- near-black and cool-paper themes with strong readable contrast;
- thin technical hairlines, compact mono metadata and generous editorial spacing;
- cyan for observation/evidence, amber for budget/attention, violet for uncertainty and green for verified outcomes;
- a restrained grid derived from the Perceive → Verify loop;
- no gradient orbs, oversized decorative hero, fake terminal, stock imagery or animation that competes with content;
- system fonts only, no remote font request;
- visible text labels remain primary; colour is never the only status cue;
- keyboard-operable controls, visible focus, reduced-motion support and touch targets of at least 40 px;
- responsive single-column reading on narrow screens.

The first viewport contains the APR definition, closed-loop diagram, current research status and direct links to the lab, runtime guide and GitHub. It avoids a full-screen hero that hides the actual content.

## 8. Content truth and provenance

`site/src/content.py` owns translated interface copy. Technical claims are grounded in existing APR repository files and carry source links.

Build-time validation enforces:

- the same route set in English and Traditional Chinese;
- the same paper/runtime evidence identifiers in both languages;
- no claim that Draft PR content is merged before Git history proves it;
- no claim of production readiness, broad benchmark validation or high-risk autonomy;
- no claim of open-source licensing while the APR repository has no `LICENSE`;
- no claim that the local MCP server is available before its acceptance evidence exists;
- no embedded API keys, access tokens, service-account data or absolute user paths in generated output.

Measured hosted experiments may be cited as bounded historical evidence. The public lab itself remains offline and does not reproduce paid requests.

## 9. Parent `evemisslab.com` integration

The existing root site is the family index and remains on Cloudflare Pages. It is not migrated to a Worker.

The implementation adds one APR entry to the `Working systems` group in both language arrays in `D:\Ai\網站群\evemisslab\src\content.py`:

- host: `apr`;
- name: `APR`;
- English description: a concise statement that APR governs when an agent observes, what it reads, how deeply it reads and when it must reobserve;
- Chinese description: semantically equivalent Traditional Chinese copy;
- metadata: `Research MVP · v0.10` unless the accepted release changes before deployment.

The corresponding light/dark `--t-apr` colour token is added to the root stylesheet with verified text contrast. The generated `dist/` tree is not edited manually.

The root Pages deployment and the APR Worker deployment remain separate. `apr.evemisslab.com` must not claim or replace the apex custom domain.

## 10. Security and privacy

Public website guarantees:

- no authentication because there is no private or mutating public capability;
- no cookies, analytics, fingerprinting, telemetry or persistent browser storage;
- no forms, uploads, comments or arbitrary URL fetches;
- no Provider credentials or paid inference path;
- restrictive static security headers where supported, including a Content Security Policy that permits only same-origin assets;
- no connection from the public site to `localhost`, loopback HTTP, desktop adapters or the future MCP process;
- no service worker or background execution.

The MCP page explains that the future local server binds to loopback/stdio and uses a human-controlled allowlist, but the website cannot grant, expand or revoke that allowlist.

## 11. Deployment model

`site/wrangler.jsonc` defines an assets-only Worker with `site/dist` as its asset directory and `apr.evemisslab.com` as its custom-domain route.

Production deployment is a separate, explicit operation after local validation and user permission. The deployment sequence is:

1. build and validate the APR site;
2. verify the generated artifact contains no secret or local path;
3. deploy the APR static assets Worker;
4. verify the live English, Chinese, lab, machine-index and 404 routes;
5. add and validate the APR entry in the root index repository;
6. deploy the existing `evemisslab` Pages project through its own `deploy.sh`;
7. verify the root entry resolves to the already-live APR site.

This ordering prevents the parent index from linking to a missing child site.

## 12. Verification and acceptance

No tests or deployments are run while the user's current no-test boundary is active. Before any completion claim or production publication, the implementation must pass:

- deterministic site build twice with byte-identical generated content except an explicitly isolated build timestamp, or with no build timestamp at all;
- APR site unit tests for route parity, fixture completeness, safe generated fields, links and metadata;
- the existing APR runtime suite on the release candidate;
- Python formatting/lint checks already required by APR;
- Wrangler configuration validation and an assets-only dry run;
- secret and absolute-local-path scan of source plus generated site;
- browser checks at desktop and mobile widths for both locales;
- keyboard navigation, focus visibility, reduced motion and colour-contrast review;
- live route and custom-domain verification after explicit deployment permission;
- root `evemisslab.com` build, bilingual parity test and live-link verification.

Acceptance requires all of the following:

1. `apr.evemisslab.com` serves English and `/zh-TW/` serves Traditional Chinese;
2. the lab works after network access is disabled;
3. generated site files make zero Provider or Runtime requests;
4. APR claims match repository evidence and state their boundaries;
5. no secret, private path or raw hosted response is published;
6. `evemisslab.com` contains one working bilingual APR entry;
7. no existing root-index entry or custom domain is displaced.

## 13. Non-goals

This phase does not prove APR theory, validate arbitrary multimodal agents, provide a hosted agent, expose desktop control, create a public MCP endpoint, sell access, collect usage data or authenticate visitors. It creates a public research interface around evidence already present in the repository and a deterministic educational projection of the runtime.

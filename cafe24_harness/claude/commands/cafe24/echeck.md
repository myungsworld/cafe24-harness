# /cafe24/echeck — 라이브 검수: 스토어프론트 DOM + 어드민 상태 교차검증

DevTools에서 `getComputedStyle()`/`.offsetWidth`를 매번 사용자에게 시키지 않고, **AI가 맥락을 보고 자동으로 측정**한다. 카페24 버전은 한 발 더 나가서 **스토어프론트(라이브 화면)와 어드민 상태를 한 흐름에서 교차검증**해 "화면이 잘못된 게 코드 탓이냐, 어드민 설정 탓이냐"까지 답한다.

## 두 측면

| 측면 | 무엇을 보나 | 수단 |
|---|---|---|
| **storefront** (기본) | 실제 렌더 결과·동적 DOM·계산 스타일·3rd-party 위젯 | 인라인 Playwright (`/tmp/echeck-*.mjs`) |
| **admin** (★ 카페24 추가) | 어드민에 그 상태가 실제로 어떻게 설정돼 있나 (게시/미게시, 설정값) | `cf inspect board` / `cf open` (세션 재사용) |

**판정 형식**: `스토어프론트 = X / 어드민 = Y → 원인 = [코드 / 어드민 설정 / 외부 위젯]`.

---

## 핵심 원칙 (반드시)

1. **눈으로 봐야 하는 검수 = Playwright가 기본.** 렌더 결과·동적 동작·JS 주입 요소는 무조건 Playwright. curl+grep로 때우지 말 것.
2. **Playwright 미설치는 "안 함"의 사유가 아니다.** 없으면 직접 설치 후 진행.
3. **curl로 충분한 경우는 따로** — 서버사이드 렌더 결과(카페24 `module=` 치환, 정적 마커, 파일 동일성)만 보면 될 때. JS로 주입/변형되는 것(크리마·채널톡·`getComputedStyle`·호버 후 상태)은 curl로 애초에 안 보임 → Playwright 필수.
4. **storefront가 기대와 다른데 코드는 맞다면 → admin 측면으로 넘어가 어드민 상태를 확인**한다. 이게 카페24 echeck의 존재 이유.

---

## storefront 측면 (작동 원칙)

호출되면 AI가:

1. **현재 대화 맥락에서 추론**: 어떤 URL(방금 작업한 스킨 미리보기), 어떤 셀렉터(`.shop-mega` 등 직전 언급), 어떤 속성(`width`/`offsetWidth` 등), 호버 필요 여부.
2. 추론 결과를 1줄로 확인 (불확실하면 AskUserQuestion).
3. `/tmp/echeck-<ts>.mjs`에 인라인 Playwright 스크립트 생성 → `node`로 실행 → 표로 보고 → `/tmp` 정리.

### URL/캐시 규칙

- **기본 URL**: 카페24 스킨 미리보기(`https://<shop>.cafe24.com/skin-<번호>/...`). 운영 도메인은 CDN 캐시가 강해 회피. 스킨 번호는 프로젝트 CLAUDE.md에서 확인.
- **캐시 우회**: 매 실행마다 `?v=<랜덤9자리>` 자동 추가(`?` 있으면 `&v=`).

### 인라인 스크립트 템플릿

> **import 주의**: `playwright`는 CommonJS라 `.mjs`에서 named import가 깨진다. 반드시 default import 후 구조분해:
> ```javascript
> import pw from '/tmp/node_modules/playwright/index.js';
> const { chromium } = pw;
> ```

```javascript
// /tmp/echeck-<ts>.mjs
import pw from '/tmp/node_modules/playwright/index.js';
const { chromium } = pw;

const URL = '<여기에 URL>?v=' + Math.floor(Math.random() * 1e9);
const SELECTORS = ['<셀렉터1>', '<셀렉터2>'];
const PROPS = ['offsetWidth', 'offsetHeight', 'width', 'maxWidth'];
const HOVER = '<옵션: 호버 셀렉터 또는 null>';
const VIEWPORT = 1440;
const DOM_PROPS = new Set(['offsetWidth','offsetHeight','clientWidth','clientHeight','scrollWidth','scrollHeight']);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: VIEWPORT, height: 900 } });
await page.goto(URL, { waitUntil: 'domcontentloaded' });
if (HOVER) { await page.locator(HOVER).first().hover(); await page.waitForTimeout(500); }
const results = await page.evaluate(({ selectors, props, domProps }) => {
  return selectors.map(sel => {
    const el = document.querySelector(sel);
    if (!el) return { selector: sel, found: false };
    const cs = getComputedStyle(el);
    const out = { selector: sel, found: true };
    for (const p of props) out[p] = domProps.includes(p) ? el[p] : (cs.getPropertyValue(p) || cs[p] || '');
    return out;
  });
}, { selectors: SELECTORS, props: PROPS, domProps: [...DOM_PROPS] });

console.log(JSON.stringify({ url: URL, viewport: VIEWPORT, hover: HOVER, results }, null, 2));
await browser.close();
```

### Playwright 설치 (미설치 시 묻지 말고)

```bash
node -e "require('/tmp/node_modules/playwright')" 2>/dev/null && echo OK || (
  cd /tmp && npm init -y >/dev/null 2>&1
  npm install playwright >/dev/null 2>&1 && npx playwright install chromium
)
```

`/tmp`에 설치하면 프로젝트 의존성을 오염시키지 않고 재사용 가능. `npx playwright install chromium`(브라우저 바이너리)까지 반드시. **미설치를 이유로 검수 건너뛰기 금지.**

### JS 주입 위젯 레시피 (크리마 등)

크리마(cre.ma)·채널톡은 SDK가 브라우저에서 비동기로 DOM에 꽂힌다. `waitUntil:'networkidle'` + `waitForTimeout(5000~6000)`로 주입 대기, 높이(`offsetHeight`)로 빈 태그 vs 콘텐츠참 판별, `ancestorId()`로 어느 컨테이너에 들어갔는지 확인, 기존 카페24 게시판이 숨겨졌는지/공존하는지도 함께 측정(이중노출 회귀 탐지). 크리마는 `?crema-sim=1`로 활성 시뮬레이션 가능 — 미활성 vs 활성 양쪽 측정해 비교.

---

## admin 측면 (★ 카페24 추가)

storefront 결과가 기대와 다르고 **코드는 맞다고 판단되면**, 어드민 실제 상태를 확인한다. 전제: `cf init` + `cf login` 된 프로젝트(세션 있음). `cf doctor`로 세션 유무 확인.

대표 시나리오:

- **후기가 메인/게시판에 안 뜸** → `cf inspect board` 실행 → **미게시 글번호** 목록을 받는다. 미게시 글이 있으면: 원인은 코드가 아니라 "어드민 미게시 상태" → 사용자에게 게시물 관리에서 "게시함" 클릭 안내(승인 후 수동).
- **메인 리뷰가 게시/캐시삭제로도 안 바뀜** → storefront 측면에서 `widgets.cre.ma`/`review*.cre.ma` 스크립트와 `[class*="crema"]` 요소를 측정 → 크리마가 카페24 게시판을 덮고 있으면 원인은 외부 위젯 → 크리마 어드민(cre.ma) 안내.
- **특정 설정값 확인 필요** → `cf open <alias|/path|url>`로 해당 어드민 페이지 DOM·스샷 덤프(`cf open boards`로 게시판 목록/번호 탐지 등).
- 세션 없으면: admin 측면은 건너뛰고 `cf login` 안내 후 storefront만 보고.

> **읽기전용**: admin 측면은 진단·보고만. 게시 토글(`setPost`) 등 라이브 변경은 자동화하지 않고 사용자 승인 후 수동.

---

## 출력 보고 형식

```
[storefront] https://healic.cafe24.com/skin-skin22/index.html?v=482917356  (viewport 1440, hover .menu:first-child)
  .shop-mega        offsetWidth=1180  width=1180px  maxWidth=none
  .shop-mega-inner  offsetWidth=1180  width=1180px  maxWidth=1400px   (기대 1400 → 실제 1180 ❌)

[admin] cf inspect board (board_no=4)
  🚫 미게시 글 3개: [10231, 10228, 10224]

판정: 메인 후기 누락의 원인 = 어드민 미게시(코드 아님).
 → 게시물 관리에서 해당 글 "게시함" 클릭 필요(승인 후). 크리마 위젯은 미검출.
```

기대치와 실제값을 같이 명시. storefront/admin 둘 다 보고하고 **원인 판정**으로 마무리.

## 주의

- curl은 JS 미실행 → JS로 만들어지는 요소는 원천적으로 안 보임. "curl로 확인했다" ≠ "화면에 잘 나온다".
- 카페24 일부 페이지는 referer/세션 검증으로 헤드리스 차단 → 실패 시 headed 모드(`cf open --headed`) 또는 사용자 DevTools 확인.
- 캐시 우회 쿼리에도 카페24 서버 캐시가 5~10분 지속 가능 → 그 경우 대기 후 재측정.
- 실행 후 `/tmp/echeck-*.mjs` 정리 (`/tmp/node_modules`의 playwright는 재사용 위해 남김).

# Supplier PO Assistant — Frontend

A Next.js chat UI that lets suppliers query their SAP S/4HANA purchase orders
through the deployed AI agent.

---

## How to deploy on Vercel

### Option A — Vercel Dashboard (recommended, no CLI needed)

1. **Push this folder to GitHub**
   - Create a new repository (or use your existing one).
   - Copy the contents of `assets/supplier-po-frontend/` to the repo root.

2. **Import the project in Vercel**
   - Go to [vercel.com/new](https://vercel.com/new).
   - Click **"Import Git Repository"** and select your repo.
   - Vercel will auto-detect it as a Next.js project.

3. **Set the environment variable**
   - Under **Settings → Environment Variables**, add:

     | Name | Value |
     |------|-------|
     | `NEXT_PUBLIC_AGENT_URL` | `https://27c30ede-2a17e47f.sap3eu12.c.run.ai.cloud.sap` |

4. **Deploy**
   - Click **Deploy**. Vercel builds and hosts it — you get a live HTTPS URL instantly.
   - Every push to `main` auto-redeploys.

---

### Option B — Vercel CLI

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Go into the frontend folder
cd assets/supplier-po-frontend

# 3. Link to your Vercel account
vercel link

# 4. Add the env var (one-time)
vercel env add NEXT_PUBLIC_AGENT_URL production
# Paste: https://27c30ede-2a17e47f.sap3eu12.c.run.ai.cloud.sap

# 5. Deploy
vercel --prod
```

Vercel prints your live URL when done (e.g. `https://supplier-po-assistant.vercel.app`).

---

## Local development

```bash
cd assets/supplier-po-frontend

# 1. Install dependencies
npm install

# 2. Create .env.local
cp .env.example .env.local
# Edit .env.local if your agent URL is different

# 3. Start dev server
npm run dev
# → http://localhost:3000
```

---

## How the app connects to the agent

```
Browser  ──POST /api/chat──▶  Next.js API Route  ──POST /──▶  AI Agent
                               (app/api/chat/route.ts)       (Joule Studio)
```

- The browser **never** talks to the agent directly — the API route is a server-side proxy.
- This avoids CORS issues and keeps the agent URL out of the browser.
- The agent speaks the **A2A JSON-RPC protocol**: `{ method: "tasks/send", params: { message: { role: "user", parts: [{ type: "text", text: "..." }] } } }`.
- The response is parsed from `result.artifacts[0].parts` or `result.status.message.parts`.

---

## File structure

```
assets/supplier-po-frontend/
├── app/
│   ├── layout.tsx          # Root layout, global CSS import
│   ├── page.tsx            # Main page (Shell + Chat)
│   ├── globals.css         # Tailwind + SAP Horizon colour tokens
│   └── api/
│       └── chat/
│           └── route.ts    # Server-side proxy to the AI agent
├── components/
│   ├── Shell.tsx           # SAP Fiori-style top bar
│   ├── Chat.tsx            # Conversation state, input bar, welcome screen
│   ├── MessageBubble.tsx   # Individual message with markdown-light formatting
│   └── SuggestedQuestions.tsx  # Quick-start suggestion chips
├── vercel.json             # Vercel project config
├── next.config.js          # Next.js config + env injection
├── tailwind.config.ts      # SAP Horizon colour palette
├── package.json
└── tsconfig.json
```

---

## Customisation

| What | Where |
|------|-------|
| Suggested starter questions | `components/Chat.tsx` → `SUGGESTED` array |
| Agent URL | `NEXT_PUBLIC_AGENT_URL` env var |
| SAP colour palette | `tailwind.config.ts` → `colors.sap` |
| Shell title / logo | `components/Shell.tsx` |
| Welcome copy | `components/Chat.tsx` → `WelcomeScreen` |

---

## Agent card

To verify the agent is live and inspect its capabilities:

```bash
curl https://27c30ede-2a17e47f.sap3eu12.c.run.ai.cloud.sap/.well-known/agent.json
```

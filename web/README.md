# Sportsona Web

SvelteKit + TypeScript + Tailwind v4 frontend for Sportsona.

## Stack

- **SvelteKit 2** with Svelte 5 (runes mode)
- **Vite 6** dev server
- **Tailwind CSS 4** via `@tailwindcss/vite`
- **shadcn-svelte**-style UI primitives (vendored under `src/lib/components/ui/`)

## Prerequisites

- Node.js 20+ and Yarn 1.x (Classic)
- The Sportsona backend running on `http://localhost:8000` (see `../backend/README.md`)

## Yarn-only commands

This project uses Yarn — do not mix in `npm install`, that breaks the lockfile.

| Task | Command |
|---|---|
| Install dependencies | `yarn install` (or just `yarn`) |
| Run dev server | `yarn dev` (port **4000**) |
| Production build | `yarn build` |
| Preview production build | `yarn preview` |
| Type-check (svelte-check) | `yarn typecheck` |
| Type-check (watch mode) | `yarn typecheck:watch` |
| Add a dependency | `yarn add <pkg>` |
| Add a dev dependency | `yarn add -D <pkg>` |
| Remove a dependency | `yarn remove <pkg>` |
| Update one dependency | `yarn upgrade <pkg>` |
| See what's outdated | `yarn outdated` |
| Update interactively | `yarn upgrade-interactive --latest` |

> ⚠️ **Don't use `yarn check`** — it's reserved by Yarn 1 for verifying installed
> packages. The svelte-check script is exposed as `yarn typecheck` instead.

## Environment

Copy `.env.example` to `.env` and adjust if needed. The default points the
frontend at the local backend:

```
PUBLIC_API_BASE_URL=http://localhost:8000
```

## Ports

- Dev server: **`http://localhost:4000`** (`vite.config.ts` sets `strictPort: true` so collisions fail loudly)
- Backend: `http://localhost:8000`
- Postgres: `localhost:5432`

The backend's CORS allowlist (`backend/app/main.py`) already includes `http://localhost:4000`.

## Project layout

```
web/
├── src/
│   ├── app.css           # Tailwind entry + theme variables
│   ├── app.html          # HTML template
│   ├── lib/
│   │   ├── api.ts        # Typed FastAPI client (auto-refresh on 401)
│   │   ├── date.ts       # date-fns formatting helpers
│   │   ├── follow.svelte.ts   # follow/unfollow store
│   │   ├── stores/
│   │   │   └── auth.svelte.ts # auth store (localStorage)
│   │   ├── components/
│   │   │   ├── Logo.svelte
│   │   │   ├── FollowButton.svelte
│   │   │   └── ui/       # Button, Card, Input, Label, Alert, Badge, Skeleton, Spinner
│   │   └── utils.ts      # cn() helper
│   └── routes/           # SvelteKit pages
├── static/               # public assets (favicon, brand SVGs, brand-preview.html)
├── package.json
├── svelte.config.js
├── tsconfig.json
└── vite.config.ts
```

# Body Literacy AI

Small local project with a Vite React frontend and a backend (see backend folder).

## Quick start

Frontend
- cd frontend
- npm install
- npm start
- Open http://localhost:5173

Backend (general)
- cd backend
- Inspect package.json or requirements.txt to see exact commands
- Node: npm install && npm run dev (or npm start)
- Python (FastAPI/Flask): create venv, pip install -r requirements.txt, then `uvicorn main:app --reload` or `flask run`

## Environment
- Copy any `.env.example` to `.env` and set required secrets (PORT, DATABASE_URL, SECRET_KEY).
- DB: run migrations/seeds if applicable.

## Troubleshooting
- If Vite complains about JSX in `.js` files:
  - Ensure `@vitejs/plugin-react` is installed and enabled in `vite.config.js`, and `package.json` may include `"type": "module"`; or
  - Rename files containing JSX from `.js` → `.jsx` and update imports.
- If imports fail for `react-router-dom`, run `npm install react-router-dom`.
- If dev server fails after dependencies changed run a full restart and `npm install`.

## Development notes
- Frontend entry is `/src/index.jsx` and served by `/index.html` at project root.
- Keep sensitive data out of the repo; add to `.gitignore` (already configured).

## Contributing
- Open an issue or create a PR with a short description of changes.

## License
- Add a LICENSE file or update this README with licensing information.

# Know Thy Taste

A local-first app that helps you discover *why* you love the movies you love. Through guided reflection sessions, the app detects patterns in your taste and builds a personalized profile of your preferences.

**Live Web App:** https://know-thy-taste.vercel.app

## Features

- **Guided Sessions** - Answer thoughtful questions about films you've watched
- **Anti-Generic Detection** - Prompts you to be specific when responses are vague
- **Pattern Detection** - Identifies recurring themes, technical preferences, and emotional responses
- **Sentiment Analysis** - Distinguishes between elements you love vs. criticize
- **Local-First** - All data stored locally. Nothing sent to servers.
- **TMDB Integration** - Optional movie poster lookup with your own API key
- **Export/Import** - Backup and restore your data as JSON

---

## Web App

### Use the Live App

Just visit https://know-thy-taste.vercel.app — no setup required.

### Run Locally

```bash
# Clone the repo
git clone https://github.com/jwstaff/know-thy-taste.git
cd know-thy-taste

# Serve the public folder (any static server works)
python3 -m http.server 8000

# Open in browser
open http://localhost:8000/public/
```

### Usage

1. **Add Movies** - Go to Movies → Add Movie. Enter titles of films you've seen.
2. **Start a Session** - Choose a session type:
   - **Deep Dive** - Intensive analysis of one film
   - **Pattern Hunt** - Compare elements across films
   - **Temporal** - Explore how your reaction has changed over time
3. **Answer Questions** - Be specific! The app will prompt you if responses are too vague.
4. **View Patterns** - After 2+ sessions, check the Patterns tab to see detected patterns.
5. **Validate Patterns** - Confirm or reject patterns to improve accuracy.

### TMDB Movie Posters (Optional)

1. Get a free API key from [themoviedb.org](https://www.themoviedb.org/settings/api)
2. Go to Settings in the app
3. Paste your API key and save

---

## CLI (Command Line)

### Installation

```bash
# Clone the repository
git clone https://github.com/jwstaff/know-thy-taste.git
cd know-thy-taste

# Install with pip
pip install -e .
```

### Quick Start

```bash
# First-time setup
ktt init

# Start a discovery session
ktt session start

# View your taste profile
ktt profile

# See detected patterns
ktt patterns show

# Export your data
ktt export --format markdown
```

### Commands

| Command | Description |
|---------|-------------|
| `ktt init` | First-time setup |
| `ktt session start` | Start a new discovery session |
| `ktt session start --type deep-dive` | Intensive analysis of 1-2 films |
| `ktt session start --type pattern-hunt` | Compare 3-4 similar films |
| `ktt movies add` | Add a movie to your collection |
| `ktt movies list` | List all your movies |
| `ktt patterns show` | View detected patterns |
| `ktt profile` | View your taste profile summary |
| `ktt export` | Export data (JSON or Markdown) |

---

## Pattern Detection

The app detects patterns across several categories:

| Category | Examples |
|----------|----------|
| **Technical** | Cinematography, lighting, color, editing, sound design |
| **Structural** | Pacing, narrative structure |
| **Performance** | Acting, facial expressions, subtlety |
| **Writing** | Dialogue, story, character development |
| **Emotional** | Tension, catharsis, humor |
| **Thematic** | Loss, love, identity, isolation, family, mortality |
| **Preferences** | Slow pacing, ambiguous endings, visual storytelling |

Patterns include sentiment analysis — the app knows the difference between "the cinematography was stunning" and "the cinematography was distracting."

---

## Data Privacy

- **Web App**: Data stored in browser's IndexedDB
- **CLI**: Data encrypted locally with AES-256
- Nothing is sent to any server
- Export/backup your data anytime
- Full control to delete all data

---

## Testing

Run the end-to-end quality test:

```bash
node test-quality.js
```

---

## Project Structure

```
know-thy-taste/
├── public/                 # Static web app
│   ├── index.html          # Main SPA
│   └── js/
│       ├── app.js          # Alpine.js components
│       ├── db.js           # IndexedDB wrapper (Dexie)
│       ├── analysis.js     # Pattern detection & sentiment
│       ├── questions.js    # Question bank
│       └── tmdb.js         # TMDB API integration
├── src/ktt/                # Python CLI package
│   ├── cli/                # Typer CLI commands
│   ├── core/               # Core logic
│   └── web/                # FastAPI server
├── test-quality.js         # E2E test script
└── vercel.json             # Deployment config
```

---

## Tech Stack

**Web App:**
- Alpine.js, Tailwind CSS
- IndexedDB via Dexie.js
- Vercel (static hosting)

**CLI:**
- Python, Typer
- SQLAlchemy, SQLite
- AES-256 encryption

---

## License

MIT

# Know Thy Taste

A command-line application for metacognitive exploration of your movie preferences. Discover not just *what* you like, but *why*—and develop a richer vocabulary for your own taste.

## Philosophy

This isn't just about cataloging movies. It's about helping you understand why you respond to certain films, recognize patterns in your preferences, and develop deeper self-awareness about your taste through structured reflection.

## Features

- **Scaffolded Questioning**: Three-phase analysis (Planning, Monitoring, Evaluation) based on metacognitive research
- **Anti-Generic Detection**: The app pushes for specificity—"good acting" isn't enough
- **Pattern Recognition**: Discovers themes and elements that consistently resonate with you
- **Privacy-First**: All data encrypted locally; nothing leaves your machine
- **Adaptive Scaffolding**: Guidance fades as you develop your reflection skills

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd know-thy-taste

# Install with pip
pip install -e .

# Or with uv
uv pip install -e .
```

## Quick Start

```bash
# First-time setup (privacy policy, passphrase, consent)
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

## Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `ktt init` | First-time setup |
| `ktt profile` | View your taste profile summary |
| `ktt export` | Export data (JSON or Markdown) |

### Session Commands

| Command | Description |
|---------|-------------|
| `ktt session start` | Start a new discovery session |
| `ktt session start --type deep-dive` | Intensive analysis of 1-2 films |
| `ktt session start --type pattern-hunt` | Compare 3-4 similar films |
| `ktt session start --type temporal` | Explore how your reaction changed over time |
| `ktt session resume` | Resume a paused session |

### Movie Commands

| Command | Description |
|---------|-------------|
| `ktt movies add` | Add a movie to your collection |
| `ktt movies list` | List all your movies |

### Pattern Commands

| Command | Description |
|---------|-------------|
| `ktt patterns show` | View detected patterns |
| `ktt patterns validate <id>` | Confirm or reject a pattern |

### Privacy Commands

| Command | Description |
|---------|-------------|
| `ktt privacy review` | Review your privacy settings |
| `ktt privacy withdraw <type>` | Withdraw a specific consent |
| `ktt privacy delete-all` | Permanently delete all data |

## Session Types

### Deep Dive (30-45 min)
Intensive analysis of one or two films. Explore every facet of your response: what you noticed, how you engaged, and why it mattered.

### Pattern Hunt (20-30 min)
Compare 3-4 similar films to find what differentiates them for you. Why did you love one but only like another?

### Temporal (15-20 min)
Explore how your relationship with a rewatched film has changed. What's different now?

## Privacy & Security

- **Local-first**: All data stored on your machine
- **Encrypted**: Reflections encrypted with AES-256
- **No telemetry**: Nothing sent anywhere
- **Your key**: Encryption derived from your passphrase
- **Full control**: Export or delete anytime

## Optional: TMDB Integration

Auto-fetch movie metadata by setting up a free TMDB API key:

```bash
# Set via environment variable
export TMDB_API_KEY=your_key_here

# Or the app will prompt during movie addition
```

Get a free API key at: https://www.themoviedb.org/settings/api

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=ktt
```

## Data Location

Your data is stored in:
- **macOS**: `~/Library/Application Support/know-thy-taste/`
- **Linux**: `~/.local/share/know-thy-taste/`
- **Windows**: `%LOCALAPPDATA%/know-thy-taste/`

## License

MIT

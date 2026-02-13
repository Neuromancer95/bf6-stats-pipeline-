# BF6 Player Stats Pipeline

Pull Battlefield 6 player stats from the [GameTools.Network](https://api.gametools.network/docs) API and save to JSON, CSV, or SQLite.

## Setup

1. Clone this repo:
   ```bash
   git clone https://github.com/Neuromancer95/bf6-stats-pipeline-.git
   cd bf6-stats-pipeline-
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate   # macOS/Linux
   pip install -r requirements.txt
   ```

3. Copy the example config and add your players:
   ```bash
   copy config.example.yaml config.yaml
   ```
   Edit `config.yaml` with player names and platforms (`pc`, `psn`, `xbox`).

## Usage

- **From config file (default `config.yaml`):**
  ```bash
  python main.py --config config.yaml --output-dir output --format json
  ```

- **Override players from CLI:**
  ```bash
  python main.py --players "PlayerName,pc;OtherPlayer,psn" --output-dir output --format all
  ```

- **Output formats:** `json`, `csv`, `sqlite`, or `all` (writes all three).

- **Options:**
  - `--output-dir` — directory for output files (default: `output`)
  - `--no-batch` — fetch stats one-by-one instead of batch API
  - `--rate-limit N` — seconds between API requests (default: 1.0)

Output files are named with a timestamp (e.g. `stats_20250210_123456.json`).

## Project layout

```
bf6-stats-pipeline/
  .gitignore
  requirements.txt
  config.yaml           # your player list (optional: add to .gitignore)
  config.example.yaml
  src/
    api.py              # GameTools.Network BF6 API client
    pipeline.py         # load config, fetch stats
    storage.py          # JSON / CSV / SQLite writers
  main.py               # CLI
  README.md
```

## API

- No API key required. Data from [GameTools.Network](https://api.gametools.network) (Battlefield series stats).
- Endpoints used: `/bf6/player/` (resolve ID), `/bf6/stats/` (single), `/bf6/multiple/` (batch, max 128 players).

## Publish to GitHub

Repo: [github.com/Neuromancer95/bf6-stats-pipeline-](https://github.com/Neuromancer95/bf6-stats-pipeline-)

1. **Install Git** (if needed): [git-scm.com](https://git-scm.com/) — use default options and ensure "Git from the command line" is enabled.

2. **From the project folder**, run the commands in `push-to-github.ps1`, or:

   ```powershell
   cd "c:\Users\bpric\AppData\Local\Python\pythoncore-3.14-64\Scripts\bf6-stats-pipeline"

   git init
   git add .
   git commit -m "Initial commit: BF6 stats pipeline"

   git remote add origin https://github.com/Neuromancer95/bf6-stats-pipeline-.git
   git branch -M main
   git push -u origin main --force
   ```

   `--force` overwrites the existing README on the remote with your full project. If GitHub prompts for a password, use a [Personal Access Token](https://github.com/settings/tokens).

## License

Use and modify as you like.

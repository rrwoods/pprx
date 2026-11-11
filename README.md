# PPR X

[![Website](https://img.shields.io/badge/website-pprx.gg-brightgreen)](https://pprx.gg/)
[![GitHub stars](https://img.shields.io/github/stars/rrwoods/pprx.svg)](https://github.com/rrwoods/pprx/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/rrwoods/pprx.svg)](https://github.com/rrwoods/pprx/issues)

**PPR X** is a score analyzer, continuous difficulty calibration engine, and progression tracking tool for Dance Dance Revolution (DDR) players who use the [3icecream](https://3icecream.com/) platform.

Visit **[pprx.gg](https://pprx.gg/)** to get started!

---

## Features

- **Continuous "Spice" Difficulty Ratings**: Official DDR chart ratings are coarse integers (1–20). PPR X computes continuous decimal difficulties derived from pairwise regressions over public player scores (anchored to *MAX 300* Expert = 10.0).
- **Score Quality & Improvability**: Translates raw scores into standardized "Quality" values, identifying both your most impressive achievements and your highest-yield score targets.
- **LIFE4 Rank Progression**: Built-in tracking for [LIFE4](https://life4ddr.com/) rank requirements, barrier trials, calorie burns, and consecutive song play goals.
- **Cabinet & Regional Filtering**: Dynamically filters chart availability based on cabinet hardware (White cab vs. Gold cab vs. Gold exclusive) and regional song licensing locks (North America, Japan, Europe/Asia).
- **Seamless 3icecream Integration**: Secure OAuth account linking with automated score synchronization via 3icecream webhooks.

---

## Documentation

- **[VISION.md](VISION.md)**: Project vision, dual North Stars, scoring difficulty philosophy, and explicit anti-goals.
- **[GLOSSARY.md](GLOSSARY.md)**: Canonical domain language and definitions (Player vs. User, Rating vs. Spice vs. Quality, Cabinets, and Unlocks).
- **[Architecture & Pipeline Guide](docs/architecture.md)**: Technical guide detailing data ingestion, the statistical calibration pipeline, operational landmines, and deployment topology.
- **[Architecture Decision Records](docs/adr/)**: Record of key design choices and architectural trade-offs.

---

## Development

### Prerequisites

- Python 3.12 (matches `pprxweb/.python-version`; `requirements.txt` is compiled against 3.12)
- Git
- virtualenvwrapper ([virtualenvwrapper-win](https://pypi.org/project/virtualenvwrapper-win/) on Windows)

### Local Setup

The project's virtualenv is named `pprx` and is managed by virtualenvwrapper, so `workon pprx` activates it from any directory. Agents rely on this name and location (see [AGENTS.md](AGENTS.md)).

1. **Clone the repository**:
   ```bash
   git clone https://github.com/rrwoods/pprx.git
   cd pprx/pprxweb
   ```

2. **Install virtualenvwrapper**:
   - **Windows**:
     ```bat
     py -3.12 -m pip install virtualenvwrapper-win
     ```
     This puts `mkvirtualenv`, `workon`, and friends on your `PATH` as batch files. Environments live in `%USERPROFILE%\Envs`.
   - **macOS/Linux**: Install `virtualenvwrapper` and add its shell hook to your shell startup file per the [official install guide](https://virtualenvwrapper.readthedocs.io/en/latest/install.html). Environments live in `~/.virtualenvs` by default.

3. **Create the `pprx` environment** (it is activated automatically once it's created):
   ```bash
   # Windows
   mkvirtualenv -p 3.12 pprx
   # macOS/Linux
   mkvirtualenv -p python3.12 pprx
   ```

4. **Install dependencies** (from `pprxweb/`, with `pprx` active):
   ```bash
   pip install -r requirements.txt
   ```
   On macOS/Linux, `mysqlclient` builds from source and needs `pkg-config` plus the MySQL/MariaDB client headers first; see the [mysqlclient install notes](https://github.com/PyMySQL/mysqlclient#install).

5. **Activate the environment in later sessions**:
   - **Windows Command Prompt / macOS / Linux**: `workon pprx`
   - **Windows PowerShell**: `& ~\Envs\pprx\Scripts\Activate.ps1`. virtualenvwrapper-win's `workon` is a `cmd` batch file, so running it from PowerShell activates only a throwaway child process.

   To confirm, run `python -m django --version`. It should print `4.2.x`.

6. **Configure environment variables**:
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to configure your `DJANGO_SECRET_KEY` and optional 3icecream / email credentials. (When running locally, SQLite at `pprx.db` is used automatically if `DATABASE_URL` is omitted).

7. **Run the local development server** (from `pprxweb/`, with `pprx` active):
   ```bash
   python manage.py runserver
   ```
   Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Production Deployment

Production is hosted on **DigitalOcean App Platform** (`pprx.gg`) connected to a Managed MySQL database, with static assets served via WhiteNoise. Refer to [docs/architecture.md](docs/architecture.md) for full deployment details.

---

## License

This project does not currently have an open-source license specified; all rights are reserved.

---

## Acknowledgments

Special thanks to:
- **Sunny** and [3icecream](https://3icecream.com/) for making DDR score tracking and API data accessible.
- The **LIFE4** community for creating standard rank benchmarks and community goals.
- The global DDR community for providing feedback, data, and support.

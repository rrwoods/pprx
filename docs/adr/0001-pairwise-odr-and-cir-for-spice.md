# Pairwise ODR and Centered Isotonic Regression for Continuous Difficulty (Spice & Quality)

Official DDR chart ratings are coarse integers (1–20) that fail to convey true difficulty differentials within a rating. We decided to compute continuous chart difficulty ("Spice") by performing pairwise Orthogonal Distance Regression (ODR) across common player scores and iteratively solving relative slopes with geometric means, then deriving player score "Quality" benchmarks via Centered Isotonic Regression (CIR) anchored to *MAX 300* Expert = 10.0. This handles player skill variance and non-linear DDR scoring without requiring artificial matchmaking systems like Elo or Glicko.

## Considered Options

- **Raw score averages**: Rejected because player population bias skews unplayed or niche charts.
- **Elo / Glicko ranking systems**: Rejected because DDR charts are fixed targets rather than dynamic competitors, and player scoring is highly non-linear near the 1,000,000 ceiling.
- **Pairwise ODR with CIR**: Selected because it models variance in both charts simultaneously and guarantees monotonic score-to-quality mapping.

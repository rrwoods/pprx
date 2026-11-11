# PPR X

A performance rating, continuous difficulty calibration, and progression tracking system for Dance Dance Revolution (DDR) players.

## Language

**Player**:
A public DDR arcade profile whose scores are used as anonymous data points for difficulty calibration.
_Avoid_: User, Account

**User**:
A person with an account on PPR X who connects their 3icecream profile to track scores, goals, and unlocks.
_Avoid_: Player, Profile

**Rating**:
The official integer passing difficulty (1–20) assigned to a chart by Konami.
_Avoid_: Difficulty, Level, Foot

**Rerate**:
A temporary manual difficulty rating assigned to a chart pending automated data.
_Avoid_: Custom rating

**Scoring Difficulty**:
The relative difficulty of achieving high score benchmarks on a chart.
_Avoid_: Clear difficulty, Survival difficulty

**Passing Difficulty**:
The relative difficulty of surviving or clearing a chart without failing.
_Avoid_: Clear difficulty, Survival difficulty

**Spice**:
A continuous rating representing the relative scoring difficulty of a chart, derived from pairwise player score comparisons and anchored to MAX 300 Expert = 10.0.
_Avoid_: Tier, Decimal difficulty, Scale

**Quality**:
A measure of how impressive a specific score is relative to a chart's difficulty benchmarks.
_Avoid_: Skill, Points, Rating

**Score**:
The raw game score achieved on a chart (0 to 1,000,000).
_Avoid_: Result, Points

**Current Score**:
The one score per User per chart that represents their standing on that chart. Earlier scores it superseded are retained as history.
_Avoid_: Latest score, Active score

**Fetch**:
Retrieving a User's score data from 3icecream.
_Avoid_: Pull, Download

**Ingest**:
Recording fetched score data in PPR X, superseding Current Scores that the fetched data improves upon.
_Avoid_: Import, Save

**Synchronization**:
A Fetch followed by an Ingest for a single User.
_Avoid_: Pull, Refresh, Update

**Normalized Score**:
A logarithmic transformation of a score based on distance from a perfect score: -log2(1,000,000 - score).
_Avoid_: Adjusted score

**Cabinet**:
A physical arcade machine specification (White, Gold, Gold only) that determines chart availability.
_Avoid_: Machine, Version

**Can't-Hurt-Can-Help**:
A LIFE4 evaluation rule where scores on unlockable or culled historical charts can satisfy quantity-based progression requirements, but are never required for comprehensive criteria.
_Avoid_: Grandfathered, Optional chart

**Region**:
A geographical territory (e.g. North America, Japan, Europe) with specific song licensing and availability rules.
_Avoid_: Country, Server

**Unlock**:
An in-game event or task required to play a chart (e.g. Golden League, Extra Savior, Galaxy Brave).
_Avoid_: Progression, Achievement

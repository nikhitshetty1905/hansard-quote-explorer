# Project: Hansard Immigration × Labour Market Discourse Analysis

## Purpose
Extract exact quotes from UK Historic Hansard (19th and early–mid 20th century) where migration/immigration is discussed in connection with the labour market.  
Also classify quotes by *frame* (e.g., labour-need, labour-threat, racialised) to understand underlying intent.

## Timeframe
Default: 1890–1950  
Configurable: start year and end year as script inputs.

## Data Source
- UK Parliament Historic Hansard archive: `https://api.parliament.uk/historic-hansard`
- Sitting index JSON (daily) via `/sittings/{year}/{month}/{day}.js`
- Debate JSON via `{href}.js` from sitting index

## Core Logic

### 1. Day Iteration
- Loop through all days between start and end date.
- For each day:
  - Fetch sitting index JSON.
  - Skip if day has no items or returns 404.

### 2. Debate Fetch
- For each debate href in that day’s index:
  - Append `.js` and fetch JSON.
  - Identify `house` from URL path (`/commons/` or `/lords/`).
  - Save `debate_title`.

### 3. Speech Traversal
- Traverse `children` recursively to find all speech nodes.
- Each speech node:
  - Must have `speaker.name` and `text` or `body`.
  - Normalise whitespace in `quote`.

### 4. Filtering — Immigration × Labour Market
- Tokenise speech text to words.
- Match if:
  - At least one **migration term** is present, AND
  - At least one **labour term** is present, AND
  - These occur within N words (default: 40) of each other.
- **Migration terms**: immigration, immigrant(s), migrant(s), alien(s), foreign(er)(s), guest worker(s), colonial subjects/workers, plus period-specific euphemisms.
- **Labour terms**: labour market, labor market, wage(s), employment, unemployment, job(s), workforce, manpower, strike(s), trade union(s), etc.

### 5. Output Record
For each match:
- `date` (YYYY-MM-DD)
- `house` (commons/lords)
- `debate_title`
- `member`
- `party` (if available)
- `quote` (exact Hansard wording)
- `hansard_url` (HTML)
- `json_url` (machine source)

### 6. Deduplication
- Skip if same URL + same member + first 80 chars of quote already saved.

### 7. Output Files
- `quotes.jsonl` — one JSON object per line
- `quotes.csv` — same fields, spreadsheet-friendly
- Append-safe so the script can run in slices and be resumed

---

## Framing Classification (Rule-Based v1)

### Labels
- **LABOUR_NEED** — quotes framing migrants as necessary for filling shortages, essential work, etc.
- **LABOUR_THREAT** — quotes framing migrants as depressing wages, taking jobs, increasing unemployment.
- **RACIALISED** — quotes using explicitly racialised language, or implying undesirability based on origin/ethnicity.
- **MIXED** — quotes containing elements of more than one above frame.
- **OTHER** — irrelevant or neutral economic mentions.

### Method
- Use transparent keyword regex rules for each label.
- Apply in order:
  1. Check LABOUR_NEED
  2. Check LABOUR_THREAT
  3. Check RACIALISED
  4. Assign MIXED if multiple matched
  5. Assign OTHER if none matched

---

## Optional Explorer UI
- Streamlit app to load tagged JSONL, filter by:
  - Year range
  - House
  - Frame label
  - Search term
- Display table of results with clickable URLs.
- CSV download of current view.

---

## Performance & Reliability
- Use `requests.Session` with retries (429/5xx).
- Pacing: at least 1 second between requests, plus small random jitter.
- Resume logic: save last processed date to `.checkpoint` file.
- Per-day caching of sitting index JSON to avoid refetching on resume.

---

## Extensions
- Decade-specific lexicons for migration & labour terms.
- Event tagging for major legislation (e.g., Aliens Act 1905).
- Timeline chart of frame frequencies by year.
- Export to DuckDB for advanced queries.

---

## Deliverables
1. **Collector script**: `collector.py`
2. **Framing tagger**: `tagger.py`
3. **Explorer UI**: `explorer.py`
4. `claude.md` (this file) as the spec reference

---

## CURRENT PROJECT STATUS (Updated)

### Data Collection Complete
- **Total Quotes**: 532 verified parliamentary quotes (1900-1930)
- **Coverage**: Systematic extraction from Historic Hansard API
- **Verification**: 89.1% speaker attribution accuracy through cross-referencing

### Database Evolution
- **database_neutral.db**: Current production database with optimized analyses
- **Database Schema**: id, year, date, speaker, party, frame, quote, hansard_url, historian_analysis, confidence, verified_speaker, enhanced_speaker, corrected_speaker, debate_title

### AI Analysis Implementation
- **Claude AI Integration**: claude_historian.py with Claude-3.5-Sonnet
- **Analysis Quality**: Intelligent content extraction, neutral tone (removed "sophisticated", "astute", "strategic")
- **Cost Efficiency**: ~$1.60 for full analysis vs $5.32 for OpenAI (70% savings)
- **Analysis Length**: Average 145 characters (shorter than quotes as required)

### Streamlit App Deployment
- **Production URL**: https://hansardquotesformanoj.streamlit.app/
- **Features**: Year filtering, frame filtering, sorting, CSV export
- **Interface**: Clean white design with SF Pro fonts, expandable quote cards
- **Performance**: Cached database connections, backwards compatibility

### Key Technical Files
- **app.py**: Main Streamlit application with neutral-tone database integration
- **claude_historian.py**: AI analysis system with historical context mapping
- **verification_and_formatting.py**: Speaker verification against actual Hansard pages
- **neutralize_tone.py**: Academic tone removal for direct, readable analyses

### Academic Documentation
- **DOCUMENTATION_FOR_LABOUR_LAW_PROFESSORS.md**: Comprehensive academic documentation
- **Target Users**: Legal scholars, historians, policy researchers
- **Research Applications**: Statutory interpretation, comparative legal history, doctrinal development

### Quality Standards Achieved
- ✅ Verified speaker attributions (89.1% accuracy)
- ✅ Neutral tone analyses without academic pretension
- ✅ Complete sentences (no truncation issues)
- ✅ Analyses shorter than original quotes
- ✅ Direct link to original Hansard sources for verification
- ✅ Academic-grade documentation for scholarly use

### Current Production State
The application is a complete, production-ready academic research tool providing systematic access to verified parliamentary discourse on immigration-labour intersection during Britain's foundational legal period (1900-1930).

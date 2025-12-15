
# ALINA

ALINA is an acronym that stands for: **Assistant for Learning, Insight, and Navigating Ambitions**

## Development Environment

```bash
uv sync
.\.venv\Scripts\activate.bat

# Running the app
alina --help
```

## Expected Folder Structure

The application expects the following folder structure:

```
<parent-directory>/
├── data/                       # Input data folder (one level above repository)
│   ├── jobs/                   # Job descriptions (*.md files)
│   │   ├── j001.md
│   │   ├── j002.md
│   │   └── ...
│   └── trainings/              # Training descriptions (*.md files)
│       ├── tr001.md
│       ├── tr002.md
│       └── ...
└── <repository-root>/
    ├── .git/
    ├── alina/                  # This project (Git repository)
    │   ├── src/
    │   ├── pyproject.toml
    │   └── README.md
    └── workspace/              # Generated/working files
        ├── jobs.json           # Analyzed job data
        ├── trainings.json      # Analyzed training data
        ├── personas.json       # Analyzed persona data
        ├── skills.json         # Skills taxonomy
        ├── manual-intents.json # Manual user intent mappings
        ├── training_suggestions.json
        ├── submissions.json    # Submission history
        ├── interviews/         # Initial interview transcripts
        │   ├── persona_001.md
        │   └── ...
        ├── interviews_job/     # Job-focused interview transcripts
        │   ├── persona_001.md
        │   └── ...
        ├── interviews_training/ # Training-focused interview transcripts
        │   ├── persona_001.md
        │   └── ...
        ├── interview_summaries/ # Interview summaries
        │   ├── persona_001_summary.md
        │   └── ...
        ├── suggestions/        # Generated suggestions
        │   ├── in_progress/    # Work-in-progress suggestions
        │   ├── suggestions_001.json
        │   └── ...
        └── submissions/        # Submitted files
            ├── submission_001.json
            └── ...
```

**Notes:**
- The `data/` folder is located **one level up** from the Git repository root
- The `data/` folder contains input markdown files for jobs and trainings
- The `workspace/` folder is automatically created within the repository root and contains all generated/working files
- The application uses `.git` directory detection to locate the repository root
- The `workspace/` folder is automatically created within the repository root and contains all generated/working files. Nothing is ignored in this folder, so we can track everything under version control if needed.

## Available Commands

### analyze
Analyze input data (jobs and trainings).

**Arguments:**
- `--ai [azure|bedrock|mistral]` - AI provider to use (optional, uses mock analyzer if not specified)
- `--jobs-only` - Only analyze jobs (default: False)
- `--trainings-only` - Only analyze trainings (default: False)
- `--only TEXT` - Analyze only a specific element by ID

**Example:**
```bash
alina analyze --ai bedrock
alina analyze --jobs-only
alina analyze --only j001
```

### build-skills
Build skills taxonomy from training analysis.

**Arguments:**
- `--ai [azure|bedrock|mistral]` - AI provider to use (required)

**Example:**
```bash
alina build-skills --ai bedrock
```

### chat
Chat with ALINA in an interactive interview session.

**Arguments:**
- `--ai [azure|bedrock|mistral]` - AI provider to use (optional, uses mock interviewer if not specified)

**Example:**
```bash
alina chat --ai mistral
```

### chat-persona
Chat with personas based on a given identifier.

**Arguments:**
- `identifier` - Persona identifier (required, positional argument)
- `--ai` - Use AI-powered persona chatter instead of mock (default: False)

**Example:**
```bash
alina chat-persona 5 --ai
```

### experiment
Run experimental analysis on submission data.

**Arguments:**
None

**Example:**
```bash
alina experiment
```

### fuzzy
Apply fuzzy logic to limit trainings and jobs in a submission.

**Arguments:**
- `--submission INTEGER` - Submission ID to apply fuzzy logic to (required)
- `--seed TEXT` - Random seed for reproducibility (required)

**Example:**
```bash
alina fuzzy --submission 108 --seed myseed123
```

### interview
Interview personas to gather their details.

**Arguments:**
- `--persona TEXT` - Persona range to interview (e.g., "5", "1-10", "all") (default: all)
- `--ai [azure|bedrock|mistral]` - AI provider to use (optional, uses mock if not specified)

**Example:**
```bash
alina interview --persona 1-10 --ai bedrock
alina interview --persona 5
```

### interview-job
Conduct job-specific interviews with personas.

**Arguments:**
- `--ai [azure|bedrock|mistral]` - AI provider to use (required)

**Example:**
```bash
alina interview-job --ai mistral
```

### interview-training
Conduct training-specific interviews with personas.

**Arguments:**
- `--ai [azure|bedrock|mistral]` - AI provider to use (required)

**Example:**
```bash
alina interview-training --ai bedrock
```

### merge
Merge two submissions into one (one for jobs, one for trainings).

**Arguments:**
- `--jobs INTEGER` - Job submission ID (required)
- `--trainings INTEGER` - Training submission ID (required)

**Example:**
```bash
alina merge --jobs 101 --trainings 102
```

### presuggest
Preprocess suggestions for each persona by analyzing interview data.

**Arguments:**
- `--ai [azure|bedrock|mistral]` - AI provider to use (optional, uses mock if not specified)
- `--persona TEXT` - Persona range to process (e.g., "5", "1-10", "all") (default: all)

**Example:**
```bash
alina presuggest --persona 1-50 --ai bedrock
```

### rank
Show submissions and leaderboard rankings.

**Arguments:**
- `--head INTEGER` - Number of top entries to show (default: 5)

**Example:**
```bash
alina rank --head 10
```

### status
Get system status including AWS, Mistral, and Amazon Bedrock connectivity.

**Arguments:**
None

**Example:**
```bash
alina status
```

### submissions
Generate an Excel file of all submissions with detailed analysis.

**Arguments:**
- `--tail INTEGER` - Show only the last N submissions (optional)
- `--inspect INTEGER` - Inspect a specific submission by ID (optional, otherwise uses latest)

**Example:**
```bash
alina submissions --tail 20
alina submissions --inspect 105
```

### submit
Submit the last computed suggestions for each persona.

**Arguments:**
None

**Example:**
```bash
alina submit
```

### suggest
Suggest job/training matches for each persona.

**Arguments:**
- `--ai [azure|bedrock|mistral]` - AI provider to use (optional, uses mock if not specified)
- `--persona TEXT` - Persona range to process (e.g., "5", "1-10", "all") (default: all)
- `--skip-jobs` - Skip job suggestions (default: False)
- `--skip-trainings` - Skip training suggestions (default: False)

**Example:**
```bash
alina suggest --persona 1-100 --ai bedrock
alina suggest --skip-jobs
```

### suggest-training
Suggest trainings for each person using advanced skill matching.

**Arguments:**
- `--ai [azure|bedrock|mistral]` - AI provider to use (required)
- `--path PATH` - Path to data folder (required)

**Example:**
```bash
alina suggest-training --ai bedrock --path ./data
```

### version
Show the version of the application.

**Arguments:**
None

**Example:**
```bash
alina version
```

## Usage
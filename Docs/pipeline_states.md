#  `pipeline_states.md` — v1 (Authoritative)

> A song ingestion pipeline is a **state machine**.  
> Each state must be:
> 
> - deterministic
>     
> - resumable
>     
> - observable
>     

No hidden magic. No vibes.

---

## 🧭 State Overview (Happy Path)

```
INIT
  ↓
SEARCHING
  ↓
DOWNLOADING
  ↓
EXTRACTING
  ↓
MATCHING_METADATA
  ↓
TAGGING
  ↓
STORING
  ↓
FINALIZED
```

Failures can occur **at any state** and must be explicit.

---

## 1️⃣ INIT

### Purpose

Validate input and create a job context.

### Inputs

- raw query string (e.g. `"Time - Pink Floyd"`)
    

### Actions

- normalize query
    
- generate `job_id`
    
- create temp working directory
    

### Possible Failures

- empty query
    
- invalid characters
    

### On Success → `SEARCHING`

---

## 2️⃣ SEARCHING

### Purpose

Find candidate audio sources.

### Actions

- invoke **yt-dlp** search mode
    
- retrieve top N video candidates
    
- rank by relevance heuristics
    

### Output

- list of candidate URLs
    

### Failures

- no results
    
- yt-dlp execution error
    
- network failure
    

### On Success → `DOWNLOADING`

---

## 3️⃣ DOWNLOADING

### Purpose

Acquire raw audio.

### Actions

- download best available audio stream
    
- save to temp directory
    
- record source info
    

### Rules

- this file is **temporary**
    
- format does NOT matter here
    

### Failures

- video unavailable
    
- download interrupted
    
- ffmpeg missing
    

### On Success → `EXTRACTING`

---

## 4️⃣ EXTRACTING

### Purpose

Convert raw audio into target format.

### Actions

- convert to FLAC or MP3 (rule-based)
    
- normalize sample rate
    
- ensure playable output
    

### Output

- clean audio file (still untagged)
    

### Failures

- codec failure
    
- corrupted stream
    
- conversion error
    

### On Success → `MATCHING_METADATA`

---

## 5️⃣ MATCHING_METADATA

### Purpose

Find **authoritative metadata**.

### Actions

- query metadata providers
    
- score matches
    
- select best candidate
    

### Output

- metadata object
    
- confidence score
    

### Rules

- YouTube title is NOT used as truth
    
- confidence must exceed threshold
    

### Failures

- no confident match
    
- provider rate-limit
    
- ambiguous results
    

### On Success → `TAGGING`

---

## 6️⃣ TAGGING

### Purpose

Embed metadata into audio file.

### Actions

- write title, artist, album, year
    
- embed album art
    
- validate tag integrity
    

### Rules

- mandatory tags must exist
    
- no partial tagging allowed
    

### Failures

- tag write error
    
- missing required fields
    
- album art fetch failure
    

### On Success → `STORING`

---

## 7️⃣ STORING

### Purpose

Move file into final library structure.

### Actions

- resolve artist/album directories
    
- handle filename conflicts
    
- move file atomically
    

### Output

- final file path
    

### Failures

- permission issues
    
- disk full
    
- naming conflict not resolvable
    

### On Success → `FINALIZED`

---

## 8️⃣ FINALIZED

### Purpose

Mark job as complete.

### Actions

- persist job record
    
- clean temp files
    
- emit success log
    

### Output

- song available in library
    

This is the **only terminal success state**.

---

## ❌ FAILED (Terminal)

### Purpose

Explicit failure with reason.

### Required Fields

- failed_state
    
- error_code
    
- human-readable message
    

### Rules

- no silent failure
    
- no partial files in library
    

---

## 🔁 Retry & Resume Rules

- States **before `STORING`** are retryable
    
- `STORING` must be **idempotent**
    
- `FINALIZED` is immutable
    

No state is allowed to “half succeed”.

---

## 🧠 Design Truth (read twice)

This pipeline:

- can run synchronously
    
- can be async later
    
- can be exposed as API
    
- can be resumed after crash
    

…because it’s **state-driven**, not script-driven.


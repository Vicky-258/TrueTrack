#  `job_model.md` — v1 (Canonical)

> A **Job** represents a single, end-to-end attempt to ingest one song  
> from query → finalized file.

A job is:

- stateful
    
- auditable
    
- resumable
    
- immutable once finalized
    

---

## 🆔 Job Identity

### Fields

- `job_id` (UUID)
    
- `created_at`
    
- `updated_at`
    

**Rules**

- `job_id` is generated at `INIT`
    
- never reused
    
- used for logs, temp dirs, retries
    

---

## 🧾 Input

### Fields

- `raw_query`  
    Example: `"Time - Pink Floyd"`
    
- `normalized_query`  
    Example: `"time pink floyd"`
    

**Rules**

- normalization happens once
    
- raw input is preserved for audit
    

---

## 🔄 State Tracking

### Fields

- `current_state`
    
- `previous_state`
    
- `state_history[]`
    

Each state entry contains:

- `state`
    
- `entered_at`
    
- `exited_at`
    
- `status` (success / failed)
    

**Rules**

- states only move forward
    
- history is append-only
    
- no state is skipped
    

---

## 📥 Source Acquisition

### Fields

- `source_type` (youtube)
    
- `source_candidates[]`
    

Each candidate:

- `url`
    
- `title`
    
- `duration`
    
- `uploader`
    
- `rank_score`
    

**Rules**

- multiple candidates allowed
    
- chosen source must be recorded
    

---

## 🎧 Download & Extraction

### Fields

- `downloaded_file_path` (temp)
    
- `original_format`
    
- `final_format` (mp3 / flac)
    
- `bitrate` (if mp3)
    
- `sample_rate`
    

**Rules**

- temp paths never leak into final state
    
- original format kept for debugging only
    

---

## 🧠 Metadata Resolution

### Fields

- `metadata_provider`
    
- `metadata_candidates[]`
    

Each candidate:

- `title`
    
- `main_artist`
    
- `album`
    
- `year`
    
- `confidence_score`
    

### Selected Metadata

- `final_metadata`
    
- `final_confidence_score`
    

**Rules**

- exactly one metadata candidate is selected
    
- confidence must meet threshold
    
- metadata is immutable after selection
    

---

## 🏷️ Tagging

### Fields

- `tagging_status`
    
- `embedded_album_art` (bool)
    
- `tag_validation_passed` (bool)
    

**Rules**

- tagging must fully succeed or fully fail
    
- partial tagging invalidates job
    

---

## 📁 Storage

### Fields

- `final_file_path`
    
- `library_artist`
    
- `library_album`
    
- `filename`
    

**Rules**

- derived only from final metadata
    
- naming rules strictly enforced
    
- no overwrite without explicit suffix
    

---

## ❌ Error Handling

### Fields

- `failed_state`
    
- `error_code`
    
- `error_message`
    
- `retry_count`
    

**Rules**

- failure is terminal unless retried
    
- retries increment counter
    
- error info must be human-readable
    

---

## 🧹 Cleanup

### Fields

- `temp_dir_path`
    
- `cleanup_status`
    

**Rules**

- cleanup happens only after FINALIZED or FAILED
    
- failure to cleanup is logged, not fatal
    

---

## 📊 Observability (Optional but Smart)

### Fields

- `logs[]`
    
- `timings` (per state)
    
- `warnings[]`
    

This makes debugging **10x easier** later.

---

## 🔐 Job Immutability Rules

- `FINALIZED` jobs cannot change
    
- `FAILED` jobs can be retried → new job_id OR reset state (decision later)
    
- Metadata and filenames never mutate post-store
    

---

## 🧠 Big Picture Insight (important)

With this job model:

- CLI = thin wrapper
    
- API = thin wrapper
    
- UI = thin wrapper
    

**The job is the product.**

Everything else just _observes_ it.


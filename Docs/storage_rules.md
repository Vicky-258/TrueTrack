#  `storage_rules.md` (Draft v1)

## What We Store (Media Format Rules)

### 🎵 Audio Formats

We allow **two formats only**:

- **FLAC** → _preferred / premium_
    
- **MP3** → _fallback / compatibility_
    

**Rules:**

- If source quality allows → **FLAC**
    
- Else → **MP3 (320kbps CBR preferred)**
    

❌ No AAC, OPUS, M4A, WEBM stored permanently  
Those are **intermediate formats only**, never final output.

> Reason: Long-term reliability, predictable tooling, and clean tagging.

---

## 2️⃣ How We Store (Ingestion Philosophy)

### 🔧 Download Source

- **yt-dlp** is used **only** to obtain raw audio
    
- yt-dlp metadata is considered **untrusted**
    

### 🧠 Metadata Source (Truth Layer)

- Metadata comes from **external metadata providers**
    
- These define:
    
    - Song title
        
    - Main artist
        
    - Album
        
    - Release year
        
    - Album art
        

**Rule:**

> Metadata providers override YouTube titles **always**

yt-dlp is a shovel.  
Metadata providers are the map.

---

## 3️⃣ Naming Rules (Critical – Do Not Break)

### 📁 File Name Format

```
Song Name - Artist.ext
```

Examples:

```
Time - Pink Floyd.flac
Numb - Linkin Park.mp3
```

### 🎤 Artist Definition

- **Artist = main / primary artist only**
    
- No:
    
    - featured artists
        
    - “feat.”
        
    - “&”
        
    - producer names
        

**Reason (important):**

- Keeps filenames clean
    
- Avoids breaking **lyrics search**
    
- Prevents combinatorial filename chaos
    

Featuring artists live in **metadata tags**, not filenames.

---

## 4️⃣ Metadata Tagging Rules (ID3 / Vorbis)

### Mandatory Tags

Every stored file **must** contain:

- Title
    
- Main Artist
    
- Album
    
- Album Artist
    
- Track Number _(if available)_
    
- Year _(if available)_
    
- Embedded Album Art
    

If **any mandatory tag fails**, the file is **not finalized**.

---

## 5️⃣ Storage Structure (Filesystem Rules)

```
/Music
  /Artist
    /Album
      Song Name - Artist.ext
```

Example:

```
/Music
  /Pink Floyd
    /The Dark Side of the Moon
      Time - Pink Floyd.flac
```

**Rules:**

- Folder names come from metadata provider
    
- Never infer folders from YouTube data
    
- No duplicate artist folders with casing differences
    

---

## 6️⃣ Conflict Resolution Rules

### If filename already exists:

- Compare metadata hashes
    
- If same → skip download
    
- If different → append suffix:
    

```
Song Name - Artist (alt).flac
```

No silent overwrites. Ever.

---

## 7️⃣ Future-Proofing Rules (Intentional Constraints)

- Filename simplicity > completeness
    
- Metadata richness > filename richness
    
- Local-first always
    
- No cloud assumptions
    
- No streaming logic mixed with storage logic
    

---

## 8️⃣ Non-Goals (Explicitly Out of Scope)

- Public hosting
    
- Streaming to others
    
- DRM removal logic
    
- UI-first design
    
- Social features
    

This is a **personal ingestion backend**, not a platform.

---

## 🔥 Why these rules are smart (short truth)

You’re optimizing for:

- long-term maintainability
    
- predictable automation
    
- clean search & lyrics integration
    
- zero ambiguity
    

Most people screw this up by being “flexible”.  
You’re being **correct** instead 😏
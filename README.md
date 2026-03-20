# Legal, Privacy & Data Handling

This project is an independent, open-source historical mirror of public in-game events from **hordes.io**.  

## 1. Data Classification (Public Event Logs)
This database records **Public World Events** (e.g., Boss Kills) that are broadcast by the game via public tables.  

- **Pseudonymization:** Historical event data is stored using pseudonymized character labels as provided by the public game state. We do not collect Google Auth IDs, emails, IP addresses, or other personally identifiable information.  
- **No Connection:** This system is entirely decoupled from the official **hordes.io** authentication systems (e.g., Google Auth).

## 2. GDPR Compliance & the “Identification” Shield (Art. 11)
Under GDPR Article 11, maintainers cannot identify the natural person behind any character name.  

- **Verification Limitations:** We cannot verify ownership of character names because we have no access to the game’s private database. Requests to modify or erase event data are therefore processed in accordance with GDPR guidance, noting that identification of the requester is impossible. Deleting data based on an unverified request would risk a security breach against the actual owner of that character's history. To verify an erasure request, we would require the user to provide official Hordes.io account credentials or PII. In accordance with the principle of Data Minimization, we refuse to collect such sensitive data, rendering verification—and thus erasure—legally impossible under Art. 12(2).
- **Automated Anonymization:** If a player deletes their character in-game, the corresponding entry in our dataset eventually reverts to a numeric `game_id`. This ensures compliance with the “Right to Erasure” through anonymization while preserving historical records.

## 3. Historical Integrity (Art. 89)
This archive serves **statistical and historical purposes** for the gaming community. To preserve the chronological integrity of Top Lists and Boss Logs, historical snapshots are maintained “as-is” under GDPR Article 89. Retroactive editing of static logs is not supported, except for anonymization when a character is deleted in-game.  

## 4. Non-Affiliation & Takedown
- **Ownership:** This project is not affiliated with, endorsed by, or mirrored from **dekdev**. All game-related terminology, assets, and character stats remain the property of the Rights Holder.  
- **Scraping Ethics:** Data is collected responsibly at low frequency to avoid impacting official game infrastructure. Requests to cease scraping or remove data from this project will be respected via formal GitHub Issues.  

## 5. Data Architecture & Privacy
- **Public Logs:** Historical event data is stored in pseudonymized, hashed JSON files.  
- **Private Processing:** Character metadata is handled in a private processing cache and is not committed to the public repository.  
- **License:** The software is licensed under MIT, and the resulting dataset is licensed under **CC BY-NC-SA 4.0**.

---

<!-- LOGS_START -->
```text
[2026-03-20 17:39:20 UTC] Sync finished.
[2026-03-20 17:39:20 UTC] Saving 25 modified players...
[2026-03-20 17:39:20 UTC] Update globals.
[2026-03-20 17:39:10 UTC] Resuming from ID: 59582.
[2026-03-20 16:52:45 UTC] Sync finished.
[2026-03-20 16:52:45 UTC] Saving 55 modified players...
[2026-03-20 16:52:45 UTC] Update globals.
[2026-03-20 16:52:35 UTC] ID: 59580..
[2026-03-20 16:52:34 UTC] Resuming from ID: 59577...
[2026-03-20 15:50:30 UTC] Sync finished.
[2026-03-20 15:50:30 UTC] Saving 14 modified players...
[2026-03-20 15:50:30 UTC] Update globals.
[2026-03-20 15:50:21 UTC] Resuming from ID: 59577.
[2026-03-20 14:50:12 UTC] Sync finished.
[2026-03-20 14:50:12 UTC] Saving 37 modified players...
```
<!-- LOGS_END -->

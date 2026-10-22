# Lecture transcripts: privacy and permission

Recording or transcribing a lecture is not automatically allowed. Before you use Granola (or any transcription tool) in a lecture:

1. **Check the rules.** Read your institution's policy on recording lectures and on using AI tools, and the course's own rules. Some lecturers allow recording, some do not, and some allow it for personal study only.
2. **Ask when in doubt.** If the policy is unclear, ask the lecturer before transcribing. A recording made against the rules can be a disciplinary matter.
3. **Keep transcripts private.** A transcript is the lecturer's words, and it may capture other students' voices and questions. Keep it on your own machine, for your own study:
   - transcripts go in `Sources/transcripts/`, which the vault's `.gitignore` excludes, so they are never pushed to GitHub;
   - never share, post or upload them;
   - delete them when you no longer need them.
4. **Notes, not copies.** `/learn:lecture` writes what was said into your notes in your own words, quotes at most a sentence, and never names or quotes other people in the room.
5. **Your Granola account.** Transcripts also live in your Granola account, under Granola's own terms and privacy policy. The plugin signs in with OAuth; its stored settings sit in `.obsidian/plugins/granola-meetings-simple-sync/`, which the vault's `.gitignore` also excludes (`.obsidian/plugins/*/data.json`).

If your institution does not allow transcription, skip this module: everything else in the plugin works without it.

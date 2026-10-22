# Optional: Granola lecture transcripts

[Granola](https://www.granola.ai) transcribes what is said in a lecture. The [Granola Meetings Simple Sync](https://github.com/philfreo/obsidian-granola-plugin) Obsidian plugin (MIT, by Phil Freo) copies each transcript into your vault through Granola's official MCP API. `/learn:lecture` then adds what the lecturer said aloud (explanations, examples, emphasis) to that lecture's notes, while the slides stay the authority for every formula.

**Read [PRIVACY.md](PRIVACY.md) first.** Only transcribe where your institution and lecturer allow it.

## Setup

1. **Install the plugin.** In Obsidian, open Settings, then Community plugins, and install "Granola Meetings Simple Sync" (or install it through the BRAT plugin with `philfreo/obsidian-granola-plugin`). Enable it.
2. **Sign in.** In the plugin's settings, click **Connect to Granola**. Your browser opens for OAuth sign-in and returns you to Obsidian. No API key is needed.
3. **Settings:**

   | Setting | Value |
   |---|---|
   | Folder path | `Sources/transcripts` |
   | Filename pattern | `{date} {title}` |
   | Template path | `Templates/Granola.md` |
   | Include transcripts (called "Sync transcripts" in some versions) | **On** (off by default; without it `{{granola_transcript}}` is empty) |
   | Only my meetings | On |
   | Skip existing notes | On, so your edits to a transcript note survive the next sync |

4. **Copy the template.** Copy `Granola.md` from this folder into your vault's `Templates/` folder.
5. **After each lecture:** let the plugin sync, open the new note in `Sources/transcripts/`, set `course:` and `lecture:` in its frontmatter, then run:

   ```
   /learn:lecture COURSE101 3
   ```

   The skill finds the transcript, reads it against that lecture's slides and notes, shows you a plan, and after you confirm adds a `## From the lecture` section to each affected note. It lists every place the transcript disagreed with the slides, and every formula that was only spoken, for you to check.

## How the pieces connect

- **API** (Application Programming Interface): a defined way for one program to ask another for data. The plugin uses Granola's API to fetch your transcripts.
- **Connector, or MCP** (Model Context Protocol): a standard plug that lets an app reach a tool or a source of data. Granola's API is served over MCP, which is why the plugin signs in with OAuth instead of a password.
- Obsidian stores the transcript as a plain Markdown file in your vault, so Claude Code reads it like any other note.

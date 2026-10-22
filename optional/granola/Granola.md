---
title: "{{granola_title}}"
type: source
course: 
lecture: 
date: {{granola_date}}
granola_id: {{granola_id}}
granola_url: {{granola_url}}
---

# {{granola_title}}

Lecture transcript, synced from Granola. Private: this folder is excluded from git. Set `course:` and `lecture:` above, then run `/learn:lecture <course> <lecture>`.

{{#granola_duration_formatted}}{{granola_start_time}} to {{granola_end_time}} ({{granola_duration_formatted}})

{{/granola_duration_formatted}}{{#granola_private_notes}}## My notes

{{granola_private_notes}}

{{/granola_private_notes}}{{#granola_enhanced_notes}}## Granola summary

{{granola_enhanced_notes}}

{{/granola_enhanced_notes}}{{#granola_transcript}}## Transcript

{{granola_transcript}}
{{/granola_transcript}}

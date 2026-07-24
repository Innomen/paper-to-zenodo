# Paper to Zenodo

Reusable GitHub Action for publishing Markdown papers to Zenodo.

The action reads the title, author, abstract, and keywords from the canonical Markdown source, uploads the supplied PDF as a public Publication / Preprint, applies Zenodo's free-to-read rights statement, publishes the record, and returns its DOI and public URL.

Paper repositories retain only a thin release workflow. They do not carry a copy of the publisher.

## Source format

The Markdown source must contain:

- One `# Title`
- The author on a bold-only line
- A `## Abstract` section
- A comma-separated `**Keywords:**` line

## Required token

The calling repository's `ZENODO_TOKEN` secret needs:

- `deposit:write`
- `deposit:actions`

## Rights

Files are publicly downloadable under Zenodo's `zenodo-freetoread-1.0` rights statement: free for private use, with other rights including distribution retained by the rightsholder. The generated description also states that all rights are reserved.

## Release workflow

See `examples/publish-paper.yml`.

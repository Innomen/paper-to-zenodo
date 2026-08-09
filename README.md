# Paper to Zenodo

Reusable GitHub Action for publishing Markdown papers to Zenodo.

The action reads the title, author, abstract, and keywords from the canonical Markdown source, uploads the supplied PDF as a public Publication / Preprint, applies Zenodo's free-to-read rights statement, publishes the record, and returns its DOI and public URL.

Paper repositories retain only their canonical Markdown, publication PDF, README, and rights file. They do not carry a copy of the publisher or a repository-specific Zenodo secret.

## Source format

The Markdown source must contain:

- One `# Title`
- The author on a bold-only line
- A `## Abstract` section
- A comma-separated `**Keywords:**` line

## Required token

The credential-bearing publisher dispatcher's `ZENODO_TOKEN` secret needs:

- `deposit:write`
- `deposit:actions`

## Rights

Files are publicly downloadable under Zenodo's `zenodo-freetoread-1.0` rights statement: free for private use, with other rights including distribution retained by the rightsholder. The generated description also states that all rights are reserved.

## Dispatch workflow

EMS currently dispatches external paper repositories through `Innomen/bootstrap-merchants/.github/workflows/publish-external-paper.yml`, which holds the credential once and accepts the public repository, ref, source path, and PDF path as inputs. The paper repository's GitHub release is created after Zenodo returns the DOI.

`examples/publish-paper.yml` remains a standalone alternative for installations that deliberately prefer one secret per paper repository.

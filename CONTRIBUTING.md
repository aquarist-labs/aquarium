# Contributing

This document outlines some basic guidelines for contributing to the `backend` repository
within *Aquarist Labs*. 

We are very welcoming of new feature implementation, patches that fix bugs or code
cleanup. 

We are still orientating ourselves with the project, please be patient while this file
and others continuously update.

### Checking out the source

You can clone from github with:

	git clone git@github.com:aquarist-labs/backend

Or:

	git clone git://github.com/aquarist-labs/backend

### Submitting Bugs and Requesting New Features

All bugs and feature requests can be filed in "Issues" in [Planning and Discussion](https://github.com/aquarists-labs/planning-and-discussion/issues).
We use GitHub templates to manage the requests. You will either select:

- Feature
- Bug
- Question

Ensure the appropriate label is selected before submitting your issue.

## Contributor Guidelines

Do not merge directly into the `main` branch. It is protected for a reason.

## Writing Commit Messages

Git commit messages should start with a maxiumum 72 character or less summary in a single
paragraph, and prefixed with the module you are changing. For example:

```
   backend: add initial README doc
   doc: fix a typo
```

The following paragraph(s) should explain the change in more detail; be as specific as possible.
If the commit message title was too short to fully state what the commit is doing, use the body
to explain not just the "what", but also the "why". For example:

```
   backend: add initial README doc
   
   This commit introduces the first README doc for aquarist labs.
```

If your changes addresses a bug or feature request, be sure to mention them in the body of the
commit message. For example:

```

   backend: add initial README doc
   
   This commit introduces the first README doc for aquarist labs.
   
   Closes #1
   
```

## Pull Request Best Practices

PRs should be opened on branches contained in your fork of `aquarist-labs/backend.git`. PRs should
target the `main` branch. 

If your PR has only one commit, the PR title can be the same as the commit title (and GitHub will 
uggest this). If the PR has multiple commits, do not accept the title GitHub suggests. Either use
the title of the most relevant commit, or write your own title.

## Document your changes

If you have added or modified any user-facing functionality, such as CLI commands or their output,
then the pull request must include appropriate updates to documentation.

It is the submitter's responsibility to make the changes, and the reviewer's responsibility to make
sure they are not merging changes that do not have the needed updates to documentation.

## Running Unit Tests

Before submitting your change, you should test it. But since this is not setup yet, we'll forgive you.

## Be Respectful

Although technical in nature, the Open Source community is first and foremost
about people. Treat other people with respect. Be kind, be open, respect the
culture of the community you are interacting with and be aware of the diversity
of people in that community. Be aware that, particularly in electronic communication,
you might misunderstand or misinterpret what others are saying or meaning. The
reverse is also true.

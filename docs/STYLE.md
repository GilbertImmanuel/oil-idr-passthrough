# Writing style

## Scope

These rules govern every piece of written English committed to this repository: code comments,
docstrings, markdown files, commit message bodies, notebook prose, and dashboard copy. They apply
to every contributor and to any automated agent that writes into the repository. A change that
violates a rule is corrected in review before it merges.

## Tone and voice

1. No conversational fillers or dramatic punctuation. Use periods and colons. Banned: em dashes, exclamation marks, conversational tildes, ellipses for trailing thoughts.
2. No pseudo-profound or philosophical musings. Do not raise code, data, or architecture to philosophy. Stay literal.
3. No narrative or metaphorical openings. Banned: "The threads connect", "The picture emerges", "The results tell a story", "At the heart of this". Start with the subject or the finding.
4. No dramatic declarative prose. Write like an audit.
5. No anthropomorphism. Models process, calculate, return, iterate, and fail. Models do not know, think, understand, strive, decide, or want.

## Data and semantics

6. No vague quantitative hedges. State the exact number, percentage, or delta. Banned: "add little", "much", "a handful of", "considerably", "significantly", "about a third". Exception: statistical uncertainty is reported in quantified form, with interval, p-value, and n. "Coefficient 0.31, 95 percent CI [0.08, 0.54], n=14" is compliant. "Oil moves the rupiah a lot" is not.
7. No hyperbolic marketing buzzwords. Banned: "blazing fast", "effortlessly", "powerful", "cutting-edge", "game-changing", "unparalleled", "seamless". Use metrics, Big-O notation, or latency.
8. No forced metaphors, analogies, or literary compounds. No poetic hyphenated adjectives.
9. No adjective and adverb stacking. Three or more modifiers in sequence is banned.

## Structure and syntax

10. No repetitive sentence structure. Do not open consecutive sentences or bullets with "This [noun]" or "The [class]". Use the imperative for instructions.
11. No contrastive rhythm. Do not alternate clauses with repeated "while", "whereas", "however", "yet" to build cadence. The words are permitted. The pattern is not.
12. No binary contrast reframing. Banned: "It is not just X, it is Y", "This does not merely do X", "More than just a framework".
13. No decorative closings. Banned: "In conclusion", "Happy coding", "Happy building". A numbered Findings block at the end of an analysis document is required and is not a decorative closing.
14. No incomplete or dangling thoughts. End on a complete syntactic unit with terminal punctuation.

## Banned words and phrases

15. Plain word substitutions:
    - leverages, utilizes to uses
    - delves into to examines, checks
    - showcases, highlights to shows, displays
    - robust to stable, type-safe
    - realm, landscape to ecosystem, space
    - crucial, essential, vital to required, necessary
16. "A testament to" is banned.
17. No rhetorical questions. Banned: "But how does it work?", "What makes it special?", "Ready to get started?" Use plain headings: "How it works", "Features", "Getting started".
18. No "most developers" comparative trope. Banned: "Unlike other tools", "Tired of X?", "Most developers struggle with".
19. No hypothetical user narration. Banned: "Imagine you are trying to". State the use case directly.

## Project-specific additions

20. No causal verbs unless the design identifies a causal effect. Use "associated with", "Granger-precedes", "coincides with", "is followed by". Reserve "causes", "drives", "leads to", and "impacts" for designs that support them. VAR and Granger tests do not.
21. Every number in a comment, markdown file, docstring, or chart annotation carries a source tag and retrieval date. Format: `[FRED:DCOILBRENTEU, 2026-08-10]`. Numbers without a tag are removed in review.

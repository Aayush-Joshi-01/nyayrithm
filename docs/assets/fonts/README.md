# Fonts

Self-hosted latin (`woff2`) subsets, so the docs site has no runtime dependency
on Google Fonts. Same typefaces the app loads via `next/font`.

| File | Family | Weights | License |
|---|---|---|---|
| `spectral-*-latin.woff2` | Spectral (Prod Type) | 400, 400 italic, 500, 600 | SIL Open Font License 1.1 |
| `libre-franklin-latin.woff2` | Libre Franklin (Impallari Type) | 400 to 600 variable | SIL Open Font License 1.1 |
| `jetbrains-mono-latin.woff2` | JetBrains Mono (JetBrains) | 400 to 500 variable | SIL Open Font License 1.1 |

Subsets pulled from the Google Fonts CSS API. To refresh, re-download the `latin`
`@font-face` `src` for each family and keep the filenames stable.

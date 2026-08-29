/* Runs before first paint (injected as an inline <script> in the root layout) to
   set data-theme so there is no flash. Kept tiny and dependency-free. */
export const THEME_STORAGE_KEY = "nyay-theme"

export const THEME_TITLES = {
  dark: "The court, after hours.",
  light: "The court, in session.",
} as const

export const themeInitScript = `
(function () {
  try {
    var stored = localStorage.getItem('${THEME_STORAGE_KEY}');
    var root = document.documentElement;
    if (stored === 'light' || stored === 'dark') {
      root.setAttribute('data-theme', stored);
    } else {
      root.removeAttribute('data-theme');
    }
    var resolved = root.getAttribute('data-theme') ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    root.style.colorScheme = resolved;
    // enable transitions only after the first paint
    requestAnimationFrame(function () { root.classList.add('theme-ready'); });
  } catch (e) {}
})();
`

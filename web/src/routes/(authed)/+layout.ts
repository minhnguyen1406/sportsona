// Auth depends on localStorage, which only exists in the browser. Rendering
// authed pages on the server would always show "loading" anyway.
export const ssr = false;

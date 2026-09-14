const paths = {
  arrow: '<path d="M4 12h15m-6-6 6 6-6 6"/>',
  back: '<path d="M20 12H5m6-6-6 6 6 6"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  code: '<path d="m8 6-6 6 6 6m8-12 6 6-6 6m-3-14-2 16"/>',
  spark:
    '<path d="m12 2 2.6 7.4L22 12l-7.4 2.6L12 22l-2.6-7.4L2 12l7.4-2.6Z"/>',
  pen: '<path d="m4 17-1 4 4-1L20 7l-3-3Zm10-10 3 3M3 22h18"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 15h7m-7 5h5"/>',
  megaphone:
    '<path d="m3 10 13-5v14L3 14Zm3 5 2 6h3l-2-5M20 8l2-2m-2 6h3m-3 4 2 2"/>',
  people:
    '<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6m2 3a5 5 0 0 1 4 5v2"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 22v-2a8 8 0 0 1 16 0v2"/>',
  badge:
    '<rect x="5" y="3" width="14" height="19" rx="2"/><path d="M9 3V1h6v2M9 17h6m-6 3h4"/><circle cx="12" cy="10" r="3"/>',
  logout: '<path d="M9 4H4v16h5m3-8h10m-5-5 5 5-5 5"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
  keyboard:
    '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M5 9h1m3 0h1m3 0h1m3 0h2M5 12h1m3 0h1m3 0h1m3 0h2M7 15h10"/>',
  camera: '<path d="M3 7h4l2-3h6l2 3h4v14H3Z"/><circle cx="12" cy="13" r="4"/>',
  shield: '<path d="M12 2 3 6v6c0 5 9 10 9 10s9-5 9-10V6ZM8 12l3 3 5-6"/>',
  nfc: '<path d="M5 8a6 6 0 0 1 0 8m4-12a12 12 0 0 1 0 16m4-19a16 16 0 0 1 0 22"/><circle cx="3" cy="12" r="1"/>',
  printer:
    '<path d="M6 8V2h12v6M6 17H2V8h20v9h-4M6 14h12v8H6Z"/><path d="M17 11h2M9 18h6"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v1"/>',
  mirror:
    '<rect x="6" y="2" width="12" height="17" rx="6"/><path d="M12 19v3m-5 0h10M10 6l4 4m-4 0 4 4"/>',
  alert: '<path d="m12 3 10 18H2Z"/><path d="M12 9v5m0 3v1"/>',
  receipt: '<path d="M5 2v20l3-2 4 2 4-2 3 2V2ZM8 7h8m-8 5h8m-8 5h5"/>',
};
export function icon(name, cls = "") {
  return `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.info}</svg>`;
}
export function logo(cls = "") {
  return `<svg class="${cls}" viewBox="0 0 48 48" fill="currentColor" aria-hidden="true"><path d="M3 36V10h8l13 17L37 10h8v26h-9V25L24 41 12 25v11Z"/></svg>`;
}

const $ = (selector, root = document) => root.querySelector(selector);
const motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');
const animateControl = $('#animate-previews');
animateControl.checked = !motionPreference.matches;
const mediaViews = [];

function node(tag, attributes = {}, ...children) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(attributes)) {
    if (value === null || value === undefined) continue;
    if (key === 'class') element.className = value;
    else if (key.startsWith('on')) element.addEventListener(key.slice(2), value);
    else if (key === 'hidden') element.hidden = Boolean(value);
    else element.setAttribute(key, String(value));
  }
  for (const child of children.flat()) {
    if (child !== null && child !== undefined) element.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return element;
}

const list = value => Array.isArray(value) ? value : [];
const numeric = value => typeof value === 'number' && Number.isFinite(value);
const format = (value, digits = 1) => numeric(value) ? value.toLocaleString('en-US', { maximumFractionDigits: digits }) : '—';
const setting = value => value === null || value === undefined ? '—' : typeof value === 'object' ? JSON.stringify(value) : String(value);
const order = run => typeof run.reverse_options === 'boolean' ? run.reverse_options ? 'Reverse' : 'Forward' : '—';

function safeURL(value) {
  if (typeof value !== 'string' || !value.trim()) return null;
  try {
    const url = new URL(value, document.baseURI);
    return ['http:', 'https:'].includes(url.protocol) ? url.href : null;
  } catch { return null; }
}

function link(label, href, attributes = {}) {
  const url = safeURL(href);
  return url ? node('a', { href: url, ...attributes }, label) : null;
}

function badge(run) {
  const status = run.success === true ? ['success', 'Successful'] : run.success === false ? ['failure', 'Unsuccessful'] : ['', 'Not assessed'];
  return node('span', { class: `status-badge ${status[0]}` }, status[1]);
}

function configBlock(title, value) {
  return node('details', { class: 'config-block' }, node('summary', {}, title), node('pre', {}, JSON.stringify(value, null, 2)));
}

function placeholder(title, description) {
  return node('div', { class: 'media-empty' },
    node('span', { 'aria-hidden': 'true', style: 'font-size:24px;line-height:1.2;color:#a4b592' }, '▧'),
    title, node('span', {}, description));
}

function createMedia(game, featured) {
  // Explicitly selected run first; otherwise the first recording in source order.
  const paths = { ...game.media, ...featured?.media };
  const gifURL = safeURL(paths.gif);
  const videoURL = safeURL(paths.video);
  const posterURL = safeURL(paths.poster);
  const frame = node('div', { class: 'media-frame' });
  const gifImage = gifURL ? node('img', { alt: `Recorded ${game.title} gameplay preview`, loading: 'lazy', decoding: 'async' }) : null;
  const posterImage = posterURL ? node('img', { src: posterURL, alt: `Still frame from the ${game.title} recording`, loading: 'lazy', decoding: 'async' }) : null;
  const video = videoURL ? node('video', { controls: '', playsinline: '', preload: 'none', poster: posterURL, 'aria-label': `Full ${game.title} rollout video` },
    node('source', { src: videoURL, type: 'video/mp4' }),
    'Your browser cannot play this recording. ', link('Open the video', videoURL)) : null;
  const gifButton = node('button', { type: 'button', 'aria-pressed': 'true' }, 'GIF preview');
  const videoButton = node('button', { type: 'button', 'aria-pressed': 'false' }, 'Full video');
  gifButton.disabled = !gifURL && !posterURL;
  videoButton.disabled = !videoURL;
  let active = gifURL || posterURL || !videoURL ? 'gif' : 'video';

  function update() {
    if (active === 'video' && video && frame.contains(video)) return;
    frame.replaceChildren();
    const showVideo = active === 'video' && video;
    gifButton.setAttribute('aria-pressed', String(!showVideo));
    videoButton.setAttribute('aria-pressed', String(Boolean(showVideo)));
    if (showVideo) frame.append(video);
    else {
      if (video) video.pause();
      if (animateControl.checked && gifImage) {
        gifImage.src = gifURL;
        frame.append(gifImage);
      } else if (posterImage) frame.append(posterImage);
      else if (gifImage) frame.append(placeholder('GIF preview paused', 'Enable “Animate GIF previews” to view the recording.'));
      else frame.append(placeholder('Recording pending', 'Actual experiment media will appear here.'));
    }
  }
  const mediaError = element => element?.addEventListener('error', () => {
    if (frame.contains(element)) frame.replaceChildren(placeholder('Recording unavailable', 'See the run ledger or open the original file.'));
  });
  [gifImage, posterImage, video].forEach(mediaError);
  video?.querySelector('source')?.addEventListener('error', () => {
    if (frame.contains(video)) frame.replaceChildren(placeholder('Recording unavailable', 'Use the original video link to inspect the file.'));
  });
  gifButton.addEventListener('click', () => { active = 'gif'; update(); });
  videoButton.addEventListener('click', () => { active = 'video'; update(); });
  update();
  mediaViews.push(update);

  const caption = featured
    ? `Shown: seed ${setting(featured.seed)} · ${order(featured).toLowerCase()} order${featured.id ? ` · ${featured.id}` : ''}`
    : 'No recorded run available';
  return node('div', { class: 'game-media' }, frame,
    node('div', { class: 'media-toolbar' },
      node('div', { class: 'media-tabs', role: 'group', 'aria-label': `${game.title} recording format` }, gifButton, videoButton),
      link('Open video ↗', videoURL, { class: 'media-download', target: '_blank', rel: 'noopener' })),
    node('p', { class: 'media-caption' }, caption));
}

function createResult(game, runs, featured) {
  const success = featured?.success === true;
  const statusText = !featured ? 'Pending' : success ? 'Completed' : featured.success === false ? 'Not completed' : 'Not assessed';
  const statusClass = !featured || typeof featured.success !== 'boolean' ? '' : success ? 'success' : 'failure';
  const hasCoverage = numeric(featured?.coverage_percent);
  const value = hasCoverage ? `${format(featured.coverage_percent, 2)}%` : format(featured?.reward, 1);
  const stats = node('dl', { class: 'mini-stats' });
  for (const [label, value] of [
    ['Shown run · simulation seconds', format(featured?.sim_seconds, 2)],
    ['Shown run · API calls', format(featured?.api_calls, 0)],
    ['Shown run · K / resolution', featured ? `${setting(featured.branching)} / ${setting(featured.resolution)}` : '—'],
    ['Shown run · mean action latency', numeric(featured?.mean_action_latency_s) ? `${format(featured.mean_action_latency_s, 2)} s` : '—']
  ]) stats.append(node('div', {}, node('dt', {}, label), node('dd', {}, value)));
  const result = node('div', { class: 'game-result' },
    node('div', { class: 'result-heading' }, node('span', { class: 'result-label' }, 'FEATURED RECORDING'), node('span', { class: `status-badge ${statusClass}` }, statusText)),
    node('div', { class: 'result-value' }, value, node('span', {}, hasCoverage ? 'track covered' : 'episode reward')),
    node('p', { class: 'result-criterion' }, game.success_criterion || 'Success is reported by the experiment runner.'), stats);
  if (list(game.notes).length) result.append(node('ul', { class: 'game-notes' }, game.notes.map(note => node('li', {}, note))));
  return result;
}

function createRunTable(runs, label) {
  const showCoverage = runs.some(run => numeric(run.coverage_percent));
  const headers = ['Run', 'Seed', 'Option order', 'K', 'Resolution', 'Reward', ...(showCoverage ? ['Track covered (%)'] : []), 'Outcome', 'Stop reason', 'Steps', 'Sim. seconds', 'API calls', 'Mean action (s)', 'Evidence'];
  const table = node('table', {}, node('caption', { class: 'visually-hidden' }, `${label}: all recorded attempts`),
    node('thead', {}, node('tr', {}, headers.map(text => node('th', { scope: 'col' }, text)))));
  const tbody = node('tbody');
  runs.forEach((run, index) => {
    const evidence = node('td');
    const sources = [link('Video ↗', run.media?.video, { target: '_blank', rel: 'noopener' }), link('GIF ↗', run.media?.gif, { target: '_blank', rel: 'noopener' }), link('Recorded trace ↗', run.trace, { target: '_blank', rel: 'noopener' })].filter(Boolean);
    evidence.append(...(sources.length ? sources : ['—']));
    tbody.append(node('tr', {},
      node('th', { scope: 'row' }, run.id || `Run ${index + 1}`),
      ...[setting(run.seed), order(run), setting(run.branching), setting(run.resolution), format(run.reward, 2)].map(value => node('td', {}, value)),
      ...(showCoverage ? [node('td', {}, format(run.coverage_percent, 2))] : []),
      node('td', {}, badge(run)),
      ...[run.stop_reason || '—', format(run.steps, 0), format(run.sim_seconds, 2), format(run.api_calls, 0), format(run.mean_action_latency_s, 3)].map(value => node('td', {}, value)), evidence));
  });
  table.append(tbody);
  return node('div', { class: 'table-scroll', tabindex: '0', role: 'region', 'aria-label': `${label} full results table; scroll horizontally for more columns` }, table);
}

function createLedger(game, runs) {
  const body = node('div', { class: 'run-ledger-body' });
  if (runs.length) {
    const successes = runs.filter(run => run.success === true).length;
    body.append(node('p', { class: 'table-hint' }, `${successes} successful recordings among ${runs.length} development attempts across settings. This is an experiment history, not an estimated success rate. All attempts appear below; “—” means not recorded.`), createRunTable(runs, game.title));
  } else body.append(node('p', { class: 'empty-ledger' }, 'No measurements have been supplied for this environment.'));
  const config = { environment: game.environment, action_dimensions: game.action_dimensions, success_criterion: game.success_criterion, ...game.config };
  const perRun = runs.filter(run => run.config).map(run => ({ id: run.id, seed: run.seed, reverse_options: run.reverse_options, ...run.config }));
  if (perRun.length) config.runs = perRun;
  body.append(configBlock('Environment & run configuration', config));
  return node('details', { class: 'run-ledger' },
    node('summary', {}, `Inspect all ${runs.length} run${runs.length === 1 ? '' : 's'}`, node('span', {}, 'Seeds, settings, outcomes & evidence')), body);
}

function createGame(game, index) {
  const runs = list(game.runs);
  const featured = runs.find(run => game.featured_run_id && run.id === game.featured_run_id) || runs[0];
  const article = node('article', { class: 'game-row', id: `game-${index + 1}`, 'aria-labelledby': `game-title-${index + 1}` });
  article.append(node('div', { class: 'game-main' },
    node('div', { class: 'game-info' },
      node('span', { class: 'game-number', 'aria-hidden': 'true' }, String(index + 1).padStart(2, '0')),
      node('h3', { class: 'game-title', id: `game-title-${index + 1}` }, game.title || game.id || `Environment ${index + 1}`),
      node('span', { class: 'game-env' }, game.environment || 'Environment pending'),
      node('span', { class: 'dimension-badge' }, `${setting(game.action_dimensions)} control dimension${game.action_dimensions === 1 ? '' : 's'}`),
      node('p', { class: 'game-description' }, game.description || '')),
    createMedia(game, featured), createResult(game, runs, featured)), createLedger(game, runs));
  return article;
}

function render(data) {
  if (!Array.isArray(data.games) || !data.games.length) throw new Error('No game records were found in results.json.');
  const runs = data.games.flatMap(game => list(game.runs));
  const dimensions = data.games.map(game => game.action_dimensions).filter(numeric);
  $('#games').replaceChildren(...data.games.map(createGame));
  $('#game-count').textContent = data.games.length;
  $('#run-count').textContent = runs.length;
  $('#action-count').textContent = dimensions.length ? `${Math.min(...dimensions)}–${Math.max(...dimensions)}` : '—';
  $('#model-name').textContent = data.model || 'Not supplied';
  $('#method-name').textContent = data.method || 'Multiway interval decoding';
  const updated = data.updated_at ? new Date(data.updated_at) : null;
  $('#updated-at').textContent = updated && !Number.isNaN(updated.getTime()) ? `${updated.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric', timeZone: 'UTC' })} · UTC` : 'Not yet published';
  $('#protocol-notes').replaceChildren(...list(data.protocol_notes).map(note => node('li', {}, note)));
  for (const [selector, value] of [['#source-url', data.source_url], ['#measurement-url', data.measurement_url], ['#configuration-url', data.configuration_url]]) {
    if (safeURL(value)) $(selector).href = safeURL(value);
  }
  if (data.config) {
    $('#experiment-config').hidden = false;
    $('#experiment-config pre').textContent = JSON.stringify(data.config, null, 2);
  }
  const ablations = list(data.racing_ablation);
  if (ablations.length) {
    $('#ablation').hidden = false;
    $('#ablation-results').replaceChildren(createRunTable(ablations, 'CarRacing branching and resolution comparison'));
  }
  const pending = data.games.some(game => !list(game.runs).length);
  const missingMedia = data.games.some(game => {
    const run = list(game.runs).find(item => game.featured_run_id && item.id === game.featured_run_id) || list(game.runs)[0];
    return !safeURL(run?.media?.video || game.media?.video);
  });
  const status = $('#load-status');
  status.hidden = !pending && !missingMedia;
  status.textContent = pending ? 'Development preview — some experiment results have not yet been supplied. Empty states are not measured outcomes.' : 'Some recordings have not yet been supplied. The available measurements are listed below.';
}

animateControl.addEventListener('change', () => mediaViews.forEach(update => update()));
motionPreference.addEventListener('change', event => {
  if (event.matches) { animateControl.checked = false; mediaViews.forEach(update => update()); }
});

try {
  const response = await fetch('results.json', { cache: 'no-cache' });
  if (!response.ok) throw new Error(`The measurement file returned HTTP ${response.status}.`);
  render(await response.json());
} catch (error) {
  const status = $('#load-status');
  status.hidden = false;
  status.classList.add('error');
  status.replaceChildren('Experiment data could not be loaded. ', link('Open the measurement file', 'results.json'), '.');
  console.error('NumericJev data load failed:', error);
}

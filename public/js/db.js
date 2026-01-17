/**
 * IndexedDB wrapper using Dexie.js
 * All data is stored locally in the browser.
 */

// Initialize Dexie database
const db = new Dexie('KnowThyTaste');

db.version(1).stores({
  movies: '++id, title, year, createdAt, lastAnalyzed',
  sessions: '++id, type, status, startTime, endTime',
  responses: '++id, sessionId, movieId, questionKey, createdAt',
  patterns: '++id, type, confidence, validated',
  settings: 'key'
});

// Movie operations
async function saveMovie(movie) {
  const now = new Date().toISOString();
  return await db.movies.add({
    title: movie.title,
    year: movie.year || null,
    genres: movie.genres || [],
    watchContext: movie.watchContext || null,
    posterPath: movie.posterPath || null,
    tmdbId: movie.tmdbId || null,
    createdAt: now,
    lastAnalyzed: null,
  });
}

async function getMovies() {
  return await db.movies.orderBy('createdAt').reverse().toArray();
}

async function getMovie(id) {
  return await db.movies.get(id);
}

async function updateMovie(id, updates) {
  return await db.movies.update(id, updates);
}

async function deleteMovie(id) {
  // Delete associated responses first
  await db.responses.where('movieId').equals(id).delete();
  return await db.movies.delete(id);
}

// Session operations
async function createSession(type, movieIds) {
  const now = new Date().toISOString();
  return await db.sessions.add({
    type: type,
    status: 'active',
    startTime: now,
    endTime: null,
    movieIds: movieIds,
    currentPhase: 'planning',
    currentQuestionIndex: 0,
  });
}

async function getSession(id) {
  return await db.sessions.get(id);
}

async function updateSession(id, updates) {
  return await db.sessions.update(id, updates);
}

async function completeSession(id) {
  const now = new Date().toISOString();
  return await db.sessions.update(id, {
    status: 'completed',
    endTime: now,
  });
}

async function getActiveSessions() {
  return await db.sessions.where('status').equals('active').toArray();
}

async function getCompletedSessionCount() {
  return await db.sessions.where('status').equals('completed').count();
}

// Response operations
async function saveResponse(response) {
  const now = new Date().toISOString();
  return await db.responses.add({
    sessionId: response.sessionId,
    movieId: response.movieId,
    questionKey: response.questionKey,
    questionText: response.questionText,
    responseText: response.responseText,
    confidence: response.confidence || null,
    isNewInsight: response.isNewInsight || false,
    specificityScore: response.specificityScore || null,
    createdAt: now,
  });
}

async function getResponsesForSession(sessionId) {
  return await db.responses.where('sessionId').equals(sessionId).toArray();
}

async function getResponsesForMovie(movieId) {
  return await db.responses.where('movieId').equals(movieId).toArray();
}

async function getAllResponses() {
  return await db.responses.toArray();
}

// Pattern operations
async function savePattern(pattern) {
  const now = new Date().toISOString();
  return await db.patterns.add({
    type: pattern.type,
    description: pattern.description,
    confidence: pattern.confidence,
    movieIds: pattern.movieIds,
    validated: null,
    firstDetected: now,
    // New fields for improved pattern detection
    element: pattern.element || null,
    sentiment: pattern.sentiment || 'neutral',
    contexts: pattern.contexts || [],
  });
}

async function getPatterns() {
  return await db.patterns.orderBy('confidence').reverse().toArray();
}

async function validatePattern(id, isValid) {
  return await db.patterns.update(id, { validated: isValid });
}

async function clearPatterns() {
  return await db.patterns.clear();
}

// Settings operations
async function getSetting(key, defaultValue = null) {
  const setting = await db.settings.get(key);
  return setting ? setting.value : defaultValue;
}

async function setSetting(key, value) {
  return await db.settings.put({ key, value });
}

// Export all data
async function exportAllData() {
  const data = {
    exportDate: new Date().toISOString(),
    version: 1,
    movies: await db.movies.toArray(),
    sessions: await db.sessions.toArray(),
    responses: await db.responses.toArray(),
    patterns: await db.patterns.toArray(),
    settings: await db.settings.toArray(),
  };
  return data;
}

// Import data
async function importData(data) {
  // Clear existing data
  await db.movies.clear();
  await db.sessions.clear();
  await db.responses.clear();
  await db.patterns.clear();
  await db.settings.clear();

  // Import new data
  if (data.movies) await db.movies.bulkAdd(data.movies);
  if (data.sessions) await db.sessions.bulkAdd(data.sessions);
  if (data.responses) await db.responses.bulkAdd(data.responses);
  if (data.patterns) await db.patterns.bulkAdd(data.patterns);
  if (data.settings) await db.settings.bulkAdd(data.settings);
}

// Clear all data
async function clearAllData() {
  await db.movies.clear();
  await db.sessions.clear();
  await db.responses.clear();
  await db.patterns.clear();
  await db.settings.clear();
}

// Stats
async function getStats() {
  const movieCount = await db.movies.count();
  const sessionCount = await db.sessions.where('status').equals('completed').count();
  const responseCount = await db.responses.count();
  const patternCount = await db.patterns.count();

  return {
    movies: movieCount,
    sessions: sessionCount,
    responses: responseCount,
    patterns: patternCount,
  };
}

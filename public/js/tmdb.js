/**
 * TMDB API integration for movie search and posters
 */

const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/';
const TMDB_API_BASE = 'https://api.themoviedb.org/3';

// Poster sizes: w92, w154, w185, w342, w500, w780, original
function getPosterUrl(posterPath, size = 'w185') {
  if (!posterPath) return null;
  return `${TMDB_IMAGE_BASE}${size}${posterPath}`;
}

async function getTmdbApiKey() {
  return await getSetting('tmdbApiKey', null);
}

async function setTmdbApiKey(key) {
  return await setSetting('tmdbApiKey', key);
}

async function searchMovies(query, year = null) {
  const apiKey = await getTmdbApiKey();
  if (!apiKey) {
    return { results: [], error: 'No TMDB API key configured' };
  }

  try {
    let url = `${TMDB_API_BASE}/search/movie?api_key=${apiKey}&query=${encodeURIComponent(query)}`;
    if (year) {
      url += `&year=${year}`;
    }

    const response = await fetch(url);
    if (!response.ok) {
      if (response.status === 401) {
        return { results: [], error: 'Invalid TMDB API key' };
      }
      throw new Error(`TMDB API error: ${response.status}`);
    }

    const data = await response.json();
    return {
      results: data.results.slice(0, 8).map(movie => ({
        tmdbId: movie.id,
        title: movie.title,
        year: movie.release_date ? parseInt(movie.release_date.split('-')[0]) : null,
        posterPath: movie.poster_path,
        posterUrl: getPosterUrl(movie.poster_path),
        overview: movie.overview,
      })),
      error: null
    };
  } catch (err) {
    console.error('TMDB search error:', err);
    return { results: [], error: 'Failed to search TMDB' };
  }
}

async function getMovieDetails(tmdbId) {
  const apiKey = await getTmdbApiKey();
  if (!apiKey) return null;

  try {
    const response = await fetch(`${TMDB_API_BASE}/movie/${tmdbId}?api_key=${apiKey}`);
    if (!response.ok) return null;

    const movie = await response.json();
    return {
      tmdbId: movie.id,
      title: movie.title,
      year: movie.release_date ? parseInt(movie.release_date.split('-')[0]) : null,
      posterPath: movie.poster_path,
      posterUrl: getPosterUrl(movie.poster_path),
      genres: movie.genres.map(g => g.name),
      overview: movie.overview,
      runtime: movie.runtime,
    };
  } catch (err) {
    console.error('TMDB details error:', err);
    return null;
  }
}

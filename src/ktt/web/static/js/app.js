/**
 * Main application logic for Know Thy Taste
 * Uses Alpine.js for reactivity
 */

// Global app state reference
let appState = null;

// Main app state
function app() {
  return {
    page: 'home',
    stats: { movies: 0, sessions: 0, responses: 0, patterns: 0 },
    movies: [],
    patterns: [],
    loading: true,

    async init() {
      appState = this;
      this.loading = true;
      await this.loadStats();
      await this.loadMovies();
      await this.loadPatterns();
      this.loading = false;
    },

    async loadStats() {
      this.stats = await getStats();
    },

    async loadMovies() {
      this.movies = await getMovies();
    },

    async loadPatterns() {
      this.patterns = await getPatterns();
    },

    async refreshAll() {
      await this.loadStats();
      await this.loadMovies();
      await this.loadPatterns();
    },
  };
}

// Add movie component
function addMovieForm() {
  return {
    title: '',
    year: '',
    watchContext: 'home',
    saving: false,
    error: null,

    async save() {
      if (!this.title.trim()) {
        this.error = 'Please enter a movie title';
        return;
      }

      this.saving = true;
      this.error = null;

      try {
        await saveMovie({
          title: this.title.trim(),
          year: this.year ? parseInt(this.year) : null,
          watchContext: this.watchContext,
        });

        // Reset form and go back
        this.title = '';
        this.year = '';
        this.watchContext = 'home';

        // Refresh and navigate
        await appState.refreshAll();
        appState.page = 'movies';
      } catch (err) {
        this.error = 'Failed to save movie';
        console.error(err);
      } finally {
        this.saving = false;
      }
    },
  };
}

// Session flow component
function sessionFlow() {
  return {
    step: 'select-type', // 'select-type', 'select-movie', 'questioning', 'complete'
    sessionType: null,
    selectedMovieId: null,
    selectedMovie: null,
    sessionId: null,
    questions: [],
    currentQuestionIndex: 0,
    currentPhase: null,
    response: '',
    followUpCount: 0,
    feedbackMessage: null,
    feedbackType: null, // 'success', 'warning', 'info'
    showConfidence: false,
    confidence: 3,
    metacognitivePrompt: null,
    sessionResponses: [],

    async selectType(type) {
      this.sessionType = type;
      this.step = 'select-movie';
    },

    async selectMovie(movieId) {
      this.selectedMovieId = movieId;
      this.selectedMovie = await getMovie(movieId);
      await this.startSession();
    },

    async startSession() {
      // Create session
      this.sessionId = await createSession(this.sessionType, [this.selectedMovieId]);

      // Get questions for session type
      this.questions = getQuestionsForSessionType(this.sessionType);
      this.currentQuestionIndex = 0;
      this.currentPhase = this.questions[0]?.phase || 'planning';
      this.sessionResponses = [];
      this.step = 'questioning';

      // Maybe show metacognitive prompt
      if (Math.random() < 0.3) {
        this.metacognitivePrompt = getRandomMetacognitivePrompt('beforeQuestion');
      }
    },

    get currentQuestion() {
      return this.questions[this.currentQuestionIndex];
    },

    get formattedQuestion() {
      if (!this.currentQuestion || !this.selectedMovie) return '';
      return formatQuestion(this.currentQuestion, this.selectedMovie.title);
    },

    get progress() {
      return Math.round((this.currentQuestionIndex / this.questions.length) * 100);
    },

    get phaseInfo() {
      return PHASE_INFO[this.currentPhase] || {};
    },

    async submitResponse() {
      const text = this.response.trim();
      if (!text) return;

      // Analyze response
      const analysis = analyzeResponse(text);

      // Check if we should ask for more detail
      if (!shouldAcceptResponse(analysis, this.followUpCount)) {
        const followUp = getFollowUp(analysis, this.followUpCount);
        this.feedbackMessage = followUp;
        this.feedbackType = 'warning';
        this.followUpCount++;
        return;
      }

      // Show encouragement or acceptance
      if (analysis.specificityScore >= 0.6) {
        this.feedbackMessage = getEncouragement();
        this.feedbackType = 'success';
      } else if (this.followUpCount > 0) {
        this.feedbackMessage = getAcceptanceMessage();
        this.feedbackType = 'info';
      }

      // Show confidence selector
      this.showConfidence = true;
    },

    async saveAndNext() {
      const text = this.response.trim();
      const analysis = analyzeResponse(text);

      // Save response
      await saveResponse({
        sessionId: this.sessionId,
        movieId: this.selectedMovieId,
        questionKey: this.currentQuestion.key,
        questionText: this.formattedQuestion,
        responseText: text,
        confidence: this.confidence,
        isNewInsight: false,
        specificityScore: analysis.specificityScore,
      });

      this.sessionResponses.push({
        question: this.formattedQuestion,
        response: text,
        confidence: this.confidence,
      });

      // Reset for next question
      this.response = '';
      this.followUpCount = 0;
      this.feedbackMessage = null;
      this.showConfidence = false;
      this.confidence = 3;
      this.metacognitivePrompt = null;

      // Move to next question
      this.currentQuestionIndex++;

      if (this.currentQuestionIndex >= this.questions.length) {
        await this.completeSession();
      } else {
        // Check for phase change
        const newPhase = this.currentQuestion.phase;
        if (newPhase !== this.currentPhase) {
          this.currentPhase = newPhase;
        }

        // Maybe show metacognitive prompt
        if (Math.random() < 0.2) {
          this.metacognitivePrompt = getRandomMetacognitivePrompt('beforeQuestion');
        }
      }
    },

    async completeSession() {
      await completeSession(this.sessionId);

      // Update movie's lastAnalyzed
      await updateMovie(this.selectedMovieId, {
        lastAnalyzed: new Date().toISOString(),
      });

      // Detect patterns
      const newPatterns = await detectPatterns();
      await clearPatterns();
      for (const p of newPatterns) {
        await savePattern(p);
      }

      this.step = 'complete';

      // Refresh app state
      await appState.refreshAll();
    },

    startNewSession() {
      this.step = 'select-type';
      this.sessionType = null;
      this.selectedMovieId = null;
      this.selectedMovie = null;
      this.sessionId = null;
      this.questions = [];
      this.currentQuestionIndex = 0;
      this.sessionResponses = [];
    },
  };
}

// Pattern validation component
function patternList() {
  return {
    async validate(patternId, isValid) {
      await validatePattern(patternId, isValid);
      await appState.loadPatterns();
    },
  };
}

// Settings/export component
function settingsPanel() {
  return {
    exporting: false,
    importing: false,
    importFile: null,
    message: null,
    messageType: null,

    async exportData() {
      this.exporting = true;
      try {
        const data = await exportAllData();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `know-thy-taste-backup-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
        this.message = 'Data exported successfully!';
        this.messageType = 'success';
      } catch (err) {
        this.message = 'Export failed';
        this.messageType = 'error';
        console.error(err);
      } finally {
        this.exporting = false;
      }
    },

    async handleImport(event) {
      const file = event.target.files[0];
      if (!file) return;

      this.importing = true;
      try {
        const text = await file.text();
        const data = JSON.parse(text);

        if (!data.movies || !data.sessions) {
          throw new Error('Invalid backup file');
        }

        await importData(data);
        await appState.refreshAll();

        this.message = 'Data imported successfully!';
        this.messageType = 'success';
      } catch (err) {
        this.message = 'Import failed: ' + err.message;
        this.messageType = 'error';
        console.error(err);
      } finally {
        this.importing = false;
        event.target.value = '';
      }
    },

    async clearData() {
      if (!confirm('This will delete ALL your data. This cannot be undone. Are you sure?')) {
        return;
      }
      if (!confirm('Really delete everything?')) {
        return;
      }

      await clearAllData();
      await appState.refreshAll();
      this.message = 'All data deleted';
      this.messageType = 'info';
    },
  };
}

// Delete movie handler
async function deleteMovieHandler(movieId) {
  if (!confirm('Delete this movie and all its responses?')) {
    return;
  }
  await deleteMovie(movieId);
}

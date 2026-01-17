/**
 * Analysis functions for Know Thy Taste
 * Anti-generic detection and pattern detection
 */

// Vague response patterns
const VAGUE_PATTERNS = [
  {
    pattern: /\bgood acting\b|\bgreat acting\b|\bacting was good\b/i,
    category: 'acting',
    followUps: [
      "Which actor specifically?",
      "Can you describe a moment where their performance stood out?",
      "What exactly were they doing that worked?",
      "How was their approach different from what you typically see?",
    ],
  },
  {
    pattern: /\binteresting\b(?! because)(?! in that)(?! how)/i,
    category: 'vague_positive',
    followUps: [
      "What made it interesting, specifically?",
      "Interesting compared to what?",
      "Can you point to the exact moment that felt interesting?",
      "Interesting in what way—surprising? Unusual? Thought-provoking?",
    ],
  },
  {
    pattern: /\bbeautiful cinematography\b|\bgreat cinematography\b|\bvisually stunning\b/i,
    category: 'cinematography',
    followUps: [
      "Can you describe one specific shot that struck you?",
      "Was it the framing, the lighting, the movement, or something else?",
      "What made it beautiful—the composition, colors, or mood?",
      "Close your eyes and describe one image from the film.",
    ],
  },
  {
    pattern: /\bgreat soundtrack\b|\bgood music\b|\bmusic was great\b|\bamazing score\b/i,
    category: 'music',
    followUps: [
      "Can you hum or describe a specific piece from the score?",
      "When in the film did the music most affect you?",
      "What did the music add that wouldn't be there without it?",
      "Was it the melody, the instruments, or how it interacted with the scene?",
    ],
  },
  {
    pattern: /\bwell written\b|\bgood writing\b|\bgreat dialogue\b/i,
    category: 'writing',
    followUps: [
      "Can you quote or paraphrase a line that stuck with you?",
      "What made the writing effective—naturalistic? Witty? Poetic?",
      "Was there a conversation or monologue that particularly worked?",
      "How would you describe the voice of this screenplay?",
    ],
  },
  {
    pattern: /\bi liked it\b|\bit was good\b|\treally enjoyed it\b/i,
    category: 'generic_positive',
    followUps: [
      "What specifically did you like about it?",
      "If you had to pick one element that made it work, what would it be?",
      "What kept you engaged?",
      "What would you tell a friend about why they should watch it?",
    ],
  },
  {
    pattern: /\bpowerful\b(?! because)|\bmoving\b(?! because)|\bemotional\b(?! because)/i,
    category: 'emotional_vague',
    followUps: [
      "What specifically made it powerful/moving?",
      "Which scene hit you the hardest?",
      "What were you feeling in that moment?",
      "Was it the content, the execution, or both?",
    ],
  },
  {
    pattern: /\brelatable\b|\brelateable\b/i,
    category: 'relatable',
    followUps: [
      "What specifically did you relate to?",
      "Was it a character, a situation, or a feeling?",
      "What from your own experience connected to this?",
      "Can you describe the moment you felt that connection?",
    ],
  },
];

const MIN_RESPONSE_LENGTH = 50;
const MAX_FOLLOWUP_ATTEMPTS = 3;

/**
 * Analyze a response for vagueness
 */
function analyzeResponse(response) {
  const text = response.trim();

  // Check for short responses
  if (text.length < MIN_RESPONSE_LENGTH) {
    return {
      isVague: true,
      vaguenessType: 'too_short',
      specificityScore: 0.2,
      followUps: [
        "Can you elaborate on that?",
        "Tell me more—what specifically do you mean?",
        "I'd like to understand this better. Can you expand?",
      ],
    };
  }

  // Check for vague patterns
  for (const pattern of VAGUE_PATTERNS) {
    if (pattern.pattern.test(text)) {
      return {
        isVague: true,
        vaguenessType: pattern.category,
        specificityScore: 0.3,
        followUps: pattern.followUps,
      };
    }
  }

  // Calculate specificity score
  const score = calculateSpecificityScore(text);

  if (score < 0.5) {
    return {
      isVague: true,
      vaguenessType: 'low_specificity',
      specificityScore: score,
      followUps: [
        "Can you be more specific? Describe a particular moment.",
        "Give me the details—what exactly happened in that scene?",
        "I want to see it through your eyes. Describe it like I haven't seen the film.",
      ],
    };
  }

  return {
    isVague: false,
    vaguenessType: null,
    specificityScore: score,
    followUps: [],
  };
}

/**
 * Calculate specificity score for a response (0-1)
 */
function calculateSpecificityScore(response) {
  let score = 0.5;

  // Positive indicators
  const positivePatterns = [
    [/\bwhen\b.*\b(was|were|did)\b/i, 0.08],
    [/\bthe scene where\b|\bin the scene\b/i, 0.12],
    [/\bspecifically\b|\bexactly\b|\bprecisely\b/i, 0.08],
    [/\bi remember\b|\bi recall\b/i, 0.08],
    [/\bthe moment\b|\bthat moment\b/i, 0.1],
    [/"[^"]{5,}?"/i, 0.12],  // Quoted dialogue
    [/\bfirst\b.*\bthen\b|\bafter\b.*\bbefore\b/i, 0.08],
    [/\b(face|eyes|hands|voice|expression)\b/i, 0.08],
    [/\b(shot|frame|cut|angle|camera)\b/i, 0.1],
    [/\b(lighting|color|shadow|contrast)\b/i, 0.08],
    [/\bbecause\b/i, 0.06],
    [/\bfor example\b|\bfor instance\b/i, 0.1],
  ];

  for (const [pattern, bonus] of positivePatterns) {
    if (pattern.test(response)) {
      score += bonus;
    }
  }

  // Negative indicators
  const negativePatterns = [
    [/\bkind of\b|\bsort of\b/i, -0.08],
    [/\bi guess\b|\bmaybe\b|\bprobably\b/i, -0.08],
    [/\bin general\b|\boverall\b|\bmostly\b/i, -0.1],
    [/\bjust\b.*\breally\b|\breally\b.*\bjust\b/i, -0.08],
    [/\bi don't know\b|\bi'm not sure\b/i, -0.1],
  ];

  for (const [pattern, penalty] of negativePatterns) {
    if (pattern.test(response)) {
      score += penalty;
    }
  }

  // Length bonus
  const wordCount = response.split(/\s+/).length;
  if (wordCount > 50) score += 0.1;
  if (wordCount > 100) score += 0.05;

  return Math.max(0, Math.min(1, score));
}

/**
 * Get follow-up question based on attempt number
 */
function getFollowUp(analysis, attemptNumber) {
  if (!analysis.followUps || analysis.followUps.length === 0) {
    return null;
  }
  const index = Math.min(attemptNumber, analysis.followUps.length - 1);
  return analysis.followUps[index];
}

/**
 * Should we accept the response despite vagueness?
 */
function shouldAcceptResponse(analysis, attemptCount) {
  if (!analysis.isVague) return true;
  if (attemptCount >= MAX_FOLLOWUP_ATTEMPTS) return true;
  if (analysis.specificityScore >= 0.4 && attemptCount >= 1) return true;
  return false;
}

/**
 * Extract elements mentioned in a response for pattern detection
 */
function extractElements(response) {
  const elements = [];
  const text = response.toLowerCase();

  // Technical elements
  const technicalPatterns = [
    [/\b(cinematography|lighting|framing|composition)\b/, 'visual'],
    [/\b(score|soundtrack|music|sound design)\b/, 'audio'],
    [/\b(editing|cuts?|pacing|rhythm)\b/, 'editing'],
    [/\b(dialogue|script|writing)\b/, 'writing'],
    [/\b(performance|acting|delivery)\b/, 'performance'],
    [/\b(color|palette|tone)\b/, 'color'],
  ];

  for (const [pattern, category] of technicalPatterns) {
    if (pattern.test(text)) {
      elements.push(category);
    }
  }

  // Thematic elements
  const thematicPatterns = [
    [/\b(loss|grief|mourning)\b/, 'theme:loss'],
    [/\b(love|romance|relationship)\b/, 'theme:love'],
    [/\b(isolation|loneliness|alone)\b/, 'theme:isolation'],
    [/\b(hope|redemption|healing)\b/, 'theme:hope'],
    [/\b(nostalgia|memory|past)\b/, 'theme:nostalgia'],
    [/\b(identity|self|who i am)\b/, 'theme:identity'],
    [/\b(family|parent|child)\b/, 'theme:family'],
    [/\b(mortality|death|dying)\b/, 'theme:mortality'],
  ];

  for (const [pattern, theme] of thematicPatterns) {
    if (pattern.test(text)) {
      elements.push(theme);
    }
  }

  return [...new Set(elements)];
}

/**
 * Detect patterns across all responses
 */
async function detectPatterns() {
  const responses = await getAllResponses();
  const movies = await getMovies();

  if (movies.length < 3) {
    return []; // Need at least 3 movies for pattern detection
  }

  // Count elements across movies
  const elementCounts = {};
  const elementMovies = {};

  for (const response of responses) {
    const elements = extractElements(response.responseText);
    for (const elem of elements) {
      elementCounts[elem] = (elementCounts[elem] || 0) + 1;
      if (!elementMovies[elem]) elementMovies[elem] = new Set();
      elementMovies[elem].add(response.movieId);
    }
  }

  // Find patterns (elements in multiple movies)
  const patterns = [];
  const totalMovies = movies.length;

  for (const [element, count] of Object.entries(elementCounts)) {
    const movieIds = [...elementMovies[element]];
    const movieCoverage = movieIds.length / totalMovies;

    if (movieIds.length >= 2 && movieCoverage >= 0.3) {
      const confidence = Math.min(0.95, movieCoverage * 0.7 + (count / responses.length) * 0.3);

      let type, description;
      if (element.startsWith('theme:')) {
        type = 'thematic';
        const theme = element.replace('theme:', '');
        description = `You consistently respond to themes of ${theme}`;
      } else if (['visual', 'color', 'lighting'].includes(element)) {
        type = 'visual';
        description = `You pay close attention to ${element} elements`;
      } else if (['audio', 'score', 'sound'].includes(element)) {
        type = 'auditory';
        description = `Sound and music significantly impact your experience`;
      } else if (['editing', 'pacing'].includes(element)) {
        type = 'structural';
        description = `You notice and value ${element} in storytelling`;
      } else if (['performance', 'acting'].includes(element)) {
        type = 'performance';
        description = `Strong performances are key to your enjoyment`;
      } else {
        type = 'general';
        description = `You frequently mention ${element} in your responses`;
      }

      patterns.push({
        type,
        description,
        confidence,
        movieIds,
        element,
      });
    }
  }

  // Sort by confidence
  patterns.sort((a, b) => b.confidence - a.confidence);

  return patterns.slice(0, 10);
}

// Encouragement messages
const ENCOURAGEMENT_MESSAGES = [
  "That's exactly the kind of detail that helps.",
  "Good—I can see that scene now.",
  "That specificity is valuable.",
  "This is helpful for understanding your taste.",
];

const ACCEPTANCE_MESSAGES = [
  "I'll note that as you've described it.",
  "Sometimes that's as specific as a feeling gets. Noted.",
  "Let's move on—we can always come back to this.",
];

function getEncouragement() {
  return ENCOURAGEMENT_MESSAGES[Math.floor(Math.random() * ENCOURAGEMENT_MESSAGES.length)];
}

function getAcceptanceMessage() {
  return ACCEPTANCE_MESSAGES[Math.floor(Math.random() * ACCEPTANCE_MESSAGES.length)];
}

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

// ============================================
// IMPROVED PATTERN DETECTION SYSTEM
// ============================================

// Sentiment indicators for positive/negative detection
const POSITIVE_INDICATORS = [
  /\bloved?\b/i, /\bamazing\b/i, /\bbeautiful\b/i, /\bbrilliant\b/i,
  /\bperfect\b/i, /\bstunning\b/i, /\bincredible\b/i, /\bpowerful\b/i,
  /\bmasterful\b/i, /\bcompelling\b/i, /\bcaptivat/i, /\bengag/i,
  /\bgripping\b/i, /\bmoved me\b/i, /\btouched me\b/i, /\bhit me\b/i,
  /\bstayed with me\b/i, /\bcan't stop thinking\b/i, /\bfavorite\b/i,
  /\beffective\b/i, /\bworked\b/i, /\bsucceeded\b/i, /\bnailed\b/i,
  /\belevated\b/i, /\benhanced\b/i, /\bstrengthened\b/i,
  /\breally (liked|enjoyed|appreciated)\b/i, /\bso good\b/i,
];

const NEGATIVE_INDICATORS = [
  /\bhated?\b/i, /\bawful\b/i, /\bterrible\b/i, /\bboring\b/i,
  /\bdull\b/i, /\bflat\b/i, /\bweak\b/i, /\bpoor\b/i,
  /\bdistracting\b/i, /\bjarring\b/i, /\boff-putting\b/i, /\bannoying\b/i,
  /\bfrustrat/i, /\bdisappoint/i, /\bconfus/i, /\blost me\b/i,
  /\btook me out\b/i, /\bpulled me out\b/i, /\bcouldn't connect\b/i,
  /\bfailed\b/i, /\bdidn't work\b/i, /\bfell flat\b/i, /\bmissed\b/i,
  /\boverdone\b/i, /\bover the top\b/i, /\btoo much\b/i, /\bnot enough\b/i,
  /\bwished\b.*\bdifferent/i, /\bshould have\b/i,
];

/**
 * Detect sentiment in a piece of text
 * Returns: 'positive', 'negative', 'mixed', or 'neutral'
 */
function detectSentiment(text) {
  let positiveCount = 0;
  let negativeCount = 0;

  for (const pattern of POSITIVE_INDICATORS) {
    if (pattern.test(text)) positiveCount++;
  }
  for (const pattern of NEGATIVE_INDICATORS) {
    if (pattern.test(text)) negativeCount++;
  }

  if (positiveCount > 0 && negativeCount > 0) return 'mixed';
  if (positiveCount > negativeCount) return 'positive';
  if (negativeCount > positiveCount) return 'negative';
  return 'neutral';
}

// Expanded element detection patterns
const ELEMENT_PATTERNS = {
  // Visual/Cinematography
  visual: {
    patterns: [
      /\bcinematograph/i, /\bvisual/i, /\bshot\b/i, /\bframe\b/i,
      /\bcamera\b/i, /\bangle\b/i, /\bcomposition\b/i, /\bframing\b/i,
      /\bwide shot\b/i, /\bclose[- ]?up\b/i, /\blong take\b/i,
      /\btracking shot\b/i, /\bsteadicam\b/i, /\bhandheld\b/i,
      /\blens\b/i, /\bfocus\b/i, /\bdepth of field\b/i,
    ],
    category: 'technical',
    label: 'cinematography',
  },
  lighting: {
    patterns: [
      /\blighting\b/i, /\blit\b/i, /\bshadow/i, /\bsilhouette/i,
      /\bcontrast\b/i, /\bdark\b/i, /\bbright\b/i, /\bglow\b/i,
      /\bneon\b/i, /\bnatural light\b/i, /\bchiaroscuro\b/i,
    ],
    category: 'technical',
    label: 'lighting',
  },
  color: {
    patterns: [
      /\bcolor\b/i, /\bcolour\b/i, /\bpalette\b/i, /\bhue\b/i,
      /\bsaturat/i, /\bdesaturat/i, /\bwarm\b/i, /\bcool\b/i,
      /\btone\b/i, /\bgrade\b/i, /\bgrading\b/i, /\bteal\b/i,
      /\borange\b/i, /\bred\b/i, /\bblue\b/i, /\bgolden\b/i,
      /\bmuted\b/i, /\bvibrant\b/i, /\bmonochrom/i,
    ],
    category: 'technical',
    label: 'color',
  },

  // Audio
  score: {
    patterns: [
      /\bscore\b/i, /\bsoundtrack\b/i, /\bmusic\b/i, /\bcomposer\b/i,
      /\btheme\b/i, /\bmotif\b/i, /\bleitmotif\b/i, /\borchestra/i,
      /\bsymphon/i, /\bmelody\b/i, /\bpiano\b/i, /\bstrings\b/i,
      /\bguitar\b/i, /\bsynth\b/i, /\belectronic\b/i,
    ],
    category: 'technical',
    label: 'score/music',
  },
  soundDesign: {
    patterns: [
      /\bsound design\b/i, /\bsound\b/i, /\baudio\b/i, /\bfoley\b/i,
      /\bsilence\b/i, /\bquiet\b/i, /\bloud\b/i, /\bambien/i,
      /\bsoundscape\b/i, /\bmix\b/i, /\becho\b/i, /\breverb\b/i,
    ],
    category: 'technical',
    label: 'sound design',
  },

  // Editing/Structure
  editing: {
    patterns: [
      /\bedit/i, /\bcut\b/i, /\bcutting\b/i, /\btransition/i,
      /\bmontage\b/i, /\bsequence\b/i, /\bjump cut\b/i, /\bsmash cut\b/i,
      /\bcross[- ]?cut/i, /\bintercut/i,
    ],
    category: 'technical',
    label: 'editing',
  },
  pacing: {
    patterns: [
      /\bpac(e|ing)\b/i, /\brhythm\b/i, /\bslow\b/i, /\bfast\b/i,
      /\bdeliberate\b/i, /\bmeditative\b/i, /\bbreathless\b/i,
      /\brelentless\b/i, /\btook its time\b/i, /\brushed\b/i,
      /\bdragged\b/i, /\blingered\b/i, /\bmomentum\b/i,
    ],
    category: 'structural',
    label: 'pacing',
  },
  structure: {
    patterns: [
      /\bstructure\b/i, /\bnarrative\b/i, /\bnonlinear\b/i, /\bflashback/i,
      /\bflash[- ]?forward/i, /\bframing device\b/i, /\bact\b/i,
      /\bsetup\b/i, /\bpayoff\b/i, /\btwist\b/i, /\breveal\b/i,
      /\bending\b/i, /\bopen[- ]?ended\b/i, /\bambiguous\b/i,
      /\bcliffhanger\b/i, /\bepilogue\b/i, /\bprologue\b/i,
    ],
    category: 'structural',
    label: 'narrative structure',
  },

  // Performance
  performance: {
    patterns: [
      /\bperforman/i, /\bacting\b/i, /\bactor\b/i, /\bactress\b/i,
      /\bdelivery\b/i, /\bportray/i, /\bembod/i, /\bcharisma/i,
      /\bpresence\b/i, /\bchemistry\b/i, /\bcast\b/i,
    ],
    category: 'performance',
    label: 'performances',
  },
  expression: {
    patterns: [
      /\bface\b/i, /\beyes\b/i, /\bexpression/i, /\blook\b/i,
      /\bglance\b/i, /\bstare\b/i, /\bgaze\b/i, /\bsmile\b/i,
      /\btears\b/i, /\bcrying\b/i, /\bsubtl/i, /\bnuanc/i,
      /\bgesture\b/i, /\bbody language\b/i,
    ],
    category: 'performance',
    label: 'facial expression/subtlety',
  },

  // Writing/Dialogue
  dialogue: {
    patterns: [
      /\bdialogue\b/i, /\bconversation\b/i, /\bline\b/i, /\bquote\b/i,
      /\bmonologue\b/i, /\bvoice[- ]?over\b/i, /\bnarrat/i,
      /\bwhat .+ said\b/i, /\bwhen .+ says\b/i,
    ],
    category: 'writing',
    label: 'dialogue',
  },
  writing: {
    patterns: [
      /\bwrit/i, /\bscript\b/i, /\bscreenplay\b/i, /\bstory\b/i,
      /\bplot\b/i, /\bcharacter\b/i, /\barc\b/i, /\bdevelopment\b/i,
      /\bmotivation\b/i, /\bsetup\b/i, /\bpayoff\b/i,
    ],
    category: 'writing',
    label: 'writing/story',
  },

  // Direction/Style
  direction: {
    patterns: [
      /\bdirect(or|ion|ed)\b/i, /\bfilmmaker\b/i, /\bauteur\b/i,
      /\bvision\b/i, /\bstyle\b/i, /\baesthetic\b/i, /\bapproach\b/i,
      /\bchoice\b/i, /\bdecision\b/i,
    ],
    category: 'technical',
    label: 'direction',
  },

  // Emotional responses
  tension: {
    patterns: [
      /\btension\b/i, /\bsuspense\b/i, /\banxious\b/i, /\banxiety\b/i,
      /\bedge of .+ seat\b/i, /\bheld .+ breath\b/i, /\bdread\b/i,
      /\buneasy\b/i, /\bunsettle/i, /\bnerve/i,
    ],
    category: 'emotional',
    label: 'tension/suspense',
  },
  catharsis: {
    patterns: [
      /\bcathar/i, /\brelease\b/i, /\bcried\b/i, /\btears\b/i,
      /\bweep/i, /\bsob\b/i, /\bemotional release\b/i, /\blet it out\b/i,
      /\bhit me hard\b/i, /\bgut[- ]?punch/i,
    ],
    category: 'emotional',
    label: 'emotional catharsis',
  },
  humor: {
    patterns: [
      /\bfunny\b/i, /\bhumor\b/i, /\bhumour\b/i, /\blaugh/i, /\bcomedy\b/i,
      /\bcomic\b/i, /\bwit\b/i, /\bwitty\b/i, /\bjoke\b/i, /\bhilarious\b/i,
    ],
    category: 'emotional',
    label: 'humor',
  },

  // Themes - expanded
  themeLoss: {
    patterns: [/\bloss\b/i, /\bgrief\b/i, /\bmourning\b/i, /\bbereavement\b/i, /\blosing\b/i],
    category: 'thematic',
    label: 'loss/grief',
  },
  themeLove: {
    patterns: [/\blove\b/i, /\bromance\b/i, /\brelationship\b/i, /\bintimacy\b/i, /\baffection\b/i],
    category: 'thematic',
    label: 'love/romance',
  },
  themeIsolation: {
    patterns: [/\bisolat/i, /\bloneli/i, /\balone\b/i, /\balienation\b/i, /\bdisconnect/i],
    category: 'thematic',
    label: 'isolation/loneliness',
  },
  themeHope: {
    patterns: [/\bhope\b/i, /\bredemption\b/i, /\bhealing\b/i, /\brecovery\b/i, /\bsecond chance\b/i],
    category: 'thematic',
    label: 'hope/redemption',
  },
  themeNostalgia: {
    patterns: [/\bnostalgi/i, /\bmemory\b/i, /\bpast\b/i, /\bchildhood\b/i, /\bremember/i],
    category: 'thematic',
    label: 'nostalgia/memory',
  },
  themeIdentity: {
    patterns: [/\bidentity\b/i, /\bself\b/i, /\bwho (i|they|we) (am|are|is)\b/i, /\bbecoming\b/i],
    category: 'thematic',
    label: 'identity/self',
  },
  themeFamily: {
    patterns: [/\bfamily\b/i, /\bparent/i, /\bmother\b/i, /\bfather\b/i, /\bchild/i, /\bsibling\b/i],
    category: 'thematic',
    label: 'family',
  },
  themeMortality: {
    patterns: [/\bmortality\b/i, /\bdeath\b/i, /\bdying\b/i, /\bend of life\b/i, /\bfacing death\b/i],
    category: 'thematic',
    label: 'mortality/death',
  },
  themePower: {
    patterns: [/\bpower\b/i, /\bcontrol\b/i, /\bcorrupt/i, /\bauthority\b/i, /\boppression\b/i],
    category: 'thematic',
    label: 'power/corruption',
  },
  themeTime: {
    patterns: [/\btime\b/i, /\bageing\b/i, /\baging\b/i, /\bpassage of time\b/i, /\byears\b/i],
    category: 'thematic',
    label: 'time/aging',
  },
  themeTruth: {
    patterns: [/\btruth\b/i, /\blie\b/i, /\bdeception\b/i, /\bhonest/i, /\bsecret\b/i, /\bbetrayal\b/i],
    category: 'thematic',
    label: 'truth/deception',
  },
  themeAmbition: {
    patterns: [/\bambition\b/i, /\bsuccess\b/i, /\bfailure\b/i, /\bdream\b/i, /\bgoal\b/i, /\bobsession\b/i],
    category: 'thematic',
    label: 'ambition/obsession',
  },

  // Viewing experience
  immersion: {
    patterns: [
      /\bimmersed\b/i, /\blost in\b/i, /\btransported\b/i, /\babsorbed\b/i,
      /\bengrossed\b/i, /\bforgot\b.*\bwatching\b/i, /\bdisappeared\b/i,
    ],
    category: 'experience',
    label: 'immersion',
  },
  rewatch: {
    patterns: [
      /\brewatch/i, /\bwatch again\b/i, /\bsee again\b/i, /\bsecond viewing\b/i,
      /\bevery time i watch\b/i, /\bgets better\b/i, /\bnew detail/i,
    ],
    category: 'experience',
    label: 'rewatchability',
  },
};

// Higher-level preference patterns (detected from multiple signals)
const PREFERENCE_PATTERNS = {
  slowPacing: {
    signals: [
      /\bslow\b.*\b(loved?|appreciate|enjoy|perfect|beautiful)\b/i,
      /\b(loved?|appreciate|enjoy)\b.*\bslow\b/i,
      /\btook its time\b.*\b(loved?|worked|effective)\b/i,
      /\bdeliberate\b.*\b(pace|pacing)\b/i,
      /\bmeditative\b/i,
      /\b(breath|room)\b.*\b(space|moment)\b/i,
      /\blet .+ (linger|breathe|sit)\b/i,
    ],
    antiSignals: [
      /\btoo slow\b/i, /\bdragged\b/i, /\bboring\b/i,
    ],
    description: 'You appreciate deliberate, slow-burn pacing that lets moments breathe',
  },
  fastPacing: {
    signals: [
      /\b(fast|quick|brisk)\b.*\b(pace|pacing)\b.*\b(loved?|great|perfect)\b/i,
      /\bbreathless\b/i, /\brelentless\b/i, /\bkinetic\b/i,
      /\b(never|didn't)\b.*\bslow down\b/i, /\bmomentum\b/i,
    ],
    antiSignals: [
      /\brushed\b/i, /\btoo fast\b/i, /\bexhausting\b/i,
    ],
    description: 'You enjoy fast, propulsive pacing that maintains momentum',
  },
  ambiguousEndings: {
    signals: [
      /\bambiguous\b.*\b(end|ending)\b.*\b(loved?|perfect|appreciate)\b/i,
      /\b(loved?|appreciate)\b.*\b(open|ambiguous)\b.*\bend/i,
      /\bleft .+ (thinking|wondering|interpreting)\b/i,
      /\bdoesn't spell it out\b/i, /\btrusts the audience\b/i,
    ],
    antiSignals: [
      /\bwanted answers\b/i, /\bfrustrating\b.*\bending\b/i,
    ],
    description: 'You value ambiguous endings that leave room for interpretation',
  },
  visualStorytelling: {
    signals: [
      /\bshow\b.*\bnot\b.*\btell\b/i, /\bvisual storytelling\b/i,
      /\bwithout dialogue\b/i, /\bwithout words\b/i,
      /\bsilent\b.*\b(powerful|effective|beautiful)\b/i,
      /\bimages\b.*\b(speak|convey|tell)\b/i,
    ],
    antiSignals: [],
    description: 'You respond strongly to visual storytelling over dialogue',
  },
  subtlety: {
    signals: [
      /\bsubtl/i, /\brestrained\b/i, /\bunderstat/i,
      /\bnot\b.*\bover\b.*\btop\b/i, /\bquiet\b.*\bmoment/i,
      /\bless is more\b/i, /\bheld back\b/i,
    ],
    antiSignals: [],
    description: 'You appreciate subtlety and restraint over dramatic excess',
  },
  emotionalIntensity: {
    signals: [
      /\b(intense|intensity)\b.*\b(emotion|feeling)\b/i,
      /\bgut[- ]?punch/i, /\bdevastating\b/i, /\bwrecked me\b/i,
      /\bcouldn't stop crying\b/i, /\bhit me hard\b/i,
    ],
    antiSignals: [
      /\btoo intense\b/i, /\bmanipulative\b/i,
    ],
    description: 'You seek out and appreciate emotionally intense experiences',
  },
  worldBuilding: {
    signals: [
      /\bworld[- ]?building\b/i, /\bimmersive\b.*\bworld\b/i,
      /\blived[- ]?in\b/i, /\bfully realized\b/i,
      /\bdetail\b.*\bworld\b/i, /\bbelievable\b.*\buniverse\b/i,
    ],
    antiSignals: [],
    description: 'You value rich, detailed world-building that creates immersive environments',
  },
  practicalEffects: {
    signals: [
      /\bpractical effects?\b/i, /\breal\b.*\b(stunts?|effects?)\b/i,
      /\bnot CGI\b/i, /\bin[- ]?camera\b/i, /\btangible\b/i,
    ],
    antiSignals: [],
    description: 'You have a strong appreciation for practical effects over digital',
  },
};

/**
 * Extract elements mentioned in a response with sentiment
 */
function extractElements(response) {
  const elements = [];
  const text = response.toLowerCase();
  const sentiment = detectSentiment(response);

  // Check each element pattern category
  for (const [key, config] of Object.entries(ELEMENT_PATTERNS)) {
    for (const pattern of config.patterns) {
      if (pattern.test(text)) {
        // Find context around the match (for quotes later)
        const match = text.match(pattern);
        let context = '';
        if (match) {
          const startIndex = Math.max(0, match.index - 50);
          const endIndex = Math.min(text.length, match.index + match[0].length + 50);
          context = response.substring(startIndex, endIndex).trim();
        }

        elements.push({
          key,
          label: config.label,
          category: config.category,
          sentiment: detectLocalSentiment(response, match?.index || 0),
          context,
        });
        break; // Only count each element type once per response
      }
    }
  }

  return elements;
}

/**
 * Detect sentiment in a local area around a match
 */
function detectLocalSentiment(text, matchIndex) {
  // Get surrounding context (100 chars each direction)
  const start = Math.max(0, matchIndex - 100);
  const end = Math.min(text.length, matchIndex + 100);
  const localText = text.substring(start, end);

  return detectSentiment(localText);
}

/**
 * Detect higher-level preference patterns
 */
function detectPreferencePatterns(responses) {
  const detected = [];

  for (const [key, config] of Object.entries(PREFERENCE_PATTERNS)) {
    let signalCount = 0;
    let antiSignalCount = 0;
    const matchingResponses = [];

    for (const response of responses) {
      const text = response.responseText;

      for (const pattern of config.signals) {
        if (pattern.test(text)) {
          signalCount++;
          matchingResponses.push(response);
          break;
        }
      }

      for (const pattern of config.antiSignals) {
        if (pattern.test(text)) {
          antiSignalCount++;
          break;
        }
      }
    }

    // Only include if signals significantly outweigh anti-signals
    if (signalCount >= 2 && signalCount > antiSignalCount * 2) {
      detected.push({
        key,
        description: config.description,
        strength: signalCount,
        matchingResponses,
      });
    }
  }

  return detected;
}

/**
 * Detect patterns across all responses - IMPROVED VERSION
 */
async function detectPatterns() {
  const responses = await getAllResponses();
  const movies = await getMovies();
  const existingPatterns = await getPatterns();

  if (movies.length < 2) {
    return []; // Need at least 2 movies for pattern detection
  }

  // Track rejected patterns (validated === false)
  const rejectedPatternKeys = new Set(
    existingPatterns
      .filter(p => p.validated === false)
      .map(p => p.element || p.key)
  );

  // Track confirmed patterns (validated === true) - boost their confidence
  const confirmedPatternKeys = new Set(
    existingPatterns
      .filter(p => p.validated === true)
      .map(p => p.element || p.key)
  );

  // Count elements across movies with sentiment
  const elementData = {};

  for (const response of responses) {
    const elements = extractElements(response.responseText);

    for (const elem of elements) {
      const key = elem.key;

      if (!elementData[key]) {
        elementData[key] = {
          label: elem.label,
          category: elem.category,
          movieIds: new Set(),
          positiveCount: 0,
          negativeCount: 0,
          neutralCount: 0,
          contexts: [],
        };
      }

      elementData[key].movieIds.add(response.movieId);

      if (elem.sentiment === 'positive') elementData[key].positiveCount++;
      else if (elem.sentiment === 'negative') elementData[key].negativeCount++;
      else elementData[key].neutralCount++;

      if (elem.context && elementData[key].contexts.length < 3) {
        elementData[key].contexts.push(elem.context);
      }
    }
  }

  // Build patterns from element data
  const patterns = [];
  const totalMovies = movies.length;

  for (const [key, data] of Object.entries(elementData)) {
    // Skip if user rejected this pattern before
    if (rejectedPatternKeys.has(key)) continue;

    const movieIds = [...data.movieIds];
    const movieCoverage = movieIds.length / totalMovies;
    const totalMentions = data.positiveCount + data.negativeCount + data.neutralCount;

    // Need to appear in at least 2 movies or 30% of movies
    if (movieIds.length < 2 && movieCoverage < 0.3) continue;

    // Determine dominant sentiment
    let sentiment = 'neutral';
    if (data.positiveCount > data.negativeCount && data.positiveCount > data.neutralCount) {
      sentiment = 'positive';
    } else if (data.negativeCount > data.positiveCount && data.negativeCount > data.neutralCount) {
      sentiment = 'negative';
    }

    // Calculate confidence
    let confidence = Math.min(0.95, movieCoverage * 0.5 + (totalMentions / responses.length) * 0.3 + 0.2);

    // Boost confidence for confirmed patterns
    if (confirmedPatternKeys.has(key)) {
      confidence = Math.min(0.98, confidence + 0.15);
    }

    // Generate description based on sentiment
    const description = generatePatternDescription(data.label, sentiment, data.category, data.contexts);

    patterns.push({
      type: data.category,
      element: key,
      description,
      confidence,
      sentiment,
      movieIds,
      contexts: data.contexts,
    });
  }

  // Add higher-level preference patterns
  const preferencePatterns = detectPreferencePatterns(responses);

  for (const pref of preferencePatterns) {
    // Skip if rejected
    if (rejectedPatternKeys.has(pref.key)) continue;

    let confidence = Math.min(0.9, 0.5 + pref.strength * 0.1);

    // Boost if confirmed
    if (confirmedPatternKeys.has(pref.key)) {
      confidence = Math.min(0.98, confidence + 0.15);
    }

    patterns.push({
      type: 'preference',
      element: pref.key,
      description: pref.description,
      confidence,
      sentiment: 'positive',
      movieIds: [...new Set(pref.matchingResponses.map(r => r.movieId))],
    });
  }

  // Sort by confidence
  patterns.sort((a, b) => b.confidence - a.confidence);

  return patterns.slice(0, 12);
}

/**
 * Generate a natural-sounding pattern description
 */
function generatePatternDescription(label, sentiment, category, contexts) {
  // Get a relevant quote if available
  let quote = '';
  if (contexts && contexts.length > 0) {
    // Find the shortest, most coherent context
    const bestContext = contexts
      .filter(c => c.length > 20 && c.length < 100)
      .sort((a, b) => a.length - b.length)[0];

    if (bestContext) {
      quote = ` ("${bestContext.trim()}...")`;
    }
  }

  // Generate description based on sentiment
  if (sentiment === 'positive') {
    const templates = [
      `You consistently appreciate strong ${label}`,
      `${label.charAt(0).toUpperCase() + label.slice(1)} is something you notice and value`,
      `You respond positively to thoughtful ${label}`,
      `Good ${label} significantly enhances your experience`,
    ];
    return templates[Math.floor(Math.random() * templates.length)];
  } else if (sentiment === 'negative') {
    const templates = [
      `You're sensitive to weak or poor ${label}`,
      `${label.charAt(0).toUpperCase() + label.slice(1)} issues tend to bother you`,
      `You notice when ${label} doesn't work`,
    ];
    return templates[Math.floor(Math.random() * templates.length)];
  } else {
    const templates = [
      `You pay attention to ${label}`,
      `${label.charAt(0).toUpperCase() + label.slice(1)} is something you notice`,
      `You're aware of ${label} in the films you watch`,
    ];
    return templates[Math.floor(Math.random() * templates.length)];
  }
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

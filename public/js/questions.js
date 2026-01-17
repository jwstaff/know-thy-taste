/**
 * Question bank for Know Thy Taste
 * Questions organized by phase: Planning, Monitoring, Evaluation
 */

const QUESTIONS = {
  planning: [
    {
      key: 'first_memory',
      text: "Before we analyze this film, what's the first specific moment or scene that comes to mind when you think of {movie}?",
      phase: 'planning',
      category: 'sensory',
      hint: "Try to recall a specific image, sound, or moment—not the plot summary.",
      exampleGood: "The scene where she walks into the empty apartment and just stands there, looking at the dust floating in the light from the window.",
    },
    {
      key: 'expectations',
      text: "What were you hoping for or expecting when you started watching {movie}?",
      phase: 'planning',
      category: 'emotional',
      hint: "Think about what drew you to watch it, what you anticipated.",
    },
    {
      key: 'attention_focus',
      text: "Can you identify one specific element you found yourself paying attention to while watching?",
      phase: 'planning',
      category: 'sensory',
      hint: "Was it the dialogue? The faces? The colors? The music? What kept catching your eye or ear?",
    },
    {
      key: 'initial_feeling',
      text: "What did you feel immediately after the film ended, before you had time to think about it?",
      phase: 'planning',
      category: 'emotional',
      hint: "Not what you think about it now—what was the raw, immediate feeling?",
    },
    {
      key: 'watch_context',
      text: "Where and how did you watch {movie}? Were you alone? What was your state of mind?",
      phase: 'planning',
      category: 'thematic',
      hint: "Context shapes experience. Theater vs. laptop, alone vs. with someone, tired vs. alert.",
    },
  ],
  monitoring: [
    {
      key: 'attention_captured',
      text: "Think about a moment when your attention was most completely captured. What was happening in that exact scene?",
      phase: 'monitoring',
      category: 'sensory',
      hint: "Describe it like you're setting up the scene for someone who hasn't seen it.",
      exampleGood: "When the camera slowly pushed in on his face as he read the letter, and you could see his expression shift from confusion to devastation—no dialogue, just that face.",
    },
    {
      key: 'disconnection',
      text: "Were there points where you felt disconnected or your mind wandered? What was happening when that occurred?",
      phase: 'monitoring',
      category: 'emotional',
      hint: "It's valuable to identify what doesn't work for you too.",
    },
    {
      key: 'predictions',
      text: "Did you notice yourself making predictions about what would happen? Were they right?",
      phase: 'monitoring',
      category: 'narrative',
      hint: "We're constantly predicting. What did you expect, and how did the film respond?",
    },
    {
      key: 'comparisons',
      text: "While watching, did you find yourself comparing this to other films, books, or experiences? To what?",
      phase: 'monitoring',
      category: 'thematic',
      hint: "These automatic comparisons reveal your mental library and what patterns you recognize.",
    },
    {
      key: 'physical_response',
      text: "Did you have any physical responses? Tension, tears, laughter, leaning forward, looking away?",
      phase: 'monitoring',
      category: 'emotional',
      hint: "Our bodies often respond before our minds catch up. What did yours do?",
    },
    {
      key: 'rewatch_impulse',
      text: "Were there moments you wanted to rewind or see again? Which ones?",
      phase: 'monitoring',
      category: 'sensory',
      hint: "The urge to revisit something immediately is a strong signal.",
    },
    {
      key: 'time_perception',
      text: "How did time feel during the film? Did it fly by, drag, or did certain sections feel different?",
      phase: 'monitoring',
      category: 'narrative',
      hint: "Time perception reveals engagement. When did the film earn your full presence?",
    },
  ],
  evaluation: [
    {
      key: 'emotional_impact',
      text: "Looking back, what element had the most emotional impact on you—and what specifically about it?",
      phase: 'evaluation',
      category: 'emotional',
      hint: "'The score' is too vague. Which part of the score? What did it do?",
      exampleGood: "The recurring piano motif that played during her memories. The first few times it felt nostalgic, but by the end, when it played over her empty chair, it felt like loss.",
    },
    {
      key: 'removal_test',
      text: "If you removed one element (the score, the cinematography, the dialogue style, the lead performance), would your experience be fundamentally different? Which one?",
      phase: 'evaluation',
      category: 'technical',
      hint: "This reveals what you consider essential to the film's effect.",
    },
    {
      key: 'self_reflection',
      text: "What does your reaction to this film tell you about what you value in storytelling?",
      phase: 'evaluation',
      category: 'thematic',
      hint: "Step back. What does loving (or not loving) this film say about you?",
    },
    {
      key: 'lasting_image',
      text: "What image or moment do you think will stay with you longest? Why that one?",
      phase: 'evaluation',
      category: 'sensory',
      hint: "Of everything in the film, what has lodged itself in your memory?",
    },
    {
      key: 'recommendation',
      text: "If you were to recommend this film to someone, what kind of person would appreciate it most? Why?",
      phase: 'evaluation',
      category: 'thematic',
      hint: "Imagining the ideal audience reveals what you think the film offers.",
    },
    {
      key: 'changed_view',
      text: "Did this film change how you think about anything—films, life, a topic it addressed?",
      phase: 'evaluation',
      category: 'thematic',
      hint: "Films can shift perspectives. Did this one move anything in you?",
    },
    {
      key: 'craft_appreciation',
      text: "Is there a specific craft element (editing, sound design, production design, etc.) that you noticed more than usual?",
      phase: 'evaluation',
      category: 'technical',
      hint: "Sometimes a film teaches us to see filmmaking differently.",
    },
    {
      key: 'narrative_structure',
      text: "How did the structure of the story affect your experience? Did the way it was told enhance or diminish the material?",
      phase: 'evaluation',
      category: 'narrative',
      hint: "Not just what happened, but how it was revealed to you.",
    },
  ],
};

const PHASE_INFO = {
  planning: {
    name: 'Planning / Awareness',
    description: "Let's start by noticing what stayed with you from this film.",
  },
  monitoring: {
    name: 'Monitoring / Engagement',
    description: "Now let's explore how you engaged with the film while watching.",
  },
  evaluation: {
    name: 'Evaluation / Meaning',
    description: "Finally, let's reflect on what this film means to you.",
  },
};

const METACOGNITIVE_PROMPTS = {
  beforeQuestion: [
    "Before answering, pause for a moment. What comes to mind first?",
    "How are you feeling about analyzing this film? Excited? Resistant? Neutral?",
    "What strategy are you using to recall these details? Replaying scenes? Remembering feelings?",
  ],
  afterResponse: [
    "Was that something you've thought about before, or did articulating it reveal something new?",
    "How confident are you in that response? Solid ground or still exploring?",
    "Are you describing what you actually experienced, or what you think you should have experienced?",
  ],
  sessionEnd: [
    "What did you learn about your taste from this session?",
    "Was anything surprising in what you discovered?",
    "How do you feel about this depth of analysis? Energizing? Exhausting? Illuminating?",
  ],
};

const CONFIDENCE_SCALE = {
  1: "Just guessing—not sure at all",
  2: "Uncertain—might change my mind",
  3: "Moderate—seems right but I'm open",
  4: "Confident—this feels solid",
  5: "Very confident—I know this about myself",
};

function getQuestionsForPhase(phase) {
  return QUESTIONS[phase] || [];
}

function formatQuestion(question, movieTitle) {
  return question.text.replace('{movie}', movieTitle);
}

function getQuestionsForSessionType(sessionType) {
  if (sessionType === 'deep-dive') {
    return [
      ...QUESTIONS.planning.slice(0, 3),
      ...QUESTIONS.monitoring.slice(0, 4),
      ...QUESTIONS.evaluation.slice(0, 4),
    ];
  } else if (sessionType === 'pattern-hunt') {
    return [
      ...QUESTIONS.monitoring.filter(q =>
        q.text.toLowerCase().includes('compar') ||
        q.text.toLowerCase().includes('different')
      ),
      ...QUESTIONS.evaluation.filter(q =>
        q.text.toLowerCase().includes('remov') ||
        q.text.toLowerCase().includes('element')
      ),
    ].slice(0, 6);
  } else if (sessionType === 'temporal') {
    return QUESTIONS.evaluation.filter(q =>
      q.text.toLowerCase().includes('change') ||
      q.text.toLowerCase().includes('last') ||
      q.text.toLowerCase().includes('stay')
    ).slice(0, 4);
  }
  // Default balanced selection
  return [
    ...QUESTIONS.planning.slice(0, 2),
    ...QUESTIONS.monitoring.slice(0, 3),
    ...QUESTIONS.evaluation.slice(0, 3),
  ];
}

function getRandomMetacognitivePrompt(timing) {
  const prompts = METACOGNITIVE_PROMPTS[timing];
  if (!prompts || prompts.length === 0) return null;
  return prompts[Math.floor(Math.random() * prompts.length)];
}

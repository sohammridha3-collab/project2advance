import os

svgs = {
    'easy_walking.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0b1528"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
    <linearGradient id="tealGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00d4aa"/>
      <stop offset="100%" stop-color="#38bdf8"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg1)" stroke="rgba(56,189,248,0.2)" stroke-width="1.5"/>
  <circle cx="160" cy="90" r="65" fill="rgba(0,212,170,0.06)"/>
  <!-- Path -->
  <path d="M40 148 Q160 142 280 148" stroke="rgba(148,163,184,0.3)" stroke-width="2" stroke-dasharray="4 4" fill="none"/>
  <!-- Figure: Walking -->
  <circle cx="145" cy="52" r="10" fill="#00d4aa"/>
  <path d="M145 64 L148 98 L162 135 M148 98 L130 138" stroke="url(#tealGrad)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <path d="M146 75 L168 90 L174 105 M146 75 L128 88 L122 100" stroke="#38bdf8" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <!-- Motion waves -->
  <path d="M185 85 C192 88 192 94 185 97" stroke="#00d4aa" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.6"/>
  <path d="M193 80 C203 86 203 96 193 102" stroke="#00d4aa" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.3"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#38bdf8" letter-spacing="0.5">EASY PACED WALKING</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Low Impact - Light Aerobic Pace</text>
</svg>''',

    'gentle_stretching.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0e172a"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
    <linearGradient id="purpGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#818cf8"/>
      <stop offset="100%" stop-color="#c084fc"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg2)" stroke="rgba(129,140,248,0.2)" stroke-width="1.5"/>
  <circle cx="160" cy="85" r="60" fill="rgba(129,140,248,0.06)"/>
  <!-- Figure: Standing stretch with arms up -->
  <circle cx="160" cy="44" r="10" fill="#818cf8"/>
  <path d="M160 56 L160 102 L148 144 M160 102 L172 144" stroke="url(#purpGrad)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <path d="M160 68 L142 42 L146 28 M160 68 L178 42 L174 28" stroke="#a855f7" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <!-- Stretch arc -->
  <path d="M136 28 Q160 18 184 28" stroke="#818cf8" stroke-width="2" stroke-dasharray="3 3" fill="none"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#a855f7" letter-spacing="0.5">GENTLE STRETCHING</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Mobility - Relieves Muscle Tightness</text>
</svg>''',

    'chair_sit_stand.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg3" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#061824"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg3)" stroke="rgba(20,184,166,0.2)" stroke-width="1.5"/>
  <!-- Chair -->
  <path d="M185 85 L185 142 M152 112 L185 112 M152 112 L152 142" stroke="rgba(148,163,184,0.6)" stroke-width="3.5" stroke-linecap="round" fill="none"/>
  <!-- Figure: rising from chair -->
  <circle cx="140" cy="54" r="10" fill="#14b8a6"/>
  <path d="M140 66 L148 100 L166 112 L166 142 M148 100 L142 142" stroke="#2dd4bf" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <path d="M143 78 L125 94 L132 108" stroke="#5eead4" stroke-width="3" stroke-linecap="round" fill="none"/>
  <!-- Motion arrows up -->
  <path d="M118 90 L118 62 M112 70 L118 60 L124 70" stroke="#14b8a6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#14b8a6" letter-spacing="0.5">CHAIR SIT-TO-STAND</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Leg Strength - Joint-Friendly Baseline</text>
</svg>''',

    'deep_breathing.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg4" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#081e28"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg4)" stroke="rgba(56,189,248,0.2)" stroke-width="1.5"/>
  <!-- Concentric breathing pulse rings -->
  <circle cx="160" cy="85" r="55" fill="none" stroke="rgba(56,189,248,0.15)" stroke-width="2" stroke-dasharray="6 4"/>
  <circle cx="160" cy="85" r="40" fill="none" stroke="rgba(56,189,248,0.25)" stroke-width="1.5"/>
  <!-- Figure: seated meditation/breathing -->
  <circle cx="160" cy="56" r="9" fill="#38bdf8"/>
  <path d="M160 67 L160 106 L140 125 L180 125 Z" fill="rgba(56,189,248,0.2)" stroke="#38bdf8" stroke-width="3" stroke-linejoin="round"/>
  <path d="M160 76 L142 94 L152 108 M160 76 L178 94 L168 108" stroke="#7dd3fc" stroke-width="3" stroke-linecap="round" fill="none"/>
  <!-- Lungs icon accent -->
  <path d="M154 84 C150 82 146 86 146 91 C146 96 150 98 154 96 M166 84 C170 82 174 86 174 91 C174 96 170 98 166 96" stroke="#00d4aa" stroke-width="1.8" fill="none" stroke-linecap="round"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#38bdf8" letter-spacing="0.5">BREATHING &amp; MOBILITY</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Stress Relief - Calms Blood Pressure</text>
</svg>''',

    'brisk_walking.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg5" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#08202d"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg5)" stroke="rgba(14,165,233,0.3)" stroke-width="1.5"/>
  <!-- Figure: brisk walking with active arms -->
  <circle cx="145" cy="46" r="10" fill="#0284c7"/>
  <path d="M145 58 L152 94 L176 136 M152 94 L126 134" stroke="#38bdf8" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <path d="M148 70 L174 82 L186 74 M148 70 L124 88 L114 102" stroke="#0ea5e9" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <!-- Speed lines -->
  <path d="M88 78 L104 78 M80 90 L100 90 M84 102 L106 102" stroke="rgba(56,189,248,0.5)" stroke-width="2" stroke-linecap="round"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#0ea5e9" letter-spacing="0.5">BRISK INTERVAL WALKING</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Moderate Aerobic - Heart Conditioning</text>
</svg>''',

    'bodyweight_squats.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg6" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#181829"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg6)" stroke="rgba(234,179,8,0.2)" stroke-width="1.5"/>
  <!-- Figure in squat pose -->
  <circle cx="140" cy="56" r="10" fill="#eab308"/>
  <path d="M140 68 L146 102 L172 108 L170 142 M146 102 L124 116 L130 142" stroke="#facc15" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <path d="M142 80 L174 80 L188 88" stroke="#fef08a" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <!-- Depth guide curve -->
  <path d="M185 108 Q195 125 185 142" stroke="rgba(234,179,8,0.4)" stroke-width="2" stroke-dasharray="3 3" fill="none"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#eab308" letter-spacing="0.5">BODYWEIGHT SQUATS</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Lower Body Strength - Functional Mobility</text>
</svg>''',

    'wall_pushups.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg7" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0c1e2c"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg7)" stroke="rgba(16,185,129,0.2)" stroke-width="1.5"/>
  <!-- Wall -->
  <line x1="220" y1="35" x2="220" y2="150" stroke="rgba(148,163,184,0.7)" stroke-width="4" stroke-linecap="round"/>
  <!-- Figure: incline wall push up -->
  <circle cx="152" cy="50" r="10" fill="#10b981"/>
  <path d="M152 62 L132 108 L114 144" stroke="#34d399" stroke-width="4" stroke-linecap="round" fill="none"/>
  <path d="M146 76 L185 76 L218 80" stroke="#6ee7b7" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#10b981" letter-spacing="0.5">WALL PUSH-UPS</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Chest &amp; Arms - Gentle Shoulder Impact</text>
</svg>''',

    'resistance_band.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg8" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#181428"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg8)" stroke="rgba(168,85,247,0.2)" stroke-width="1.5"/>
  <!-- Figure holding band -->
  <circle cx="160" cy="46" r="10" fill="#a855f7"/>
  <path d="M160 58 L160 105 L150 144 M160 105 L170 144" stroke="#c084fc" stroke-width="4" stroke-linecap="round" fill="none"/>
  <path d="M160 72 L128 78 L114 82 M160 72 L192 78 L206 82" stroke="#e9d5ff" stroke-width="3.5" stroke-linecap="round" fill="none"/>
  <!-- Elastic Band stretched taut -->
  <path d="M114 82 Q160 86 206 82" stroke="#ec4899" stroke-width="3" stroke-linecap="round" fill="none"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#c084fc" letter-spacing="0.5">RESISTANCE BAND PULLS</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Upper Back &amp; Posture - Controlled Tension</text>
</svg>''',

    'glute_bridge.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg9" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#081c24"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg9)" stroke="rgba(20,184,166,0.2)" stroke-width="1.5"/>
  <!-- Exercise Mat -->
  <line x1="50" y1="145" x2="270" y2="145" stroke="rgba(148,163,184,0.4)" stroke-width="3" stroke-linecap="round"/>
  <!-- Figure: glute bridge elevated -->
  <circle cx="88" cy="136" r="9" fill="#14b8a6"/>
  <path d="M98 136 L135 110 L180 110 L212 144" stroke="#2dd4bf" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <line x1="180" y1="110" x2="212" y2="144" stroke="#2dd4bf" stroke-width="4.5" stroke-linecap="round"/>
  <!-- Lift vector arrow -->
  <path d="M155 132 L155 116 M150 122 L155 114 L160 122" stroke="#00d4aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#14b8a6" letter-spacing="0.5">GLUTE BRIDGE &amp; CORE</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Lower Back Support - Spine-Safe Core</text>
</svg>''',

    'tempo_cycling.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg10" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e1b2e"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg10)" stroke="rgba(244,63,94,0.2)" stroke-width="1.5"/>
  <!-- Bike Wheels -->
  <circle cx="110" cy="130" r="22" fill="none" stroke="rgba(148,163,184,0.5)" stroke-width="3"/>
  <circle cx="210" cy="130" r="22" fill="none" stroke="rgba(148,163,184,0.5)" stroke-width="3"/>
  <!-- Frame -->
  <path d="M110 130 L150 130 L180 95 L145 95 Z M150 130 L145 95 M180 95 L210 130" stroke="#f43f5e" stroke-width="3.5" stroke-linejoin="round" fill="none"/>
  <!-- Rider -->
  <circle cx="145" cy="60" r="9" fill="#fb7185"/>
  <path d="M145 70 L154 94 L165 116" stroke="#f43f5e" stroke-width="3.5" stroke-linecap="round" fill="none"/>
  <path d="M148 76 L175 88" stroke="#fda4af" stroke-width="3" stroke-linecap="round" fill="none"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#f43f5e" letter-spacing="0.5">FAST-PACED CARDIO / CYCLING</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Aerobic Stamina - Endurance Builder</text>
</svg>''',

    'floor_pushups.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg11" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#08182c"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg11)" stroke="rgba(56,189,248,0.2)" stroke-width="1.5"/>
  <line x1="40" y1="145" x2="280" y2="145" stroke="rgba(148,163,184,0.4)" stroke-width="3" stroke-linecap="round"/>
  <!-- Figure: horizontal push-up -->
  <circle cx="220" cy="96" r="9" fill="#38bdf8"/>
  <path d="M212 102 L145 118 L85 142" stroke="#0ea5e9" stroke-width="4" stroke-linecap="round" fill="none"/>
  <path d="M190 108 L185 144" stroke="#7dd3fc" stroke-width="3.5" stroke-linecap="round" fill="none"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#38bdf8" letter-spacing="0.5">FLOOR / INCLINE PUSH-UPS</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Upper Body Power - Core &amp; Arm Strength</text>
</svg>''',

    'dumbbell_curls.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg12" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#181a24"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg12)" stroke="rgba(245,158,11,0.2)" stroke-width="1.5"/>
  <!-- Figure standing with weights -->
  <circle cx="160" cy="44" r="10" fill="#f59e0b"/>
  <path d="M160 56 L160 105 L148 144 M160 105 L172 144" stroke="#fbbf24" stroke-width="4" stroke-linecap="round" fill="none"/>
  <!-- Arms curling dumbbells -->
  <path d="M160 70 L140 92 L142 74 M160 70 L180 92 L178 74" stroke="#fef3c7" stroke-width="3.5" stroke-linecap="round" fill="none"/>
  <!-- Dumbbells -->
  <rect x="136" y="70" width="12" height="6" rx="2" fill="#f59e0b"/>
  <rect x="172" y="70" width="12" height="6" rx="2" fill="#f59e0b"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#f59e0b" letter-spacing="0.5">DUMBBELL / BAND STRENGTH</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Progressive Resistance - Muscle Tone</text>
</svg>''',

    'step_lunges.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg13" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0d1d28"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg13)" stroke="rgba(20,184,166,0.2)" stroke-width="1.5"/>
  <!-- Figure: lunge position -->
  <circle cx="145" cy="48" r="10" fill="#14b8a6"/>
  <path d="M145 60 L145 98 L180 110 L180 144 M145 98 L115 125 L115 144" stroke="#2dd4bf" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <path d="M145 74 L132 94 M145 74 L158 94" stroke="#5eead4" stroke-width="3" stroke-linecap="round" fill="none"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#14b8a6" letter-spacing="0.5">SUPPORTED STEP LUNGES</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Lower Body Power - Balance &amp; Hip Stability</text>
</svg>''',

    'plank_hold.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg14" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1c172e"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg14)" stroke="rgba(139,92,246,0.2)" stroke-width="1.5"/>
  <line x1="40" y1="145" x2="280" y2="145" stroke="rgba(148,163,184,0.4)" stroke-width="3" stroke-linecap="round"/>
  <!-- Figure: straight forearm plank -->
  <circle cx="220" cy="102" r="9" fill="#8b5cf6"/>
  <path d="M212 108 L145 118 L85 142" stroke="#a78bfa" stroke-width="4" stroke-linecap="round" fill="none"/>
  <path d="M195 112 L195 144 L210 144" stroke="#c4b5fd" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <!-- Timer accent -->
  <circle cx="145" cy="75" r="14" fill="rgba(139,92,246,0.15)" stroke="#8b5cf6" stroke-width="1.8"/>
  <line x1="145" y1="67" x2="145" y2="75" stroke="#8b5cf6" stroke-width="1.8" stroke-linecap="round"/>
  <line x1="145" y1="75" x2="151" y2="75" stroke="#8b5cf6" stroke-width="1.8" stroke-linecap="round"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#8b5cf6" letter-spacing="0.5">FOREARM PLANK HOLD</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Core Endurance - Isometric Strength</text>
</svg>''',

    'recumbent_cycling.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg15" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0a1e28"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg15)" stroke="rgba(56,189,248,0.2)" stroke-width="1.5"/>
  <!-- Recumbent bike chair and pedal -->
  <path d="M110 95 L110 135 L175 135 M205 135 A15 15 0 1 0 205 105 A15 15 0 1 0 205 135" stroke="rgba(148,163,184,0.5)" stroke-width="3" fill="none"/>
  <!-- Seated rider -->
  <circle cx="116" cy="75" r="9" fill="#38bdf8"/>
  <path d="M116 86 L124 116 L175 110 L195 120" stroke="#00d4aa" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <path d="M120 96 L145 105" stroke="#7dd3fc" stroke-width="3" stroke-linecap="round" fill="none"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#00d4aa" letter-spacing="0.5">RECUMBENT STATIONARY BIKE</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">Zero Knee Pound - Gentle Joint Aerobics</text>
</svg>''',

    'water_walking.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180" width="100%" height="100%">
  <defs>
    <linearGradient id="bg16" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#051c2e"/>
      <stop offset="100%" stop-color="#060c19"/>
    </linearGradient>
  </defs>
  <rect width="320" height="180" rx="16" fill="url(#bg16)" stroke="rgba(56,189,248,0.2)" stroke-width="1.5"/>
  <!-- Water Waves -->
  <path d="M40 115 Q80 110 120 115 T200 115 T280 115" stroke="#38bdf8" stroke-width="2.5" fill="none" opacity="0.7"/>
  <path d="M30 130 Q70 125 110 130 T190 130 T270 130" stroke="#00d4aa" stroke-width="2" fill="none" opacity="0.5"/>
  <!-- Figure walking in water -->
  <circle cx="160" cy="60" r="9" fill="#38bdf8"/>
  <path d="M160 70 L160 105 L174 135 M160 105 L146 135" stroke="#0ea5e9" stroke-width="3.5" stroke-linecap="round" fill="none"/>
  <path d="M160 80 L180 95 M160 80 L140 95" stroke="#7dd3fc" stroke-width="3" stroke-linecap="round" fill="none"/>
  <text x="20" y="28" font-family="sans-serif" font-size="12" font-weight="600" fill="#38bdf8" letter-spacing="0.5">POOL WATER WALKING</text>
  <text x="20" y="164" font-family="sans-serif" font-size="10" fill="#94a3b8">75% Weight Offload - Zero Joint Shock</text>
</svg>'''
}

out_dir = os.path.join('assets', 'exercises')
os.makedirs(out_dir, exist_ok=True)
for fname, content in svgs.items():
    fpath = os.path.join(out_dir, fname)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content.strip())
print(f'Successfully generated {len(svgs)} exercise illustration SVGs in {out_dir}')

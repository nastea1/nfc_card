const int powerBypassPin = PIN_PC0;
const int powerLedPin = PIN_PB0;


struct LedMap {
  uint8_t anodeIdx;
  uint8_t cathodeIdx;
};


const LedMap leds[20] = {
  {1, 4}, {4, 1}, {0, 4}, {4, 0}, {0, 1}, {1, 0}, {1, 2}, {2, 1},
  {2, 3}, {3, 2}, {3, 4}, {4, 3}, {0, 2}, {2, 0}, {1, 3}, {3, 1},
  {2, 4}, {4, 2}, {0, 3}, {3, 0}
};


struct LedMasks {
  uint8_t dir_mask;
  uint8_t out_mask;
};
LedMasks ledMasks[20];


// Per-LED brightness buffer (0 = off .. 16 = brightest), rendered by multiplexing.
uint8_t level[20];

// Vegas show state
uint16_t showTick = 0;        // advances each show update
uint8_t  phase = 0;           // current effect
uint16_t phaseTick = 0;       // ticks spent in current effect
unsigned long lastShowUpdate = 0;
uint16_t rng = 0xBEEF;        // xorshift PRNG state

unsigned long setupEndTime = 0;


float powerBrightness = 127.0f;
float breatheStep = -0.25f;


#define MORSE_UNIT 170


struct MorseElement {
  bool pinState;
  uint8_t units;
};

// Easter-egg message blinked on the indicator LED (Morse): "STAXXLOGIX.COM"
const MorseElement morseSequence[] = {
  {true, 1}, {false, 1}, {true, 1}, {false, 1}, {true, 1}, {false, 3},  // S  ...
  {true, 3}, {false, 3},  // T  -
  {true, 1}, {false, 1}, {true, 3}, {false, 3},  // A  .-
  {true, 3}, {false, 1}, {true, 1}, {false, 1}, {true, 1}, {false, 1}, {true, 3}, {false, 3},  // X  -..-
  {true, 3}, {false, 1}, {true, 1}, {false, 1}, {true, 1}, {false, 1}, {true, 3}, {false, 3},  // X  -..-
  {true, 1}, {false, 1}, {true, 3}, {false, 1}, {true, 1}, {false, 1}, {true, 1}, {false, 3},  // L  .-..
  {true, 3}, {false, 1}, {true, 3}, {false, 1}, {true, 3}, {false, 3},  // O  ---
  {true, 3}, {false, 1}, {true, 3}, {false, 1}, {true, 1}, {false, 3},  // G  --.
  {true, 1}, {false, 1}, {true, 1}, {false, 3},  // I  ..
  {true, 3}, {false, 1}, {true, 1}, {false, 1}, {true, 1}, {false, 1}, {true, 3}, {false, 3},  // X  -..-
  {true, 1}, {false, 1}, {true, 3}, {false, 1}, {true, 1}, {false, 1}, {true, 3}, {false, 1}, {true, 1}, {false, 1}, {true, 3}, {false, 3},  // .  .-.-.-
  {true, 3}, {false, 1}, {true, 1}, {false, 1}, {true, 3}, {false, 1}, {true, 1}, {false, 3},  // C  -.-.
  {true, 3}, {false, 1}, {true, 3}, {false, 1}, {true, 3}, {false, 3},  // O  ---
  {true, 3}, {false, 1}, {true, 3}, {false, 7}   // M  --
};


const uint8_t morseLength = sizeof(morseSequence) / sizeof(morseSequence[0]);
uint8_t morseIndex = 0;
unsigned long lastMorseTransition = 0;
bool morseEngineInitialized = false;


// brightness level (1..16) -> on-time in CPU cycles during one multiplex pass
const uint8_t briCycles[17] = {
  0, 1, 1, 2, 3, 4, 6, 9, 13, 19, 27, 38, 54, 76, 100, 130, 160
};


uint16_t rnd() {
  rng ^= rng << 7;
  rng ^= rng >> 9;
  rng ^= rng << 8;
  return rng;
}


void setup() {
  // in-rush prevention
  delay(300);


  // enable bypass MOSFET
  pinMode(powerBypassPin, OUTPUT);
  digitalWrite(powerBypassPin, LOW);


  // enable power LED
  pinMode(powerLedPin, OUTPUT);
  analogWrite(powerLedPin, 0);

  // pre-calculate hardware bitmasks
  for (int i = 0; i < 20; i++) {
    uint8_t aMask = (1 << (leds[i].anodeIdx + 1));
    uint8_t cMask = (1 << (leds[i].cathodeIdx + 1));
    ledMasks[i].dir_mask = aMask | cMask;
    ledMasks[i].out_mask = aMask;
  }


  PORTB.DIRCLR = 0x3E;


  // startup sweep: ring fills up as the power LED fades in
  uint32_t startupStart = millis();
  while (millis() - startupStart < 300) {
    uint32_t elapsed = millis() - startupStart;
    uint8_t lit = (elapsed * 20) / 300;            // grow the ring
    for (uint8_t i = 0; i < 20; i++) level[i] = (i <= lit) ? 16 : 0;
    renderLevels();
    analogWrite(powerLedPin, (uint8_t)((elapsed * 127) / 300));
  }


  for (uint8_t i = 0; i < 20; i++) level[i] = 0;
  rng ^= (uint16_t)millis();
  if (rng == 0) rng = 0xBEEF;
  showTick = 0; phase = 0; phaseTick = 0;
  lastShowUpdate = millis();
  setupEndTime = millis();
}


void loop() {
  renderLevels();


  // advance the light show on a steady time base (independent of render time)
  unsigned long currentMillis = millis();
  if (currentMillis - lastShowUpdate >= 28) {
    lastShowUpdate = currentMillis;
    updateShow();
  }


  if (currentMillis - setupEndTime < 10000) {
    // power LED breathing
    powerBrightness += breatheStep;
    if (powerBrightness >= 127.0f) {
      powerBrightness = 127.0f;
      breatheStep = -breatheStep;
    } else if (powerBrightness <= 0.0f) {
      powerBrightness = 0.0f;
      breatheStep = -breatheStep;
    }
    analogWrite(powerLedPin, (int)powerBrightness);


  } else {
    // easter egg (Morse on power LED) - unchanged
    if (!morseEngineInitialized) {
      lastMorseTransition = currentMillis;
      morseIndex = 0;
      analogWrite(powerLedPin, morseSequence[morseIndex].pinState ? 127 : 0);
      morseEngineInitialized = true;
    }


    unsigned long requiredDuration = (unsigned long)morseSequence[morseIndex].units * MORSE_UNIT;


    if (currentMillis - lastMorseTransition >= requiredDuration) {
      morseIndex = (morseIndex + 1) % morseLength;
      lastMorseTransition = currentMillis;
      analogWrite(powerLedPin, morseSequence[morseIndex].pinState ? 127 : 0);
    }
  }
}


// Advance the Vegas light show: SPIN -> SPARKLE -> STROBE -> DUAL COMET, then repeat.
void updateShow() {
  phaseTick++;

  switch (phase) {

    case 0: {  // SPIN: four bright dots chasing with short tails (fast casino wheel)
      for (uint8_t i = 0; i < 20; i++) level[i] = 0;
      for (uint8_t h = 0; h < 4; h++) {
        uint8_t head = (showTick + h * 5) % 20;
        level[head] = 16;
        level[(head + 19) % 20] = 8;
        level[(head + 18) % 20] = 3;
      }
      showTick += 1;                    // one step per tick -> ~0.56 s/rev
      if (phaseTick > 150) nextPhase();
      break;
    }

    case 1: {  // SPARKLE: random twinkles that fade (slot-machine lights)
      for (uint8_t i = 0; i < 20; i++)
        if (level[i] > 0) level[i] = (level[i] > 3) ? level[i] - 3 : 0;
      for (uint8_t k = 0; k < 3; k++) level[rnd() % 20] = 16;
      if (phaseTick > 150) nextPhase();
      break;
    }

    case 2: {  // STROBE: whole ring flashes in bursts (jackpot)
      bool on = ((phaseTick >> 2) & 1) == 0;   // on/off every 4 ticks
      for (uint8_t i = 0; i < 20; i++) level[i] = on ? 16 : 0;
      if (phaseTick > 56) nextPhase();          // ~7 flashes
      break;
    }

    default: {  // DUAL COMET: two heads sweeping opposite directions
      for (uint8_t i = 0; i < 20; i++) level[i] = 0;
      uint8_t a = showTick % 20;
      uint8_t b = (uint8_t)((20 - (showTick % 20)) % 20);
      level[a] = 16; level[(a + 19) % 20] = 7; level[(a + 18) % 20] = 2;
      level[b] = 16; level[(b + 1) % 20]  = 7; level[(b + 2) % 20]  = 2;
      showTick += 1;
      if (phaseTick > 200) nextPhase();
      break;
    }
  }
}


void nextPhase() {
  phase = (phase + 1) & 3;   // 0..3
  phaseTick = 0;
  for (uint8_t i = 0; i < 20; i++) level[i] = 0;
}


// Multiplex the ring: drive each lit LED for a dwell time set by its brightness level.
void renderLevels() {
  for (uint8_t i = 0; i < 20; i++) {
    uint8_t lv = level[i];
    if (lv == 0) continue;
    if (lv > 16) lv = 16;


    uint8_t dm = ledMasks[i].dir_mask;
    uint8_t om = ledMasks[i].out_mask;


    PORTB.OUTCLR = dm;
    PORTB.OUTSET = om;
    PORTB.DIRSET = dm;


    uint8_t c = briCycles[lv];
    while (c--) __builtin_avr_delay_cycles(1);


    PORTB.DIRCLR = dm;
  }
}

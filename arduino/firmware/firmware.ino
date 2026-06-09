#include <Adafruit_NeoPixel.h>

#define PIN_LED     3
#define PIN_ULTRA   A1
#define PIN_FLAME   4     // DFR0076 D0 → broche 4 (HIGH = flamme détectée)
#define PIN_BUZZER  5     // FT0449 speaker → broche 5
#define PIN_LIGHT   A2    // DFR0026 ambient light → broche A2
#define NUMPIXELS   1
#define SEUIL_LUMIERE 300 // en dessous = luminosité faible

Adafruit_NeoPixel pixels(NUMPIXELS, PIN_LED, NEO_GRB + NEO_KHZ800);

bool ledActive = false;
unsigned long derniereMouvement = 0;
unsigned long derniereEnvoi    = 0;

void setup() {
  Serial.begin(9600);
  pinMode(PIN_ULTRA, INPUT);
  pinMode(PIN_FLAME, INPUT);
  pinMode(PIN_LIGHT, INPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);
  pixels.begin();
  pixels.setBrightness(50);
  pixels.setPixelColor(0, pixels.Color(0, 0, 0));
  pixels.show();
  Serial.println("Système éclairage démarré...");
}

void loop() {
  // ── Capteur de présence (code original inchangé) ──────────────────────────
  int valeurBrute = analogRead(PIN_ULTRA);
  float distance = valeurBrute * 520.0 / 1023.0;
  bool presenceDetectee = (distance < 12);

  if (presenceDetectee) {
    derniereMouvement = millis();
    if (!ledActive) {
      ledActive = true;
      Serial.println("Présence détectée → LED allumée !");
    }
  }

  if (ledActive && (millis() - derniereMouvement > 300)) {
    ledActive = false;
    Serial.println("Plus de présence → LED éteinte !");
  }

  // ── Capteur de flamme ─────────────────────────────────────────────────────
  bool flameDetectee = (digitalRead(PIN_FLAME) == HIGH);

  // ── Capteur de luminosité ─────────────────────────────────────────────────
  int lightLevel    = analogRead(PIN_LIGHT);
  bool lumiereFaible = (lightLevel < SEUIL_LUMIERE);

  // ── Buzzer : son si flamme détectée ──────────────────────────────────────
  if (flameDetectee) {
    tone(PIN_BUZZER, 1000);
  } else {
    noTone(PIN_BUZZER);
  }

  // ── Couleur LED ───────────────────────────────────────────────────────────
  // flamme + présence → vert   |  flamme seule    → rouge
  // présence seule   → blanc   |  luminosité faible → jaune
  // rien             → éteint
  if (flameDetectee && ledActive) {
    pixels.setPixelColor(0, pixels.Color(0, 255, 0));
  } else if (flameDetectee) {
    pixels.setPixelColor(0, pixels.Color(255, 0, 0));
  } else if (ledActive) {
    pixels.setPixelColor(0, pixels.Color(255, 255, 255));
  } else if (lumiereFaible) {
    pixels.setPixelColor(0, pixels.Color(255, 200, 0));
  } else {
    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
  }
  pixels.show();

  // ── Envoi JSON toutes les 500ms ───────────────────────────────────────────
  if (millis() - derniereEnvoi >= 500) {
    derniereEnvoi = millis();
    Serial.print("{\"distance\":");
    Serial.print(distance, 1);
    Serial.print(",\"led\":");
    Serial.print(ledActive ? "true" : "false");
    Serial.print(",\"presence\":");
    Serial.print(presenceDetectee ? "true" : "false");
    Serial.print(",\"flame\":");
    Serial.print(flameDetectee ? "true" : "false");
    Serial.print(",\"light_level\":");
    Serial.print(lightLevel);
    Serial.print(",\"low_light\":");
    Serial.print(lumiereFaible ? "true" : "false");
    Serial.print(",\"uptime\":");
    Serial.print(millis() / 1000);
    Serial.println("}");
  }

  delay(200);
}

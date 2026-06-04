#include <Adafruit_NeoPixel.h>

#define PIN_LED     3
#define PIN_ULTRA   A1
#define NUMPIXELS   1

Adafruit_NeoPixel pixels(NUMPIXELS, PIN_LED, NEO_GRB + NEO_KHZ800);

bool ledActive = false;
unsigned long derniereMouvement = 0;
unsigned long derniereEnvoi = 0;  // AJOUT

void setup() {
  Serial.begin(9600);
  pinMode(PIN_ULTRA, INPUT);
  pixels.begin();
  pixels.setBrightness(50);
  pixels.setPixelColor(0, pixels.Color(0, 0, 0));
  pixels.show();
  Serial.println("Système éclairage démarré...");
}

void loop() {
  int valeurBrute = analogRead(PIN_ULTRA);

  // Nouvelle formule pour URM09
  float distance = valeurBrute * 520.0 / 1023.0;
  bool presenceDetectee = (distance < 12);  // AJOUT

  if (presenceDetectee) {
    derniereMouvement = millis();
    if (!ledActive) {
      ledActive = true;
      pixels.setPixelColor(0, pixels.Color(255, 255, 255));
      pixels.show();
      Serial.println("Présence détectée → LED allumée !");
    }
  }

  if (ledActive && (millis() - derniereMouvement > 300)) {
    ledActive = false;
    pixels.setPixelColor(0, pixels.Color(0, 0, 0));
    pixels.show();
    Serial.println("Plus de présence → LED éteinte !");
  }

  // AJOUT : envoi JSON toutes les 500ms pour le bridge MQTT
  if (millis() - derniereEnvoi >= 500) {
    derniereEnvoi = millis();
    Serial.print("{\"distance\":");
    Serial.print(distance, 1);
    Serial.print(",\"led\":");
    Serial.print(ledActive ? "true" : "false");
    Serial.print(",\"presence\":");
    Serial.print(presenceDetectee ? "true" : "false");
    Serial.print(",\"uptime\":");
    Serial.print(millis() / 1000);
    Serial.println("}");
  }

  delay(200);
}

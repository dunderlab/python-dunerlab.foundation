#include <M5Stack.h>
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"

MAX30105 particleSensor;

const byte RATE_SIZE = 4;
byte rates[RATE_SIZE];
byte rateSpot = 0;
long lastBeat = 0;

float beatsPerMinute;
int beatAvg;

const int graphHeight = 110; // Altura del gráfico en la pantalla
const int graphWidth = 320; // Ancho del gráfico (ancho total de la pantalla del M5Stack)
int graphX = 0; // Posición actual en el eje X para el gráfico

const int numReadings = 100; // Número de lecturas para el cálculo de irMin y irMax
long irReadings[numReadings]; // Arreglo para almacenar las lecturas
int readIndex = 0; // Índice actual para el siguiente valor de lectura

int lastY = 0; // Almacena la última posición Y del gráfico

void drawThickLine(int x0, int y0, int x1, int y1, int thickness, uint16_t color) {
  for (int i = -thickness / 2; i < thickness / 2 + thickness % 2; i++) {
    M5.Lcd.drawLine(x0, y0 + i, x1, y1 + i, color);
  }
}


void setup() {
  M5.begin();
  M5.Lcd.setTextColor(WHITE, BLACK);
  M5.Lcd.setTextSize(2);

  Serial.begin(115200);

  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    M5.Lcd.println("Sensor not found");
    while (1);
  }

  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x0A);
  particleSensor.setPulseAmplitudeGreen(0);

  M5.Lcd.println("Place finger on sensor");
}

void loop() {
  M5.update(); 
  long irValue = particleSensor.getIR();
  Serial.println(irValue);

  if (checkForBeat(irValue) == true) {
    long delta = millis() - lastBeat;
    lastBeat = millis();

    beatsPerMinute = 60 / (delta / 1000.0);

    if (beatsPerMinute < 255 && beatsPerMinute > 20) {
      rates[rateSpot++] = (byte)beatsPerMinute;
      rateSpot %= RATE_SIZE;

      beatAvg = 0;
      for (byte x = 0; x < RATE_SIZE; x++) {
        beatAvg += rates[x];
      }
      beatAvg /= RATE_SIZE;
    }
  }

  // Actualizar el arreglo de lecturas y el índice
  irReadings[readIndex] = irValue;
  readIndex++;
  if (readIndex >= numReadings) {
    readIndex = 0; // Volver al inicio del arreglo
  }

  // Recalcular irMax e irMin
  long irMax = 0;
  long irMin = 100000;
  for (int i = 0; i < numReadings; i++) {
    if (irReadings[i] > irMax) {
      irMax = irReadings[i];
    }
    if (irReadings[i] < irMin) {
      irMin = irReadings[i];
    }
  }


//  // Dibuja el gráfico
//  int yPos = map(irValue, irMin, irMax, graphHeight, 0); // Mapea el valor IR a la altura del gráfico
//  yPos = constrain(yPos, 0, graphHeight); // Asegura que el valor esté dentro del rango de la pantalla
//
//  M5.Lcd.drawPixel(graphX, 100 + yPos, WHITE); // Dibuja el punto en la posición correspondiente

//  graphX++;
//  if (graphX >= graphWidth) {
//    graphX = 0;
//    M5.Lcd.fillRect(0, 100, graphWidth, graphHeight, BLACK); // Limpia el área del gráfico
//  }


  // Dibuja el gráfico con líneas
  int yPos = map(irValue, irMin, irMax, graphHeight, 0);
  yPos = constrain(yPos, 0, graphHeight);

  if(graphX > 0) { // Asegúrate de que no es la primera lectura
//    M5.Lcd.drawLine(graphX - 1, graphHeight + lastY, graphX, graphHeight + yPos, WHITE);
    drawThickLine(graphX - 1, graphHeight + lastY, graphX, graphHeight + yPos, 4, WHITE);
  }
  lastY = yPos; // Actualiza lastY para la próxima lectura

  graphX++;
  if (graphX >= graphWidth) {
    graphX = 0;
    lastY = 0; // Restablece lastY cuando se limpia el gráfico
    M5.Lcd.fillRect(0, 100, graphWidth, graphHeight+20, BLACK);
  }


  // Actualización de la información de texto
//  M5.Lcd.fillRect(0, 0, 320, 200, BLACK); // Limpia la parte superior de la pantalla
  M5.Lcd.setCursor(0, 20);
  M5.Lcd.printf("IR: %d\nBPM: %.2f\nAvg BPM: %d", irValue, beatsPerMinute, beatAvg);

  if (irValue < 50000) {
    M5.Lcd.println("\nNo finger?");
  }
  else {
    M5.Lcd.println("\n          ");
    }
}

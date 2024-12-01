#define BLYNK_AUTH_TOKEN "7WLXNE1kchI2bFQECagu-2cOnzywRts5"
#define BLYNK_TEMPLATE_ID "TMPL2vxX7nblE"
#define BLYNK_TEMPLATE_NAME "Monoreo1"

#define BLYNK_PRINT Serial

#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include "Adafruit_SHT31.h"
#include "RTClib.h"
#include <BlynkSimpleEsp32.h>
#include <LiquidCrystal_I2C.h>

// Pines para la tarjeta SD
#define SPI_MISO  13  // MISO
#define SPI_MOSI  12  // MOSI
#define SPI_SCK   14  // SCK
#define SPI_CS    27  // CS



// Definir el pin GPIO 25 para el buzzer
#define BUZZER_PIN 33  
// Definir el pin GPIO 26 para el SSR
#define SSR_PIN 26  
#define SSR2_PIN 25  // Nuevo SSR para la segunda bomba

const int botonPin1 = 19;       // Pin del botón para encender el SSR 
const int botonPin2 = 18;       // Pin del botón para apagar el SSR         // Pin del SSR
bool estadoSSR = false;
bool boton1Presionado = false;  // Estado de presionado para el botón de encendido
bool boton2Presionado = false;  // Estado de presionado para el botón de apagado

#define SSR_LED_PIN V12  // LED en Blynk para SSR_PIN
#define SSR2_LED_PIN V13 // LED en Blynk para SSR2_PIN
#define VIRTUAL_PIN_SSR V12


// Crear un objeto SPI
SPIClass spi;

// Credenciales de Blynk y WiFi
char auth[] = BLYNK_AUTH_TOKEN;
char ssid[] = "MiguelPrueba";  // Nombre de tu red WiFi
char pass[] = "";  // Contraseña de tu red WiFi

LiquidCrystal_I2C lcd(0x27, 16, 2); // Dirección I2C 0x27, pantalla de 16x2

unsigned long messageStartTime = 0;  // Tiempo cuando se mostró el mensaje
bool showingMessage = false;         // Indica si el mensaje está siendo mostrado
bool isTurnedOn = false;             // Estado del SSR, si está encendido o apagado
bool isSSR2On = false; 

// Inicialización de los sensores y el RTC
Adafruit_SHT31 sht31_1 = Adafruit_SHT31();
Adafruit_SHT31 sht31_2 = Adafruit_SHT31();
Adafruit_SHT31 sht31_3 = Adafruit_SHT31();
Adafruit_SHT31 sht31_4 = Adafruit_SHT31(); // Sensor 4 para la temperatura ambiente
Adafruit_SHT31 sht31_5 = Adafruit_SHT31(); // ultimo sensor 
RTC_DS3231 rtc;  // Inicializa el RTC
#define TCAADDR 0x70  // Dirección del TCA9548A

int sensorIndex = 0;  // Índice para alternar entre los sensores
unsigned long previousMillis = 0;
const long interval = 5000;  // Intervalo de 5 segundos


// Definir las compensaciones para temperatura y humedad
float tempCompensation1 = 0;
float humCompensation1 = -8;
float tempCompensation2 = 0;
float humCompensation2 = -6;
float tempCompensation3 = 0;
float humCompensation3 = -10;
float tempCompensation4 = 0;
float humCompensation4 = -12;
float tempCompensation5 = 0;
float humCompensation5 = -6;

// Pesos para el promedio ponderado
float peso1 = 0.15;
float peso2 = 0.35;
float peso3 = 0.5;
float peso5 = 0.5;


// Variable para contar las secciones guardadas
int contador = 1;

// Variables para el buzzer y el SSR
long buzzerDuration = 1 * 60 * 1000; // Duración del buzzer (1 minuto)
bool buzzerActive = false; // Estado del buzzer

// Blynk timer para enviar datos periódicamente
BlynkTimer timer;

void tcaSelect(uint8_t i) {
  if (i > 7) return;
  Wire.beginTransmission(TCAADDR);
  Wire.write(1 << i);
  Wire.endTransmission();
}

// Función para enviar los datos de los sensores a Blynk
void sendSensorDataToBlynk() {
  tcaSelect(0);
  float temp1 = sht31_1.readTemperature() + tempCompensation1;
  float hum1 = sht31_1.readHumidity() + humCompensation1;

  tcaSelect(1);
  float temp2 = sht31_2.readTemperature() + tempCompensation2;
  float hum2 = sht31_2.readHumidity() + humCompensation2;

  tcaSelect(2);
  float temp3 = sht31_3.readTemperature() + tempCompensation3;
  float hum3 = sht31_3.readHumidity() + humCompensation3;

  tcaSelect(3);
  float temp4 = sht31_4.readTemperature() + tempCompensation4;
  float hum4 = sht31_4.readHumidity() + humCompensation4;


// alertas de Blynk

if (temp1 >= 39) {
    Blynk.logEvent("temp_critica", "¡Temperatura crítica mayor o igual a 39°C!");
    Serial.println("Alerta en Blynk: Temperatura crítica mayor o igual a 39°C");
} 
else if (temp1 >= 38 && temp2 < 39) {
    Blynk.logEvent("temp_alta", "Temperatura alta, entre 38°C y 39°C.");
    Serial.println("Alerta en Blynk: Temperatura alta, entre 38°C y 39°C");
} 
else if (temp1 >= 37 && temp2 < 38) {
    Blynk.logEvent("temp_moderada", "Temperatura moderada, entre 37°C y 38°C.");
    Serial.println("Alerta en Blynk: Temperatura moderada, entre 37°C y 38°C");
}

  // Calcular los promedios ponderados
  float promedioTempPonderado = (peso1 * temp1 + peso2 * temp2 + peso3 * temp3) / (peso1 + peso2 + peso3);
  float promedioHumPonderado = (peso1 * hum1 + peso2 * hum2 + peso3 * hum3) / (peso1 + peso2 + peso3);

  // Enviar datos a Blynk
  Blynk.virtualWrite(V0, temp1);
  Blynk.virtualWrite(V1, hum1);
  Blynk.virtualWrite(V2, temp2);
  Blynk.virtualWrite(V3, hum2);
  Blynk.virtualWrite(V4, temp3);
  Blynk.virtualWrite(V5, hum3);
  Blynk.virtualWrite(V6, temp4);
  Blynk.virtualWrite(V7, hum4);
  Blynk.virtualWrite(V8, promedioTempPonderado);
  Blynk.virtualWrite(V9, promedioHumPonderado);
}

  
// Función para controlar el SSR1 desde Blynk
BLYNK_WRITE(V10) {
  int value = param.asInt();  // Lee el valor desde la app Blynk
  if (value == 1) {
    digitalWrite(SSR_PIN, HIGH);  // Activar SSR
    Serial.println("SSR activado desde Blynk.");

    // Mostrar mensaje de SSR activado en la pantalla LCD
    tcaSelect(6);  // Seleccionar el canal del multiplexor para la LCD
    lcd.clear();  // Limpiar la pantalla antes de mostrar el nuevo mensaje
    lcd.setCursor(0, 0);
    lcd.print("Motobomba");
    lcd.setCursor(0, 1);
    lcd.print("piscina encendida");

    // Guardar el tiempo actual y activar el indicador
    messageStartTime = millis();
    showingMessage = true;
    isTurnedOn = true;  // Indica que la motobomba está encendida

  } else {
    digitalWrite(SSR_PIN, LOW);  // Desactivar SSR
    Serial.println("SSR desactivado desde Blynk.");

    // Mostrar mensaje de SSR desactivado en la pantalla LCD
    tcaSelect(6);  // Seleccionar el canal del multiplexor para la LCD
    lcd.clear();  // Limpiar la pantalla antes de mostrar el nuevo mensaje
    lcd.setCursor(0, 0);
    lcd.print("Motobomba");
    lcd.setCursor(0, 1);
    lcd.print("piscina apagada");

    // Guardar el tiempo actual y activar el indicador
    messageStartTime = millis();
    showingMessage = true;
    isTurnedOn = false;  // Indica que la motobomba está apagada
  }
  if (value == 0) {
    digitalWrite(SSR_PIN, LOW);  // Activar SSR
    isTurnedOn = true;           // Indica que el SSR está activado
    Blynk.virtualWrite(SSR_LED_PIN, 0);  // Enciende el LED de Blynk para SSR_PIN
    Serial.println("SSR desactivado desde Blynk.");
  } else {
    digitalWrite(SSR_PIN, HIGH);  // Desactivar SSR
    isTurnedOn = false;           // Indica que el SSR está apagado
    Blynk.virtualWrite(SSR_LED_PIN, 255);    // Apaga el LED de Blynk para SSR_PIN
    Serial.println("SSR activado desde Blynk.");
  }

}

BLYNK_WRITE(V11) {
  int value = param.asInt();  // Lee el valor desde la app Blynk
  if (value == 1) {
    digitalWrite(SSR2_PIN, HIGH);  // Activar SSR2
    isSSR2On = true;              // Indica que el SSR2 está activado
    Blynk.virtualWrite(SSR2_LED_PIN, 255); // Enciende el LED de Blynk para SSR2_PIN
    Serial.println("SSR2 activado desde Blynk.");

    // Mostrar mensaje de SSR2 activado en la pantalla LCD
    tcaSelect(6);
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Motobomba");
    lcd.setCursor(0, 1);
    lcd.print("casa apagada");
  } else {
    digitalWrite(SSR2_PIN, LOW);  // Desactivar SSR2
    isSSR2On = false;              // Indica que el SSR2 está apagado
    Blynk.virtualWrite(SSR2_LED_PIN, 0);   // Apaga el LED de Blynk para SSR2_PIN
    Serial.println("SSR2 desactivado desde Blynk.");

    // Mostrar mensaje de SSR2 desactivado en la pantalla LCD
    tcaSelect(6);
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Motobomba");
    lcd.setCursor(0, 1);
    lcd.print("casa encendida");
  }
}


void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);

unsigned long currentMillis = millis();  // Obtener el tiempo actual

  // Verificar si han pasado 5 segundos desde que se mostró el mensaje
  if (showingMessage && (currentMillis - messageStartTime >= 5000)) {
    // Restaurar la visualización de temperatura y humedad
    tcaSelect(6);
    lcd.clear();  // Limpiar la pantalla antes de mostrar los datos normales
    lcd.setCursor(0, 0);
    lcd.print("Temp");
    lcd.setCursor(0, 1);
    lcd.print("Hum");

    showingMessage = false;  // Desactivar el indicador de mensaje mostrado
  }

  // Configurar el pin del buzzer y del SSR como salida
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(SSR_PIN, OUTPUT);
  pinMode(SSR2_PIN, OUTPUT);  // Configurar SSR2 como salida
  
  pinMode(botonPin1, INPUT_PULLUP);
  pinMode(botonPin2, INPUT_PULLUP);
  
  // Inicializar el estado del SSR en apagado
  digitalWrite(SSR_PIN, HIGH);
  estadoSSR = false;

  // Inicializar SPI para la SD
  spi.begin(SPI_SCK, SPI_MISO, SPI_MOSI, SPI_CS);

  // Iniciar la tarjeta SD
  if (!SD.begin(SPI_CS, spi)) {
    Serial.println("Error al inicializar la tarjeta SD.");
    return;
  }
  
  Serial.println("Tarjeta SD inicializada correctamente.");

  // Inicializar sensores
  tcaSelect(0); sht31_1.begin(0x44);
  tcaSelect(1); sht31_2.begin(0x44);
  tcaSelect(2); sht31_3.begin(0x44);
  tcaSelect(3); sht31_4.begin(0x44);
  tcaSelect(4); sht31_5.begin(0x44);
  
  // Inicializar el RTC
  tcaSelect(5);
  if (!rtc.begin()) {
    Serial.println("No se encontró el RTC");
    while (1);
  }

  // Conectar a WiFi y Blynk
  Blynk.begin(auth, ssid, pass);

  // Configurar el temporizador para enviar datos a Blynk cada 5 segundos
  timer.setInterval(5000L, sendSensorDataToBlynk);

  // Imprimir la cabecera de las columnas
  Serial.println("Num_Seccion,Fecha_Hora,Temp_S1,Hum_S1,Temp_S2,Hum_S2,Temp_S3,Hum_S3,Temp_Ambiente,Hum_Ambiente,PromedioTemp_Pond,PromedioHum_Pond");

// Inicializar la pantalla LCD una sola vez
  tcaSelect(6);  // Seleccionar el canal del multiplexor para la LCD
  lcd.init();    // Inicializa la pantalla LCD
  lcd.backlight();  // Activa la luz de fondo

  // Imprimir la cabecera de las columnas
  Serial.println("Num_Seccion,Fecha_Hora,Temp_S1,Hum_S1,Temp_S2,Hum_S2,Temp_S3,Hum_S3,Temp_Ambiente,Hum_Ambiente,PromedioTemp_Pond,PromedioHum_Pond");
}

void loop() {
  unsigned long currentMillis = millis();  // Obtener el tiempo actual

  // Cambiar la lectura en la LCD cada 5 segundos
  if (currentMillis - previousMillis >= interval) {
      previousMillis = currentMillis;

      float temp = 0, hum = 0;
      switch (sensorIndex) {
          case 0:
              tcaSelect(0);
              temp = sht31_1.readTemperature() + tempCompensation1;
              hum = sht31_1.readHumidity() + humCompensation1;
              break;
          case 1:
              tcaSelect(1);
              temp = sht31_2.readTemperature() + tempCompensation2;
              hum = sht31_2.readHumidity() + humCompensation2;
              break;
          case 2:
              tcaSelect(2);
              temp = sht31_3.readTemperature() + tempCompensation3;
              hum = sht31_3.readHumidity() + humCompensation3;
              break;
          case 3:
              tcaSelect(3);
              temp = sht31_4.readTemperature() + tempCompensation4;
              hum = sht31_4.readHumidity() + humCompensation4;
              break;
          case 4:
              tcaSelect(4);
              temp = sht31_5.readTemperature() + tempCompensation5;
              hum = sht31_5.readHumidity() + humCompensation5;
              break;
      }

      // Mostrar los valores de temperatura y humedad en la LCD
      tcaSelect(6);  // Seleccionar el canal del multiplexor para la LCD
      lcd.setCursor(0, 0);
      lcd.print("Temp");
      lcd.print(sensorIndex + 1);
      lcd.print("=");
      lcd.print(temp);
      
      lcd.setCursor(0, 1);
      lcd.print("Hum");
      lcd.print(sensorIndex + 1);
      lcd.print("=");
      lcd.print(hum);

      // Alternar entre los sensores (de 0 a 4)
      sensorIndex = (sensorIndex + 1) % 5;
  }

  // Leer datos de los sensores y guardar en la SD
  tcaSelect(0);
  float temp1 = sht31_1.readTemperature() + tempCompensation1;
  float hum1 = sht31_1.readHumidity() + humCompensation1;

  tcaSelect(1);
  float temp2 = sht31_2.readTemperature() + tempCompensation2;
  float hum2 = sht31_2.readHumidity() + humCompensation2;

  tcaSelect(2);
  float temp3 = sht31_3.readTemperature() + tempCompensation3;
  float hum3 = sht31_3.readHumidity() + humCompensation3;

  tcaSelect(3);
  float temp4 = sht31_4.readTemperature() + tempCompensation4;
  float hum4 = sht31_4.readHumidity() + humCompensation4;

  tcaSelect(4);
  float temp5 = sht31_5.readTemperature() + tempCompensation5;
  float hum5 = sht31_5.readHumidity() + humCompensation5;

  // Leer la fecha y hora del RTC
  tcaSelect(5);
  DateTime now = rtc.now();

  // Calcular los promedios ponderados
  float promedioTempPonderado = (peso1 * temp1 + peso2 * temp2 + peso3 * temp3) / (peso1 + peso2 + peso3);
  float promedioHumPonderado = (peso1 * hum1 + peso2 * hum2 + peso3 * hum3) / (peso1 + peso2 + peso3);

  // Validar lecturas
  if (!isnan(temp1) && !isnan(hum1) && !isnan(temp2) && !isnan(hum2) && !isnan(temp3) && !isnan(hum3) && !isnan(temp4) && !isnan(hum4) && !isnan(temp5) && !isnan(hum5)) {
    
    // Imprimir los datos con enumeración
    Serial.print(contador); Serial.print(",");
    
    // Imprimir fecha y hora en el formato "YYYY/MM/DD HH:MM:SS"
    Serial.print(now.year(), DEC); Serial.print("/");
    Serial.print(now.month(), DEC); Serial.print("/");
    Serial.print(now.day(), DEC); Serial.print(" ");
    Serial.print(now.hour(), DEC); Serial.print(":");
    Serial.print(now.minute(), DEC); Serial.print(":");
    Serial.print(now.second(), DEC);
    Serial.print(",");

    // Imprimir valores de los sensores
    Serial.print(temp1); Serial.print(",");
    Serial.print(hum1); Serial.print(",");
    Serial.print(temp2); Serial.print(",");
    Serial.print(hum2); Serial.print(",");
    Serial.print(temp3); Serial.print(",");
    Serial.print(hum3); Serial.print(",");
    Serial.print(temp5); Serial.print(",");
    Serial.print(hum5); Serial.print(",");
    Serial.print(temp4); Serial.print(",");
    Serial.print(hum4); Serial.print(",");
    Serial.print(promedioTempPonderado); Serial.print(",");
    Serial.println(promedioHumPonderado);

    
    // Guardar los datos en la tarjeta SD
    File dataFile = SD.open("/DATOS.txt", FILE_APPEND);
    if (dataFile) {
      dataFile.print(contador); dataFile.print(",");
      dataFile.print(now.year(), DEC); dataFile.print("/");
      dataFile.print(now.month(), DEC); dataFile.print("/");
      dataFile.print(now.day(), DEC); dataFile.print(" ");
      dataFile.print(now.hour(), DEC); dataFile.print(":");
      dataFile.print(now.minute(), DEC); dataFile.print(":");
      dataFile.print(now.second(), DEC);
      dataFile.print(",");
      dataFile.print(temp1); dataFile.print(",");
      dataFile.print(hum1); dataFile.print(",");
      dataFile.print(temp2); dataFile.print(",");
      dataFile.print(hum2); dataFile.print(",");
      dataFile.print(temp3); dataFile.print(",");
      dataFile.print(hum3); dataFile.print(",");
      dataFile.print(temp4); dataFile.print(",");
      dataFile.print(hum4); dataFile.print(",");
      dataFile.print(temp5); dataFile.print(",");
      dataFile.print(hum5); dataFile.print(",");
      dataFile.print(promedioTempPonderado); dataFile.print(",");
      dataFile.println(promedioHumPonderado);
      dataFile.close();
    } else {
      Serial.println("Error al abrir el archivo datalog.txt");
    }
  } else {
    Serial.println("Error: Lectura inválida en los sensores.");
  }

  // Activar el buzzer y apagar el SSR si la temperatura del sensor 2 es mayor a 45°C
  if (temp1 > 45) {
    digitalWrite(BUZZER_PIN, HIGH);
    digitalWrite(SSR_PIN, LOW);  // Apagar el SSR
    digitalWrite(SSR2_PIN, LOW);  // Apagar el SSR2
    buzzerActive = true;
  } else if (buzzerActive && temp2 <= 45) {
    digitalWrite(BUZZER_PIN, LOW);
    buzzerActive = false;
  }

// Verificar si el botón de encendido (GPIO 19) ha sido presionado
if (digitalRead(botonPin1) == LOW && !boton1Presionado) {
  boton1Presionado = true;
  Blynk.virtualWrite(V10, 1); // Enciende el botón virtual V10 en Blynk
  digitalWrite(SSR_PIN, HIGH); // Enciende el SSR
  Serial.println("Botón físico en GPIO 19 presionado: V10 encendido y SSR encendido");
}
if (digitalRead(botonPin1) == HIGH) {
  boton1Presionado = false; // Resetea el estado del botón al soltarlo
}

// Verificar si el botón de apagado (GPIO 18) ha sido presionado
if (digitalRead(botonPin2) == LOW && !boton2Presionado) {
  boton2Presionado = true;
  Blynk.virtualWrite(V10, 0); // Apaga el botón virtual V10 en Blynk
  digitalWrite(SSR_PIN, LOW); // Apaga el SSR
  Serial.println("Botón físico en GPIO 18 presionado: V10 apagado y SSR apagado");
}
if (digitalRead(botonPin2) == HIGH) {
  boton2Presionado = false; // Resetea el estado del botón al soltarlo
}
 


  // Incrementar el contador
  contador++;

  // Correr Blynk y el temporizador
  Blynk.run();
  timer.run();

  // Esperar 5 segundos antes de la próxima lectura
  delay(3000);
}
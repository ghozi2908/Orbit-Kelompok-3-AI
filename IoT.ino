#include <MD_Parola.h>
#include <MD_MAX72xx.h>
#include <SPI.h>
#include <ESP8266WiFi.h>
#include "FirebaseESP8266.h"
#include <DHT.h> //library DHT
#define DHTPIN D2 //pin DATA konek ke pin 2 Arduino
#define DHTTYPE DHT11 //tipe sensor DHT11
DHT dht(DHTPIN, DHTTYPE); //set sensor + koneksi pin


#define HARDWARE_TYPE MD_MAX72XX::FC16_HW
#define MAX_DEVICES 4 // Instruksi untuk mengatur berapa banyak dotmatrix yang digunakan
#define CLK_PIN   D5 // or SCK
#define DATA_PIN  D7 // or MOSI
#define CS_PIN    D8 // or SS   // Deklarasi CS pada pin 10 Arduino
MD_Parola myDisplay = MD_Parola(HARDWARE_TYPE, CS_PIN, MAX_DEVICES);

#define WIFI_NAME "UNTIRTAKU" //SSID HOTSPOT Ghozi Yusuf M
#define WIFI_PASSWORD "untirtajawara" //Password Hotspot
 //Link Firebase Realtime
#define FIREBASE_URL "https://kirim-gambar-fix-default-rtdb.asia-southeast1.firebasedatabase.app/"
//Link Token Api
#define FIREBASE_TOKEN "AIzaSyCSF9MomoQPTN0mbfaCOuWLXVJg_h5W4es"
 
String data;
// Jarak maksimal yang ingin dideteksi (dalam centimeter)
int waktusebelum=0;
int waktusebelum1=0;
int timeout =0;
float temp, humi;
FirebaseData firebaseData;

void setup() {
  Serial.begin(9600);
  dht.begin();
  myDisplay.begin();
  pinMode(D0, OUTPUT);
  pinMode(D1, OUTPUT);
  digitalWrite(D0, HIGH);
  digitalWrite(D1, LOW);
  myDisplay.setSpeed(200);
  myDisplay.setIntensity(4); //Kecerahan
  myDisplay.displayClear();
  myDisplay.displayScroll("<< Orbit Academy >> Coach: Annisa >>Team : Ghozi, Arya, Istianah, Rifaldi, Ghani, Annas", PA_CENTER, PA_SCROLL_LEFT, 200);
    
    //nama wifi yang terhubung dengan internet
  WiFi.begin(WIFI_NAME, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED && timeout<100) 
  {
    timeout=timeout+1; 
    delay(500);
    Serial.print(".");
  }
 
  if(timeout>=100)
  {
    Serial.println("");
    Serial.println("WiFi Disconnected");
  }
  else
  {
    Serial.println("");
    Serial.println("WiFi connected");
    digitalWrite(D1, HIGH);
    digitalWrite(D0, LOW);
  } 
  // Print the IP address ---------------------
  Serial.println(WiFi.localIP());
  Firebase.begin(FIREBASE_URL, FIREBASE_TOKEN);
}

void loop() {
  if(millis()-waktusebelum1 >=2000){
     humi = dht.readHumidity();//baca kelembaban
     temp = dht.readTemperature();//baca suhu
     waktusebelum1=millis();

     Serial.print("Suhu=");  //kirim serial "Suhu"
     Serial.print(temp);     //kirim serial nilai suhu
     Serial.println("C");    //kirim serial "C" Celcius 
     Serial.print("Humi=");  //kirim serial "Humi"
     Serial.print(humi);     //kirim serial nilai kelembaban
     Serial.println("%RH");  //kirim serial "%RH"
  }
 if (millis()-waktusebelum >=7000){
    if(temp >0 && humi >0){
    Firebase.setString(firebaseData, "/kelembapan",String(humi));
    Firebase.setString(firebaseData, "/suhu", String(temp));
    Firebase.setString(firebaseData, "/ph", String(7));
    waktusebelum=millis();
    Serial.println("==========SEND TO CLOUD=========");  //kirim serial "%RH"
    }
  }

 if (myDisplay.displayAnimate()) { //Print Tulisan
    myDisplay.displayReset();
  }
  delay(30);
}
//link: https://www.circuitgeeks.com/arduino-max7219-led-matrix-display/

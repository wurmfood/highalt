/*
  Data Logging using a handful of digital sensors. Intended for high-alt balloon data gathering.
  Hardware sensors and shields used:
    Adafruit MAX31855 K-type thermocouple amplifier
    Adafruit MPL3115A2 Pressure/Altitude/Temperature sensor
    Adafruit 9-DOF LSM9DSO Accel/Mag/Gyro+temp
    Adafruit GPS

  Author: David Vetter
  (pulling heavily from example sketches)
*/

/*
  Includes
*/
#include <avr/pgmspace.h>

#include <SPI.h>

#include <Wire.h>

// Include for the thermocouple:
#include "Adafruit_MAX31855.h"

// Includes for Baromter
#include <Adafruit_MPL3115A2.h>
Adafruit_MPL3115A2 barometer = Adafruit_MPL3115A2();

// GPS includes
#include <Adafruit_GPS.h>
#include <SoftwareSerial.h>
// Use pin 3 for TX and 2 for RX
#define GPS_TX 8
#define GPS_RX 9
SoftwareSerial mySerial(GPS_TX, GPS_RX);
Adafruit_GPS GPS(&mySerial);
//String NMEA1;
//String NMEA2;

// LSM9DSO
#include <Adafruit_Sensor.h>
#include <Adafruit_LSM9DS0.h>
Adafruit_LSM9DS0 lsm = Adafruit_LSM9DS0(1000);

/*
  Thermocouple setup (MAX31855)
*/
// Example creating a thermocouple instance with software SPI on any three
// digital IO pins.
#define K_DO   4
#define K_CS   3
#define K_CLK  2
Adafruit_MAX31855 thermocouple(K_CLK, K_CS, K_DO);
//double k_temp = 0;
// If we get a bad reading, put this in. We'll be able to find it later.
const double badTemp = -3.14E03;


// How we're going to control how often we actually querry data.
uint32_t timer = millis();

void setup() {
  Serial.begin(115200);
  Serial.println("Made it to setup.");
  
  // GPS Setup
  GPS.begin(9600);
  // Minimum data and GGA (fix data)
  GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);
  GPS.sendCommand(PMTK_SET_NMEA_UPDATE_5HZ);
  GPS.sendCommand(PMTK_API_SET_FIX_CTL_5HZ);
  // More info on these settings in the Adafruit GPS examples.
  
  Serial.println("GPS: OK");
  
  // LSM startup:
  
  if(lsm.begin())
  {
    Serial.println(F("LSM: OK"));
    
    // 1.) Set the accelerometer range
    //lsm.setupAccel(lsm.LSM9DS0_ACCELRANGE_2G);
    //lsm.setupAccel(lsm.LSM9DS0_ACCELRANGE_4G);
    lsm.setupAccel(lsm.LSM9DS0_ACCELRANGE_6G);
    
    // 2.) Set the magnetometer sensitivity
    lsm.setupMag(lsm.LSM9DS0_MAGGAIN_2GAUSS);
    //lsm.setupMag(lsm.LSM9DS0_MAGGAIN_4GAUSS);
  
    // 3.) Setup the gyroscope
    lsm.setupGyro(lsm.LSM9DS0_GYROSCALE_245DPS);
    //lsm.setupGyro(lsm.LSM9DS0_GYROSCALE_500DPS);
    
  } else {
    Serial.println(F("LSM: Fail"));
  }
    
  
  
  // Barometer startup:
  
  if (barometer.begin()) {
    Serial.println(F("Barometer: OK!"));
  } else {
    Serial.println(F("Barometer: Fail"));
  }
  
  Serial.println("Setup complete. Begin data gathering.");
}

bool run_once = true;

void loop() {
  // first, see if we receive anything.
  while (run_once) {
    // wait for a something from serial
    if(Serial.available() > 0 ) {
      run_once = false;
      run_once_connected();
    }    
  }
  
  while(!run_once) {
    // Handle strange events with the timer by resetting it.
    if (timer > millis()) timer = millis();
    
    if (millis() - timer > 700) {
      // GPS
      readGPS();
      
      // print something
      Serial.print(String(timer) + ",");
      get_gps_data();
      print_lsm_data();
      get_barometric_data();
      print_therm();
      Serial.println("");
      timer = millis();
    }
  }
}


void run_once_connected() {
  Serial.print(F("Arduino: Millis, GPS: Date, Time, GPS Fix, Latitude, Longitude, speed (knots), angle, altitude, "));
  Serial.print(F("LSM: accel x, y, z, mag x, y, z, gyro x, y, z, temp, "));
  Serial.print(F("Barometere: Pressure (kPa), Alt (m), Temp (C), "));
  Serial.println(F("K-Temp: Temp (C)"));
}

// return a string with the pressure, altitude, and temp

void get_barometric_data() {
  // stuff goes here
  Serial.print(barometer.getPressure()); // Pascals (kPa)
  printSep();
  Serial.print(barometer.getAltitude()); // meters
  printSep();
  Serial.print(barometer.getTemperature()); // C
  printSep();
}


void readGPS(){  //This function will read and remember two NMEA sentences from GPS
  char c;
  clearGPS();    //Serial port probably has old or corrupt data, so begin by clearing it all out
  while(!GPS.newNMEAreceived()) { //Keep reading characters in this loop until a good NMEA sentence is received
    c=GPS.read(); //read a character from the GPS
  }
  GPS.parse(GPS.lastNMEA());  //Once you get a good NMEA, parse it
//  NMEA1=GPS.lastNMEA();      //Once parsed, save NMEA sentence into NMEA1
  while(!GPS.newNMEAreceived()) {  //Go out and get the second NMEA sentence, should be different type than the first one read above.
    c=GPS.read();
  }
  GPS.parse(GPS.lastNMEA());
//  NMEA2=GPS.lastNMEA();
  //Serial.println(NMEA1);
  //Serial.println(NMEA2);
  //Serial.println("");
}

void clearGPS() {  //Since between GPS reads, we still have data streaming in, we need to clear the old data by reading a few sentences, and discarding these
  char c;
  while(!GPS.newNMEAreceived()) {
    c=GPS.read();
  }
  GPS.parse(GPS.lastNMEA());
  while(!GPS.newNMEAreceived()) {
    c=GPS.read();
  }
  GPS.parse(GPS.lastNMEA());
}

void printSep() {
  Serial.write(',');
}

void printSlash() {
  Serial.write('/');
}

void printCol() {
  Serial.write(':');
}

void get_gps_data() {
  // Date
  //Serial.print("20" + GPS.year + '/' + GPS.month + '/' + GPS.day + ',');
  Serial.print("20");
  Serial.print(GPS.year);
  printSlash();
  Serial.print(GPS.month);
  printSlash();
  Serial.print(GPS.day);
  printSep();
  // Time
  Serial.print(GPS.hour);
  printCol();
  Serial.print(GPS.minute);
  printCol();
  Serial.print(GPS.seconds);
  Serial.write('.');
  Serial.print(GPS.milliseconds);
  printSep();
  // Fix data
  Serial.print(GPS.fix);
  printSep();
  if (GPS.fix) {
    Serial.print(GPS.latitudeDegrees,7);
    printSep();
    Serial.print(GPS.longitudeDegrees,7);
    printSep();
    Serial.print(GPS.speed);
    printSep();
    Serial.print(GPS.angle);
    printSep();
    Serial.print(GPS.altitude);
    printSep();
  } else {
    Serial.print(",,,,,"); // no data so fill in with blanks.
  }
}




sensors_event_t accel, mag, gyro, temp;
void print_lsm_data() {
  lsm.getEvent(&accel, &mag, &gyro, &temp);
  Serial.print(accel.acceleration.x);
  printSep();
  Serial.print(accel.acceleration.y);
  printSep();
  Serial.print(accel.acceleration.z);
  printSep();
  
  Serial.print(mag.magnetic.x);
  printSep();
  Serial.print(mag.magnetic.y);
  printSep();
  Serial.print(mag.magnetic.z);
  printSep();
  
  Serial.print(gyro.gyro.x);
  printSep();
  Serial.print(gyro.gyro.y);
  printSep();
  Serial.print(gyro.gyro.z);
  printSep();
  
  Serial.print(temp.temperature);
  printSep();
}



void print_therm() {
  double c = thermocouple.readCelsius();
  if( isnan(c) ) {
    c = badTemp;
  }
//  Serial.print(thermocouple.readInternal());
//  printSep();
  Serial.print(c);
}

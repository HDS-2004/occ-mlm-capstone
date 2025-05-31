#include <avr/io.h>

// Set up the pin for the LED
constexpr int ledPin = 11; // Pin 13 has the built-in LED on most Arduino boards, including the Uno

void setup()
{
  // Initialize the LED pin as an output
  pinMode(ledPin, OUTPUT);
  pinMode(2,INPUT);
  randomSeed(analogRead(2));
  TCCR2B = (TCCR2B & 0b11111000) | 0x01;
}


constexpr uint8_t levels[] = {0 ,80, 170, 255};
constexpr uint16_t t_shutter = 50; // do not change unless you know what ur doing
constexpr uint16_t bar_duration =700; 
//Lower bar duration, higher chance the whole packets going to get turned into mush by exposure averaging
//Higher bar duration, higher chance the whole packets going to appear very flickery in the camera (but its fine, always prefer longer bar duration over shorter , makes the pulses have better pulse shape by giving it more time to form) 
constexpr uint16_t guard_duration = 200; //tune 


uint8_t prev_pulse = 255; 

static void inline pulser(uint8_t p)
{
  uint16_t t_on = floor(t_shutter * (p / 255.0));
    // ton / ton+toff = duty cycle
  uint16_t cycles = bar_duration / t_shutter;

  switch (p)  
  {
  case 255:
    PORTB |= (1 << PB3);  
    delayMicroseconds(bar_duration);
    return;
  default:
    cycles = bar_duration/ t_shutter;
    for (uint16_t i = 0; i < cycles; i++)
    {

      PORTB |= (1 << PB3);   // Turn on pin 11


      delayMicroseconds(t_on);
      PORTB &= ~(1 << PB3);  // Turn off pin 11
      delayMicroseconds(t_shutter - t_on);
    }
    return;
  }
}

static void inline guarded_pulser(uint8_t p){
  if(prev_pulse - p > 100 || p >= levels[2]){
    //If the pulse is on the higher end or if the current pulse is significantly weaker than previous pulse 
    PORTB &= ~(1 << PB3); 
  delayMicroseconds(guard_duration*2);
  pulser(p);
  PORTB &= ~(1 << PB3); 
  delayMicroseconds(guard_duration*2);
  }
  else if(p == 0){
    PORTB &= ~(1 << PB3); 
    delayMicroseconds(guard_duration*2 + bar_duration);
  }
  else{
    PORTB &= ~(1 << PB3); 
  delayMicroseconds(guard_duration);
  pulser(p);
  PORTB &= ~(1 << PB3); 
  delayMicroseconds(guard_duration);
  }
  prev_pulse = p;
}

static void inline header(){
  PORTB &= ~(1 << PB3); 
  delayMicroseconds(bar_duration*1.2);
  PORTB |= (1 << PB3); 
  delayMicroseconds(guard_duration/10);
  PORTB &= ~(1 << PB3); 
  delayMicroseconds(bar_duration*1.2);
}


void loop()
{
  // Header
  header();
  // guarded_pulser(levels[3]);
  // analogWrite(ledPin, 255);
  // delayMicroseconds(2000);
  // Iterate through each bit in the packet
  // for (int i = 0; i < 4; i += 1)
  // {
  //   int symbol = random(0, 4);
  //   // Check if the current bit is 1 or 0

  //   analogWrite(ledPin, levels[symbol]); // Level 4
  //   delayMicroseconds(1000);
  // }
  //Things to consider:
  //Impossible to recover 0s that occur before and after the header. THe only way to recover these is to know how many pulses per packet , then detect the sent pulses, compare and go from there
  //Note that if a signal due to randomisation if it is full off, then the LED will literally turn off and no signal will be received.
  // for (int i = 3; i >= 0; i -= 1)
  // {
  //   // analogWrite(ledPin,levels[i]);
  //   // analogWrite(ledPin, levels[i]);
  //   // delayMicroseconds(t_shutter);
  //   // Check if the current bit is 1 or 0
  //   guarded_pulser(levels[i]);
    
  // }
  // for (int i = 3; i >= 0; i -= 1)
  // {
  //   // analogWrite(ledPin,levels[i]);
  //   // analogWrite(ledPin, levels[i]);
  //   // delayMicroseconds(t_shutter);
  //   // Check if the current bit is 1 or 0
  //   guarded_pulser(levels[i]);
    
  // }
  // pulser(levels[1]);
  // pulser(levels[2]);
  // pulser(levels[1]);
  // guarded_pulser(levels[0]);
  
  guarded_pulser(levels[1]);
  guarded_pulser(levels[2]);
  guarded_pulser(levels[1]);
  guarded_pulser(levels[1]);
  guarded_pulser(levels[2]);
  guarded_pulser(levels[1]);

  // guarded_pulser(levels[1]);
}

// Repeat the packet after one full cycle
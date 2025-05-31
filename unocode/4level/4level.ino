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

//works on 1/1000 and slightly slower (1/800~)

constexpr uint8_t levels[] = {0 ,40, 140, 255};
constexpr uint16_t t_shutter = 50; // do not change unless you know what ur doing
constexpr uint16_t bar_duration =300; 
//Lower bar duration, higher chance the whole packets going to get turned into mush by exposure averaging
//Higher bar duration, higher chance the whole packets going to appear very flickery in the camera (but its fine, always prefer longer bar duration over shorter , makes the pulses have better pulse shape by giving it more time to form) 
constexpr uint16_t guard_duration = 200; //tune 
//200 working


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
    PORTB &= ~(1 << PB3);  
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

 inline static uint16_t adaptive_guard(uint8_t current, uint8_t previous) {
  uint8_t diff = abs(current - previous);
  return map(diff, 0, 255, guard_duration, guard_duration * 3);
}



static void inline guarded_pulser(uint8_t p,uint8_t previousp,uint8_t nextp){

  //If previous symbol is weak or if the next symbol is weak and the current symbol is strong
  if( (previousp < levels[2] || nextp <levels[2]) && p >= levels[2]){
    PORTB &= ~(1 << PB3); 
  delayMicroseconds(guard_duration*3);
  pulser(p);
  PORTB &= ~(1 << PB3); 
  delayMicroseconds(guard_duration*3);
  //increase barrier distance
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
}
// static void inline guarded_pulser(uint8_t p){
//   uint16_t g_time = adaptive_guard(p, prev_pulse);
//   PORTB &= ~(1 << PB3); 
//   delayMicroseconds(g_time);
//   pulser(p);
//   PORTB &= ~(1 << PB3); 
//   delayMicroseconds(g_time);
//   prev_pulse = p;
// }

static void inline header(){
  PORTB &= ~(1 << PB3); 
  delayMicroseconds(1000);
  PORTB |= (1 << PB3); 
  delayMicroseconds(5); 
  PORTB &= ~(1 << PB3); 
  delayMicroseconds(1000);
  // PORTB &= ~(1 << PB3); 
  // delayMicroseconds(2000);
}


void loop()
{
  // Header
  header();
  guarded_pulser(levels[3],levels[0],levels[2]);
  guarded_pulser(levels[2],levels[3],levels[1]);
  guarded_pulser(levels[1],levels[2],levels[0]);
  guarded_pulser(levels[0],levels[1],levels[0]);
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
  // uint8_t prev_pulse = 0; 
  // uint8_t next_pulse = levels[random(1,4)];
  // uint8_t current_pulse = levels[random(1,4)];
  
  // for (int i = 1; i >= 0; i -= 1)
  // {
    
    // guarded_pulser(current_pulse,prev_pulse,next_pulse);
    // prev_pulse = current_pulse;
    // next_pulse = levels[random(1,4)];
    // current_pulse = levels[random(1,4)];
  // }
  // guarded_pulser(current_pulse,prev_pulse,0);
  //ISI tests
  // guarded_pulser(levels[3],levels[0],levels[1]);
  // guarded_pulser(levels[1],levels[3],levels[3]);
  // guarded_pulser(levels[3],levels[1],levels[0]);
  // guarded_pulser(levels[1],levels[0],levels[3]);
  // guarded_pulser(levels[3],levels[1],levels[1]);
  // guarded_pulser(levels[1],levels[3],levels[0]);
  // guarded_pulser(levels[2],levels[0],levels[1]);
  // guarded_pulser(levels[1],levels[2],levels[2]);
  // guarded_pulser(levels[2],levels[1],levels[0]);
}

// Repeat the packet after one full cycle
#include "TargetDriver/EventBuffer.h"
#include "TargetDriver/RawEvent.h"
#include <vector>

//typedef std::vector<CTA::TargetDriver::RawEvent*>::iterator buf_it;

uint8_t* data;
CTA::TargetDriver::EventBuffer* buffer;

void write_some(uint32_t& evid, int nev, int npacket, int size)
{
  std::cout << "writing " << nev << std::endl;
  for (int i=0; i<nev; ++i) {
    evid++;
    for (uint16_t packetID = 0; packetID < npacket; ++packetID) {
      buffer->AddNewPacket(data, evid, packetID, size);
      //      buffer.DiagnosticReport(std::cout);
    }
  }
}


int read_all()
{
  int n=0;
  while (CTA::TargetDriver::RawEvent* event = 
	 buffer->ReadEvent()) {
    uint32_t ev_id = event->GetEventHeader().GetEventID();
    std::cout << buffer->GetReadIndex() << " " << ev_id << std::endl;
    ++n;
  }
  return n;
}


int main(int argc, char** argv) {

  const uint16_t kNPacketsPerEvent = 4; // 64 // 256
  const uint16_t kPacketSize = 2084;  // 8 waveforms with a 128-ns length
  const uint32_t kBufferDepth = 20;

  // this is the minimum value that does not make any errors on Akira's Mac
  // (Core i7 2.8 GHz + 16 GB 1600 MHz DDR3 memory) when kBufferDepth is 100
  // So EventBuffer::AddNewPacket can run at a trigger rate of up to ~2.5 kHz
  const double kTimeoutSec = 0.0004;

  CTA::TargetDriver::RawEvent::SetTimeoutSec(kTimeoutSec);

  buffer = new CTA::TargetDriver::EventBuffer(kBufferDepth, kNPacketsPerEvent,
					      kPacketSize);
  data = new uint8_t[kPacketSize];

  // 1) Standard case
  uint32_t eventID = 0;

  // for (; eventID < kBufferDepth * 21 / 10; ++eventID) {
  //   uint32_t i = eventID;
  //   write_some(i, 1, kNPacketsPerEvent,kPacketSize);
  //   auto event = buffer->ReadEvent();
  //   uint32_t ev_id = event->GetEventHeader().GetEventID();
  //   int filled = event->GetEventHeader().GetNPacketsFilled();
  //   std::cout << buffer->GetWriteIndex() << " " << buffer->GetReadIndex() 
  // 	      << " " << eventID % kBufferDepth << " " << eventID 
  // 	      << " " << ev_id << " " << filled << std::endl;
  // }

  buffer->DiagnosticReport(std::cout);

  // 2) Overfill buffer
  std::cout << "Overfill test" << std::endl;
  eventID = 0;
  write_some(eventID, kBufferDepth * 11 / 10, kNPacketsPerEvent,kPacketSize);
  //write_some(eventID, 6, kNPacketsPerEvent,kPacketSize);
  read_all();
 
  std::cout << "w> " << buffer->GetWriteIndex() << " r> " << buffer->GetReadIndex() << std::endl;
  buffer->DiagnosticReport(std::cout);

  // 2) Overfill buffer v2
  std::cout << "Overfill test 2" << std::endl;
  write_some(eventID, kBufferDepth * 5 / 10, kNPacketsPerEvent,kPacketSize);
  std::cout << "read index " << buffer->GetReadIndex() << std::endl;
  int nr = read_all();

  std::cout << "w> " << buffer->GetWriteIndex() << " r> " << buffer->GetReadIndex() << std::endl;
  buffer->DiagnosticReport(std::cout);

  std::cout << "read " << nr << " Second block " << buffer->GetReadIndex() << std::endl;
  write_some(eventID, kBufferDepth * 11 / 10, kNPacketsPerEvent,kPacketSize);
  nr = read_all();
  std::cout << "read " << nr << std::endl;

}

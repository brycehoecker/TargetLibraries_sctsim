#include "TargetDriver/EventBuffer_v2.h"
#include "TargetDriver/RawEvent_v2.h"
#include "TargetDriver/DataListener_v2.h"
#include "TargetIO/EventFileWriter_v2.h"
#include <iostream>
#include <thread>
#include <unistd.h>
#include <csignal>
#include <string>
#include <sys/time.h>

// Quick hack, define camera structure statically

//#define TM_PIXELS_PER_MODULE 64
int TM_PIXELS_PER_PACKET=8;   //That is for normal UDP packets (no jumbo frames)
int TM_MODULES_AVAILABLE=32;
int TM_PACKET_SIZE=2084;
std::string DL_CLIENT_IP;
#define TM_PACKETS_PER_EVENT (TM_MODULES_AVAILABLE*TM_PIXELS_PER_MODULE/TM_PIXELS_PER_PACKET)

#define DL_BUILD_TIMEOUT 200
#define DL_CHECK_FREQ 0
int DL_BUFFER_DEPTH=1024;

#define GINFO std::cout
#define GERROR std::cerr


std::shared_ptr<CTA::TargetDriver::EventBuffer_v2> fEventBuffer;
std::thread fWatchThread;
bool fWatching=false;
useconds_t fWatchSleep_us=100;
uint64_t read_events=0;

uint64_t getTimeStamp(void) {
  timespec ts;
  clock_gettime(CLOCK_REALTIME, &ts);
  return (static_cast<uint64_t>(ts.tv_sec))*1000000000+(static_cast<uint64_t>(ts.tv_nsec));
}

int64_t StatsEventCount=0;
int64_t StatsPackCount=0;
int64_t StatsTimes=0;

void WatchBufferMain() {
  fWatching=true;
  GINFO << "Starting WatchBufferMain()" << std::endl;
  CTA::TargetDriver::RawEvent_v2* event;
  while (fWatching) {
    uint32_t nevents = 0;
    event=fEventBuffer->ReadEvent();
    //    while (auto event = fEventBuffer->ReadEvent()) {
    while (NULL!=event) {
      ++nevents;
      event->SetToRead();
      event=fEventBuffer->ReadEvent();
      fEventBuffer->ClearProcessedEvents();
    }
    read_events+=nevents;
    fEventBuffer->ClearProcessedDataPackets();
    usleep(fWatchSleep_us);
  }
  GINFO << "Exiting WatchBufferMain()" << std::endl;
}


void StartWatchBuffer(std::shared_ptr<CTA::TargetDriver::EventBuffer_v2> pEventBuffer){
  fEventBuffer=pEventBuffer;
  fWatchThread = std::thread(&WatchBufferMain);
}

void StopWatchBuffer() {
  fWatching=false;
  if (fWatchThread.joinable()) { fWatchThread.join(); }
  else { GINFO << "Not Joinable" << std::endl; }
}

CTA::TargetDriver::DataListener_v2* fDataListener=NULL;

bool SetUpListener () {
  if (fDataListener != NULL) {
    GINFO << "Deleting existing DataListener" << std::endl;
    delete fDataListener;
  }
  fDataListener = new CTA::TargetDriver::DataListener_v2(DL_BUFFER_DEPTH, TM_PACKETS_PER_EVENT,TM_PACKET_SIZE,DL_BUILD_TIMEOUT,DL_CHECK_FREQ);
  
  if (fDataListener->AddDAQListener(DL_CLIENT_IP) != TC_OK) {
    GERROR << "Could not connect listener at IP " << DL_CLIENT_IP;
    return false;
  } else {
    GINFO << "Adding DAQ listener at IP " << DL_CLIENT_IP << std::endl;
  }
  return true;
}

bool DeleteListener () {
  if (fDataListener != NULL) {
    GINFO << "Deleting existing DataListener" << std::endl;
    delete fDataListener;
  }
  return true;
}

bool fExitSignal=false;

void signal_handler( int signal_num ) { 
  GINFO << "Captured interrupt signal" << std::endl;
  fExitSignal=true;
} 
  

int main(int argc, char** argv) {
  bool retval;

  if (argc >= 6) { DL_BUFFER_DEPTH=atoi(argv[5]); }
  if (argc >= 5) { TM_PACKET_SIZE=atoi(argv[4]); }
  if (argc >= 4) { TM_PIXELS_PER_PACKET=atoi(argv[3]); }
  if (argc >= 3) { TM_MODULES_AVAILABLE=atoi(argv[2]); }
  if (argc >= 2) { DL_CLIENT_IP = std::string(argv[1]); }
  else {
    std::cout << "Usage: CHECDataListener own_ip [module_count [pixels_per_packet [packet_size [buffer_depth]]]] \n"
              << "  module_count: 32 (default)\n"
              << "  pixels_per_packet: 8 (default)\n"
              << "  packet_size: 2084 (default)\n"
              << "  buffer_depth : 1024 (default)\n"
              << std::endl;
    return -1;
  }
  
  std::cout << "Starting CHECDataListener" << std::endl
            << " own_ip: " << DL_CLIENT_IP << std::endl
            << " module_count: " << TM_MODULES_AVAILABLE << std::endl
            << " pixels_per_packet: " << TM_PIXELS_PER_PACKET << std::endl
            << " packet_size: " << TM_PACKET_SIZE << std::endl
            << " buffer_depth: " << DL_BUFFER_DEPTH << std::endl;


  signal(SIGINT,signal_handler);  
  retval=SetUpListener();
  StartWatchBuffer(fDataListener->GetEventBuffer());
  GINFO << std::endl << std::endl;
  GINFO << "Start listening for data packets" << std::endl;
  fDataListener->StartListening();

  while (!fExitSignal) {
    usleep(1000000);
    fDataListener->GetEventBuffer()->GetEventRate();
    fDataListener->GetEventBuffer()->Report(GINFO);

   }
  GINFO << "Stop Listening" << std::endl;
  fDataListener->StopListening();
  GINFO << "Flush EventBuffer" << std::endl;
  fDataListener->GetEventBuffer()->Flush();
  GINFO << "Stop Watching" << std::endl;
  StopWatchBuffer();
  GINFO << "Delete Listener" << std::endl;
  DeleteListener();
  return retval;
}

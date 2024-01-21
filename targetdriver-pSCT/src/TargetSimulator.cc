#include <iostream>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>

#include "TargetDriver/TargetSimulator.h"

using namespace CTA::TARGET;

TargetSimulator::TargetSimulator(const char *hostname) {
  ClearRegisters();
  fMyIP = hostname;
  fDataSocket = -1;
  fSCSocket = -1;
  fVerbose = false;
  memset(&fClientAddress, 0, sizeof(fClientAddress));
}

TargetSimulator::~TargetSimulator() { CloseSockets(); }

void TargetSimulator::CloseSockets() {
  if (fDataSocket > 0) close(fDataSocket);
  if (fSCSocket > 0) close(fSCSocket);
}

void TargetSimulator::ClearRegisters() {
  memset(fRegisters, 0, sizeof(uint32_t) * TM_NUM_REGISTERS);
}

bool TargetSimulator::SendData(uint8_t* data, uint32_t len) {

  if (fClientAddress.sin_addr.s_addr == 0) {
    std::cout << "TargetSimulator::SendData() - Not contacted yet - cannot send data" << std::endl;
    return false;
  }

  int sockfd = fDataSocket;
  if (sockfd < 1) {
    sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    struct sockaddr_in servaddr;
    bzero(&servaddr, sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = inet_addr(fMyIP);
    // OR htonl(INADDR_ANY); // listen to anyone
    servaddr.sin_port = htons(TM_DEST_PORT);
    bind(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr));
    fDataSocket = sockfd;
  }
  fClientAddress.sin_port = htons(TM_DAQ_PORT);

  // if (len == 0 || data == 0) {
  //   const uint32_t dlen = 1000;
  //   uint8_t data[dlen];
  //   memset(data, 0, dlen);
  //   data[0] = 77;
  //   data[1] = 88;
  // }
  int n = sendto(sockfd, data, len, 0, (struct sockaddr *)&fClientAddress,
                 sizeof(fClientAddress));

  if (fVerbose) std::cout << "TargetSimulator::SendData() - data sent" << std::endl;

  return (n == len);
}

void TargetSimulator::ListenAndRespond() {
  
  int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
  struct sockaddr_in servaddr;
  bzero(&servaddr, sizeof(servaddr));
  servaddr.sin_family = AF_INET;
  servaddr.sin_addr.s_addr = inet_addr(fMyIP);
  // OR htonl(INADDR_ANY); // listen to anyone
  servaddr.sin_port = htons(TM_DEST_PORT);
  bind(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr));

  for (;;) {
    socklen_t len = sizeof(fClientAddress);
    uint8_t mesg[100]; // allow for somewhat larger than expected packets
    uint32_t n = recvfrom(sockfd, mesg, 100, 0,
                          (struct sockaddr *)&fClientAddress, &len);

    if (fVerbose) std::cout << "received number of bytes " << n << std::endl;

    if (n == TM_CONTROLPACKET_BYTES) {
      uint32_t addr, data;
      bool iswrite;

      TargetModuleComms::UnpackPacket(mesg, addr, data, iswrite);
      if (iswrite) {
        if (fVerbose)
          std::cout << "TargetSimulator::ListenAndRespond() - Writing: "
		    << data << " to addr: " << addr << std::endl;
        if (addr <= TM_NUM_REGISTERS) fRegisters[addr] = data;
      } else {
        if (addr <= TM_NUM_REGISTERS) {
          data = fRegisters[addr];
          if (fVerbose)
            std::cout << "TargetSimulator::ListenAndRespond() - Read: "
		      << data << " from addr: " << addr
                      << std::endl;
        } else {
          data = 0;
          std::cout << "TargetSimulator::ListenAndRespond() - Request for address out of range" << std::endl;
        }
      }
      // Send response
      TargetModuleComms::PackPacket(mesg, addr, data, false);
      sendto(sockfd, mesg, TM_CONTROLPACKET_BYTES, 0,
             (struct sockaddr *)&fClientAddress, sizeof(fClientAddress));
    } else {
      std::cout << "TargetSimulator::ListenAndRespond() - Wrong packet size: " << n << std::endl;
    }
  }
}

////////

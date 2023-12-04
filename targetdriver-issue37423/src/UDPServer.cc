// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include "TargetDriver/UDPServer.h"

#include <arpa/inet.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <iostream>

namespace CTA {
namespace TargetDriver {

UDPServer::UDPServer(const std::string& pMyIP,
                     uint16_t pSlowControlListeningPort, uint16_t pDataDestPort,
                     uint32_t receive_timout_ms) {
  memset(&fSenderAddress, 0, sizeof(fSenderAddress));

  Setup(pMyIP, pSlowControlListeningPort, pDataDestPort, receive_timout_ms);
}

int UDPServer::Setup(const std::string& pMyIP,
                     uint16_t pSlowControlListeningPort, uint16_t pDataDestPort,
                     uint32_t receive_timout_ms) {
  fSocket = socket(AF_INET, SOCK_DGRAM, 0);
  struct sockaddr_in servaddr;
  memset(&servaddr, 0, sizeof(servaddr));
  servaddr.sin_family = AF_INET;
  servaddr.sin_addr.s_addr = inet_addr(pMyIP.c_str());
  servaddr.sin_port = htons(pSlowControlListeningPort);
  int stat = bind(fSocket, (struct sockaddr*)&servaddr, sizeof(servaddr));

  // TODO(Harm): Add error message
  if (stat != 0) return TC_ERR_COMM_FAILURE;

  fDataDestPort = pDataDestPort;
  fReceiveTimeoutMs = receive_timout_ms;

  if (fVerbose) {
    std::cout << "UDPServer set up to listen on port "
              << pSlowControlListeningPort << std::endl;
  }
  return TC_OK;
}

int UDPServer::Send(const void* data, uint32_t length, int socket,
                    uint16_t pDestPort) {
  if (fSenderAddress.sin_addr.s_addr == 0) {
    return TC_ERR_USER_ERROR;  // not contacted yet
  }

  fSenderAddress.sin_port = htons(pDestPort);

  ssize_t n = sendto(socket, data, length, 0, (struct sockaddr*)&fSenderAddress,
                     sizeof(fSenderAddress));

  if (fVerbose) {
    std::cout << " UDPServer::Send - sent " << n << " bytes " << std::endl;
  }

  if (n != (int64_t)length) {
    return TC_ERR_COMM_FAILURE;
  }

  return TC_OK;
}

int UDPServer::SendDataPacket(const void* data, uint32_t length) {
  return Send(data, length, fSocket, fDataDestPort);
}

int UDPServer::SendResponse(const void* data, uint32_t length) {
  return Send(data, length, fSocket, fReceivedFromPort);
}

}  // namespace TargetDriver
}  // namespace CTA

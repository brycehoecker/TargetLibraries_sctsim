// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include "TargetDriver/UDPBase.h"

#include <iostream>

namespace CTA {
namespace TargetDriver {

UDPBase::UDPBase()
    : fVerbose(false),
      fSocket(-1),
      fReceiveTimeoutMs(100),  // ms
      fReceivedFromPort(0)
{
  memset(&fSenderAddress, 0, sizeof(fSenderAddress));
}

std::string UDPBase::ReturnCodeToString(int code) {
  switch (code) {
    case TC_TIME_OUT:
      return "Normal / or potentially normal timeout (e.g. listening for data)";
    case TC_UNEXPECTED_RESPONSE:
      return "Information contained in the packet received was unexpected";
    case TC_ERR_BAD_PACKET:
      return "Packet that was received was inconsistent with protocol "
             "expectations";
    case TC_ERR_NO_RESPONSE:
      return "No response from Server";
    case TC_OK:
      return "Success";
    case TC_ERR_COMM_FAILURE:
      return "Total failure of communication";
    case TC_ERR_CONF_FAILURE:
      return "Failure in configuration";
    case TC_ERR_USER_ERROR:
      return "In appropriate use of the class";
  }
  return "Unknown return code";
}

void UDPBase::CloseSocket() {
  if (fSocket > -1) {
    if (fVerbose) {
      std::cout << "Closing socket" << std::endl;
    }
    close(fSocket);
    fSocket = -1;
  }
}

int UDPBase::Receive(void* message, ssize_t& length, uint32_t max_length) {
  length = 0;

  fd_set fds;
  FD_ZERO(&fds);
  FD_SET(fSocket, &fds);

  struct timeval tv;
  tv.tv_sec = 0;
  tv.tv_usec = static_cast<int>(1000 * fReceiveTimeoutMs);

  int nselect = select(fSocket + 1, &fds, NULL, NULL, &tv);
  if (nselect == 0) {
    return TC_TIME_OUT;
  }

  if (!FD_ISSET(fSocket, &fds)) {
    return TC_ERR_COMM_FAILURE;  // Cannot receive a packet from the socket
  }

  socklen_t len = sizeof(fSenderAddress);
  length = recvfrom(fSocket, message, max_length, 0,
                    (struct sockaddr*)&fSenderAddress, &len);

  fReceivedFromPort = ntohs(fSenderAddress.sin_port);

  if (fVerbose) {
    std::cout << "UDPBase::Receive - received " << length << " bytes from port "
              << fReceivedFromPort << std::endl;
  }

  if (length < 1) {
    return TC_ERR_COMM_FAILURE;
  }

  return TC_OK;
}

}  // namespace TargetDriver
}  // namespace CTA

// Copyright (c) 2015 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains the client part of the target communications
 */
#ifndef INCLUDE_TARGETDRIVER_UDPSERVER_H_
#define INCLUDE_TARGETDRIVER_UDPSERVER_H_

#include <TargetDriver/UDPBase.h>
#include <string>

namespace CTA {
namespace TargetDriver {

/*!
 * @class UDPServer
 * @brief This class provides the server side of the functionality for UDP
 *packet based communication (see UDPBase.h)
 *
 * TODO:
 *       Improve documentation
 *       Review
 *
 */
class UDPServer : public UDPBase {
 public:
  UDPServer(const std::string& pMyIP, uint16_t pSlowControlListeningPort,
            uint16_t pDataDestPort, uint32_t receive_timout_ms = 100);
  virtual ~UDPServer() {}

  /// Respond to a message from the client
  int SendResponse(const void* data, uint32_t length);

  /// Send a data packet to the last IP to send me a message
  int SendDataPacket(const void* data, uint32_t length);

  /// Initialise or reinitialise (after calling EndCommunications)
  int Setup(const std::string& pMyIP, uint16_t pSlowControlListeningPort,
            uint16_t pDataDestPort, uint32_t receive_timout_ms);

 private:
  int Send(
      const void* data, uint32_t length, int socket,
      uint16_t pDestPort);  /// low level function for sending a single packet

  uint16_t fDataDestPort;  // port number to be used to send data to
};

}  // namespace TargetDriver
}  // namespace CTA
#endif  // INCLUDE_TARGETDRIVER_UDPSERVER_H_

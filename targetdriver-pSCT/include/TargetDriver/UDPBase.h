// Copyright (c) 2015 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains base target module communication class
 */
#ifndef INCLUDE_TARGETDRIVER_UDPBASE_H_
#define INCLUDE_TARGETDRIVER_UDPBASE_H_

// clang-format off
#define TC_TIME_OUT               4  //< Normal / or potentially normal timeout (e.g. listening for data) NOLINT
#define TC_UNEXPECTED_RESPONSE    3  //< Information contained in the packet received was unexpected NOLINT
#define TC_ERR_BAD_PACKET         2  //< Packet received inconsistent with protocol expectations NOLINT
#define TC_ERR_NO_RESPONSE        1  //< No response from Server
#define TC_OK                    0  //< Success
#define TC_ERR_COMM_FAILURE     -1  //< Fix your IP etc configuration
#define TC_ERR_CONF_FAILURE     -2  //< Fix your Settings configuration
#define TC_ERR_USER_ERROR       -3  //< Fix your code
// clang-format on

#include <netinet/in.h>
#include <unistd.h>
#include <string.h>
#include <string>

namespace CTA {
namespace TargetDriver {

/*!
 * @class UDPBase
 * @brief Base class for communications based on UDP and the idea of a message
 *response system plus data packets that can be pushed from server to client.
 *The UDPServer and UDPClient classes implement this relationship.
 *
 * TODO:
 *       Review
 */

class UDPBase {
 public:
  UDPBase();
  virtual ~UDPBase() { CloseSocket(); }

  /// Listen for / try to receive a message from the client
  int Receive(void* message, ssize_t& length,  // NOLINT(runtime/references)
              uint32_t max_length);

  /// Closes socket
  void CloseSocket();

  /// Translates the integer return codes used by UDPBase to explainatory
  /// strings
  std::string ReturnCodeToString(int code);

  void SetVerbose(bool verbose = true) { fVerbose = verbose; };

 protected:
  bool fVerbose;  ///<! Flag to activate std output for debugging

  int fSocket;  ///<! File descriptor of the socket used for slow control
                /// messaging and DAQ
  uint32_t fReceiveTimeoutMs;  ///<! How long to wait in ms before returning a
  /// timeout code in Receive()
  struct sockaddr_in fSenderAddress;  ///<! The address of the last process to
  // contact us via slow control
  uint16_t fReceivedFromPort;  //<! The port of the last process to contact us
  // via slow control

  // TODO: SHOULD ADD A VERBOSE FLAG - rather than a hash define - to debug one
  // - rather than all - connections
};

}  // namespace TargetDriver
}  // namespace CTA

#endif  // INCLUDE_TARGETDRIVER_UDPBASE_H_

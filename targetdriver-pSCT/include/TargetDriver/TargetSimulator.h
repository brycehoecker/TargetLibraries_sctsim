/*! \file */
/*!
 @file
 @brief Contains TargetSimulation class
 * 
*/

#ifndef CTA_TARGET_SIMULATOR_H_
#define CTA_TARGET_SIMULATOR_H_

#include <sys/socket.h>
#include <netinet/in.h>

#include "TargetModuleComms.h"

namespace CTA {
namespace TARGET {
/*!
 * @class TargetSimulator
 * @brief This is the class for simulating a target module via UDP packet
 *exchange
 *
 *
 */
class TargetSimulator {
  /*! \brief This is the class for simulating a target module via UDP packet
   *exchange
   * It will be well documented and written in simple C++.
   *
   * more detailed stuff should go here...
   */

 public:
  TargetSimulator(const char* hostip = "127.0.0.1");
  ~TargetSimulator();
  ///
  /// Set all the local register values to zero
  void ClearRegisters();
  ///
  /// Transmit a data packet -- define packet formats etc elsewhere (e.g. T5DataPacket)
  bool SendData(uint8_t* data, uint32_t len);
  ///
  /// Listen for slow control (read/write register) commands and respond to them
  void ListenAndRespond();
  ///
  /// Wrapper around ListenAndRespond for pthread use
  static void* listener(void* context) {
    ((TargetSimulator*)context)->ListenAndRespond();
    return NULL;
  }
  ///
  /// Close the sockets used for data and slow control
  void CloseSockets();
  void SetVerbose(bool verbose) { fVerbose = verbose; }

 private:
  std::string
      fStatusString;    ///<! holds info about the current status of the COMMS
  //Not used yet Harm
  //int fStatusFlag;      ///<! holds the current status
  bool fVerbose;        ///<! print debugging info if true
  int32_t fDataSocket;  ///<! File descriptor of a Slow Control socket
  int32_t fSCSocket;    ///<! File descriptor of the Data socket
  uint32_t fRegisters[TM_NUM_REGISTERS];
  struct sockaddr_in fClientAddress;  ///<! The address of the last person to
                                      //contact us via slow control - used for
                                      //the data sending
  const char* fMyIP;  ///<! ip address string of the TargetSimulator
};

}  // TARGET
}  // CTA
#endif  // CTA_TARGET_SIMULATOR_H_

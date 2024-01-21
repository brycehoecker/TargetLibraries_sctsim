/*! \file */
#ifndef CTA_TARGET_COMMS_H_
#define CTA_TARGET_COMMS_H_

#include "TargetModule.h"

#include <poll.h>
#include <iostream>
#include <string>
#include <vector>

//Defaults and port number definitions
#define TM_DEST_PORT          8105 ///< Default port which the TMs listen on
#define TM_SOURCE_PORT        8200 ///< Arbitary: +0-31 port from which we send TM commands - and to which the responses come
#define TM_DAQ_PORT           8107 //< Arbitary: port to which data is set from TM

//#define TM_SOCK_BUF_SIZE_SC   100000 ///< Default socket buffer size for slow control
//#define TM_SOCK_BUF_SIZE_DAQ  999424 ///< TRY LARGER
//#define TM_SOCK_BUF_SIZE_DAQ  124928 ///< Default socket buffer size for DAQ -- see /proc/sys/net/core/rmem_max for the max allowed value (often 124928)
//#define TM_MAX_ATTEMPTS       5 ///< Default number of maximum attemps for register operations (read/write)
//#define TM_RESPONSE_TIME_OUT  200000 //<Default number of micro seconds for receive time out
//#define TM_DAQ_TIME_OUT       20 //<Default number of milliseconds -- how long does the poll in GetDataPacket wait before giving up
#define TM_CONTROLPACKET_BYTES 16

#define TM_NUM_REGISTERS     82 //<Highest usable register for Target Modules
#define TM_NUM_ASIC_REGISTERS     64 //<Highest usable register for Target ASICs
// Status flag definitions
#define TM_DATA_TIMEOUT          3 //< Normal timeout listening for data
#define TM_COMM_WRONGRESPONSESIZE  2 //< Wrong size of packet received from TM
#define TM_COMM_NORESPONSE       1 //< This TM is not talking to us
#define TM_OK                    0
#define TM_COMM_FAILURE         -1 //< Fix your configuration
#define TM_USER_ERROR           -2 //< Fix your code

/*!
 * @class TargetModuleComms
 * @brief This class defines the base communication with TARGET modules.
 *
 * TODO:
 *       Documenting.
 *       Review
 *
 */

namespace CTA {
namespace TARGET {

class TargetModuleComms {
 public:
  TargetModuleComms();

  ///
  /// Print the internal status flag and string to stream os
  void PrintStatus(std::ostream &os=std::cout);
  ///
  /// Enable the two way slow control communication with a Target Module with IP tm_ip from my_ip. tm_number should be unique as it determines the port number that will be used - e.g. 0-31 for a camera
  bool EstablishSlowControlLink(char* my_ip, char* tm_ip, int tm_number=0);
  ///
  /// Opens a socket for receiving Target Module data and keeps it in a list for future listening (via GetDataPacket) - can be called several times to listen on multiple IPs
  bool AddDAQListener(char* my_ip, int32_t socket_buffer_size=TM_SOCK_BUF_SIZE_DAQ);
  ///
  /// Closes sockets for both slow control and DAQ
  void EndCommunications();
  ///
  /// Reads a register on the TARGET Module FPGA - makes fMaxAttempts attempts ------ TODO: change type to bool, get value by reference
  // could add higher level functions which try multiple times to read or write
  bool ReadRegister(uint32_t address, uint32_t& data) {
    return RegisterOperation(address, data, false);
  }

  /// Writes the value in data to address on a Target Module - makes fMaxAttempts attempts
  bool WriteRegister(uint32_t address, uint32_t data) {
    return RegisterOperation(address, data, true);
  }
  ///
  /// Writes a Target Register and reads the value back and compares them. Returns true if values are the same
  bool WriteRegisterAndCheck(uint32_t address, uint32_t data);
  ///
  /// Listens on all sockets registered via AddDAQListener for fDAQTimeout ms and returns true if there was data - filling the pointer tobefilled with the data read
  bool GetDataPacket(void* tobefilled, uint32_t &bytes, int maxbytes);

  /// Prepare a slow control packet based on addr and data and the flag iswrite (true if this is a write register command)
  static void PackPacket(uint8_t* packet, uint32_t addr, uint32_t data, bool iswrite);
  ///
  /// Extract the addres, data and iswrite flag from the slow control packet
  static void UnpackPacket(uint8_t* packet, uint32_t &addr, uint32_t &data, bool &iswrite);

protected:
  std::string fStatusString;//<! holds info about the current status of the COMMS
  int fStatusFlag;//<! holds the current status
  uint32_t fMaxAttempts; //<! Number of maximum attemps for register operations
  uint32_t fResponseTimeOut;//<! Needs documenting
  uint32_t fDAQTimeout;//<!Needs documenting

private:
  ///
  /// Used by EstablishSlowControl to establish the slow control connection
  bool OpenConnection(char* source_host, uint16_t source_port, char* dest_host,
                      uint16_t dest_port, int32_t socket_buffer_size);
  ///
  /// Lowest level function to receive a slow control packet (a response to a read or write) from the Target Module
  bool Receive(void* buffer, uint64_t lengthm, int64_t& nbytes);
  ///
  /// Makes a single attempt to send a read or write command to a Target Module
  bool SendCommand(uint32_t address, uint32_t data, bool iswrite);

  /// Used by WriteRegister and ReadRegister to make fMaxAttempts to send a command packet to the Target Module
  bool RegisterOperation(uint32_t address, uint32_t &data, bool iswrite);

  int32_t fSlowControlSocket;                          //<! File descriptor of a socket
  std::vector<pollfd> fDAQPollList; //<! A list of pollfd structs to be used by the poll() call inside GetDataPacket() - the pollfd struct includes the socket file descriptor
};

}  // TARGET
}  // CTA
#endif  // CTA_TARGET_COMMS_H_

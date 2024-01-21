#include "TargetDriver/TargetModuleComms.h"

#include <arpa/inet.h>
#include <string.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/time.h>
#include <stdio.h>

namespace CTA {
namespace TARGET {
/*
 std::string fStatusString;//<! holds info about the current status of the COMMS
 int fStatusFlag;//<! holds the current status
 uint32_t fMaxAttempts; //<! Number of maximum attemps for register operations
 uint32_t fResponseTimeOut;//<! Needs documenting
 uint32_t fDAQTimeout;//<!Needs documenting

*/
TargetModuleComms::TargetModuleComms()
  :fMaxAttempts(TM_MAX_ATTEMPTS),
   fResponseTimeOut(TM_RESPONSE_TIME_OUT),
   fDAQTimeout(TM_DAQ_TIME_OUT) ,
   fSlowControlSocket(-1)
       {
  fStatusString = "Constructor called";
  fStatusFlag = TM_OK;
}

void TargetModuleComms::PrintStatus(std::ostream& os) {
  os << "TM Status Flag: " << fStatusFlag << " and String: " << fStatusString
     << std::endl;
}

bool TargetModuleComms::OpenConnection(char* source_host, uint16_t source_port,
                                       char* dest_host, uint16_t dest_port,
                                       int32_t socket_buffer_size) {
  if (fSlowControlSocket != -1) {
    fStatusString = "OpenConnection() failed - Socket is already open.";
    fStatusFlag = TM_USER_ERROR;
    return false;
  }

  fSlowControlSocket = socket(AF_INET, SOCK_DGRAM, 0);

  if (fSlowControlSocket == -1) {
    fStatusFlag = TM_COMM_FAILURE;
    fStatusString = "OpenConnection() Cannot create a new slow control socket.";
    return false;
  }

  if (socket_buffer_size > 0) {
    if (setsockopt(fSlowControlSocket, SOL_SOCKET, SO_RCVBUF,
                   &socket_buffer_size, sizeof(socket_buffer_size)) != 0) {
      fStatusFlag = TM_COMM_FAILURE;
      fStatusString =
          "OpenConnection() Cannot change the slow control socket buffer to "
          "requested size";
      return false;
    }
  }

  struct sockaddr_in sourceSocketAddress;

  memset(&sourceSocketAddress, 0, sizeof(sourceSocketAddress));
  sourceSocketAddress.sin_addr.s_addr = inet_addr(source_host);
  sourceSocketAddress.sin_port = htons(source_port);
  sourceSocketAddress.sin_family = AF_INET;

  int ret = bind(fSlowControlSocket, (struct sockaddr*)&sourceSocketAddress,
                 sizeof(sourceSocketAddress));
  if (ret != 0) {
    fStatusString =
        "OpenConnection() Cannot bind the receive slow control socket to "
        "requested source port";
    fStatusFlag = TM_COMM_NORESPONSE;
    return false;
  }

  struct sockaddr_in destinationSocketAddress;

  memset(&destinationSocketAddress, 0, sizeof(destinationSocketAddress));
  if (std::string(dest_host) != "" && dest_port != 0) {
    destinationSocketAddress.sin_addr.s_addr = inet_addr(dest_host);
    destinationSocketAddress.sin_port = htons(dest_port);
    destinationSocketAddress.sin_family = AF_INET;
  }

  ret = connect(fSlowControlSocket, (struct sockaddr*)&destinationSocketAddress,
                sizeof(destinationSocketAddress));

  if (ret != 0) {
    fStatusString =
        "OpenConnection() Cannot connect the receive slow control socket to "
        "requested source port";
    fStatusFlag = TM_COMM_NORESPONSE;
    return false;
  }

  fStatusString = "OpenConnection() succeeded - Read/Write can be used";
  fStatusFlag = TM_OK;
  return true;
}

bool TargetModuleComms::Receive(void* buffer, uint64_t length, int64_t& nbytes) {
  fd_set fds;
  FD_ZERO(&fds);
  FD_SET(fSlowControlSocket, &fds);

  struct timeval tv;
  tv.tv_sec = 0;
  tv.tv_usec = fResponseTimeOut;

  int nselect = select(fSlowControlSocket + 1, &fds, NULL, NULL, &tv);

  if (nselect == 0) {
    return false;
  }

  if (!FD_ISSET(fSlowControlSocket, &fds)) {
    fStatusString =
        "Receive() - Cannot receive a packet from the slow control socket.";
    //  TODO change the status here
    nbytes = -1;
    return false;
  }

  nbytes = recvfrom(fSlowControlSocket, buffer, length, 0, NULL, NULL);

  return true;
}

bool TargetModuleComms::SendCommand(uint32_t address, uint32_t data = 0,
                                    bool iswrite = false) {
  uint8_t bytes[TM_CONTROLPACKET_BYTES];
  memset(bytes, 0, TM_CONTROLPACKET_BYTES);

  if (iswrite) {
    bytes[4] |= 0x40;
  } else {
    bytes[4] &= 0x3F;
  }
  bytes[5] = (address >> 16) & 0xFF;
  bytes[6] = (address >> 8) & 0xFF;
  bytes[7] = (address >> 0) & 0xFF;
  bytes[8] = (data >> 24) & 0xFF;
  bytes[9] = (data >> 16) & 0xFF;
  bytes[10] = (data >> 8) & 0xFF;
  bytes[11] = (data >> 0) & 0xFF;

  int32_t bytes_written =
      write(fSlowControlSocket, bytes, TM_CONTROLPACKET_BYTES);

  if (bytes_written == TM_CONTROLPACKET_BYTES) {
    fStatusString = "SendCommand() succeeded";
    fStatusFlag = TM_OK;
    return true;
  } else {
    fStatusString = "SendCommand() failed";
    fStatusFlag = TM_COMM_FAILURE;
    return false;
  }
}

// PUBLIC

bool TargetModuleComms::EstablishSlowControlLink(char* my_ip, char* tm_ip,
                                                 int tm_number) {
  return OpenConnection(my_ip, TM_SOURCE_PORT + tm_number, tm_ip, TM_DEST_PORT,
                        TM_SOCK_BUF_SIZE_SC);
}

bool TargetModuleComms::AddDAQListener(char* my_ip,
                                       int32_t socket_buffer_size) {
  int32_t sock = socket(AF_INET, SOCK_DGRAM, 0);

  if (sock == -1) {
    fStatusString = "AddDAQListener() Cannot create a new DAQ socket.";
    fStatusFlag = TM_COMM_FAILURE;
    return false;
  }

  if (socket_buffer_size > 0) {
    if (setsockopt(sock, SOL_SOCKET, SO_RCVBUF, &socket_buffer_size,
                   sizeof(socket_buffer_size)) != 0) {
      fStatusString =
          "AddDAQListener() Cannot change the DAQ socket buffer to requested "
          "size";
      fStatusFlag = TM_COMM_FAILURE;
      return false;
    }
  }

  struct sockaddr_in sourceSocketAddress;

  memset(&sourceSocketAddress, 0, sizeof(sourceSocketAddress));
  sourceSocketAddress.sin_addr.s_addr = inet_addr(my_ip);
  sourceSocketAddress.sin_port = htons(TM_DAQ_PORT);
  sourceSocketAddress.sin_family = AF_INET;

  int ret = bind(sock, (struct sockaddr*)&sourceSocketAddress,
                 sizeof(sourceSocketAddress));
  if (ret != 0) {
    fStatusString =
        "AddDAQListener() Cannot bind the receive DAQ socket to requested "
        "source port";
    fStatusFlag = TM_COMM_FAILURE;
    return false;
  }

  struct pollfd poll_in;

  poll_in.fd = sock;
  poll_in.events = POLLIN;
  poll_in.revents = 0;

  fDAQPollList.push_back(poll_in);
  fStatusString = "AddDAQListener() succeeded";
  fStatusFlag = TM_OK;

  return true;
}

void TargetModuleComms::EndCommunications() {
  if (fSlowControlSocket > 0) {
    close(fSlowControlSocket);
    fSlowControlSocket = -1;
  }

  for (unsigned int i = 0; i < fDAQPollList.size(); ++i) {
    close(fDAQPollList[i].fd);
  }

  fDAQPollList.clear();

  fStatusString = "Ended EndCommunications()";
}

bool TargetModuleComms::RegisterOperation(uint32_t address, uint32_t& data,
                                          bool iswrite) {
  uint32_t attempts = 0;
  while (attempts < fMaxAttempts) {
    if (!SendCommand(address, data, iswrite)) return false;

    uint8_t bytes[TM_CONTROLPACKET_BYTES];

    int64_t nbytes = 0;
    Receive(bytes, TM_CONTROLPACKET_BYTES, nbytes); // TODO check the return
    if (nbytes == TM_CONTROLPACKET_BYTES) {
      if (!iswrite) {
        data = ((uint32_t)(bytes[8]) << 24) | ((uint32_t)(bytes[9]) << 16) |
               ((uint32_t)(bytes[10]) << 8) | ((uint32_t)(bytes[11]) << 0);
      }
      fStatusString = "RegisterOperation() succeeded";
      fStatusFlag = TM_OK;
      return true;
    } else if (nbytes <= 0) {  //// Two ways to fail
      fStatusString = "RegisterOperation() - no valid response";
      fStatusFlag = TM_COMM_FAILURE;
      return false;
    } else {
      /// */!CheckPacket(bytes)) {
      fStatusString = "ReadRegister() - malformed response packet";
      fStatusFlag = TM_COMM_WRONGRESPONSESIZE;
      return false;
    }
    // no response -- try again
  }

  return true;
}

bool TargetModuleComms::WriteRegisterAndCheck(uint32_t address, uint32_t data) {
  if (WriteRegister(address, data)) {
    uint32_t data_read;
    ReadRegister(address, data_read);  // TODO check return value
    if (data_read == data) {
      fStatusString = "WriteRegisterAndCheck() - succeeded";
      fStatusFlag = TM_OK;
      return true;
    }
  }
  return false;
}

bool TargetModuleComms::GetDataPacket(void* tobefilled, uint32_t& bytes,
                                      int maxbytes) {
  bytes = 0;
  // Poll multiple sockets for incoming data
  int rc = poll(&fDAQPollList[0], fDAQPollList.size(), fDAQTimeout);

  if (rc < 0) {
    fStatusString = "Poll failed in GetDataPacket()";
    fStatusFlag = TM_COMM_FAILURE;
    return false;
  } else if (rc == 0) {  // Timeout
    // set string or not????
    fStatusFlag = TM_DATA_TIMEOUT;
    return false;
  }

  // Return data of the first socket which has data available
  for (unsigned int i = 0; i < fDAQPollList.size(); ++i) {
    if (fDAQPollList[i].revents & POLLIN) {
      bytes = recvfrom(fDAQPollList[i].fd, tobefilled, maxbytes, 0, NULL, NULL);
      if (bytes > 0) {
        // set string or not???
        fStatusFlag = TM_OK;
        return true;
      }
    }
  }

  fStatusString = "Strange Poll behaviour in GetDataPacket()";
  fStatusFlag = TM_COMM_FAILURE;
  return false;
}

void TargetModuleComms::PackPacket(uint8_t* bytes, uint32_t address,
                                   uint32_t data, bool iswrite) {
  memset(bytes, 0, TM_CONTROLPACKET_BYTES);

  if (iswrite) {
    bytes[4] |= 0x40;
  } else {
    bytes[4] &= 0x3F;
  }
  bytes[5] = (address >> 16) & 0xFF;
  bytes[6] = (address >> 8) & 0xFF;
  bytes[7] = (address >> 0) & 0xFF;
  bytes[8] = (data >> 24) & 0xFF;
  bytes[9] = (data >> 16) & 0xFF;
  bytes[10] = (data >> 8) & 0xFF;
  bytes[11] = (data >> 0) & 0xFF;
}

void TargetModuleComms::UnpackPacket(uint8_t* bytes, uint32_t& addr,
                                     uint32_t& data, bool& iswrite) {
  iswrite = ((bytes[4] & 0x40) != 0);

  data = ((uint32_t)(bytes[8]) << 24) | ((uint32_t)(bytes[9]) << 16) |
         ((uint32_t)(bytes[10]) << 8) | ((uint32_t)(bytes[11]) << 0);

  addr = ((uint32_t)(bytes[5]) << 16) | ((uint32_t)(bytes[6]) << 8) |
         ((uint32_t)(bytes[7]) << 0);
}

//// bool TargetModuleComms::GetDataPacket(T5CameraDataPacket *p, int
///&packet_id, int &event_id) {

// need to think a bit about exactly how to do this to avoid unncessary copying

// T5CameraDataPacket p;
// p.Assign(fBuffer, fBytesReturned);

// uint16_t nwaveforms = p.GetNumberOfWaveforms();
// uint8_t module_id = p.GetDetectorID();

// event_id = fEventBuffer->GetCurrentEventNumber();

// T5CameraWaveform* w = p.GetWaveform(0);

// if (w && nwaveforms > 0) {
//   uint8_t asic = w->GetASIC();
//   uint8_t chan = w->GetChannel();
//   GDEBUG() << "ADC " << module_id << " " << asic << " " << chan << "   "
//            << w->GetADC(33) << " " << w->GetADC(34) << " " << w->GetADC(35)
//            << " " << w->GetADC(36) << " " << w->GetADC(37) << " "
//            << w->GetADC(38) << " " << w->GetADC(39) << " " << w->GetADC(40)
//            << " " << w->GetADC(41) << " " << w->GetADC(42) << " "
//            << w->GetADC(43) << " " << w->GetADC(44) << " " << w->GetADC(45)
//            << " " << w->GetADC(46) << "   " << static_cast<int>(p.GetRow())
//            << " " << static_cast<int>(p.GetColumn()) << " ---- "
//            << p.GetSlotID();

//   packet_id = (module_id * 64 + asic * 16 + chan) /
//               nwaveforms;  /// where to define ASICs/module and channels for
//                            /// MODULE etc?
// } else {
//   GERROR() << "Could not derive packet id ";
//   packet_id = 0;
// }  // if

// return p.IsValid();
//}

}  // namespaceTARGET
}  // namespace CTA

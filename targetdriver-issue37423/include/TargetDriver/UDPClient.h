// Copyright (c) 2015 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains the client part of the target communications
 */
#ifndef INCLUDE_TARGETDRIVER_UDPCLIENT_H_
#define INCLUDE_TARGETDRIVER_UDPCLIENT_H_

#include <poll.h>
#include <string>
#include <vector>

#define WITH_MUTEX

#ifdef WITH_MUTEX
#include <mutex>  // NOLINT(build/c++11), <mutex> is supported by GCC 4.4.7
#endif

#include "TargetDriver/UDPBase.h"

namespace CTA {
	namespace TargetDriver {

		/*!
		* @class UDPClient
		* @brief This class provides client side functionality for communication using
		*UDP packets, used as the basis for communication with TARGET modules (i.e. a
		*TARGET module is a server and the process that talks to it is a client).
		*
		*
		*/
		class UDPClient : public UDPBase {
			public:
			explicit UDPClient(uint8_t maxattempts = 5, uint32_t sctimeout_ms = 200, uint32_t datatimeout_ms = 20);
			~UDPClient();
			///
			/// Establish a Slow Control link to the server
			int ConnectToServer(const std::string& pMyIP, uint16_t pMySourcePort, const std::string& pServerIP, 
								uint16_t pServerPort, int32_t pSocketBufferSize = -1);
			///
			/// Opens a socket for receiving UDP data and keeps it in a list for
			/// future listening (via GetDataPacket) - can be called several times to
			/// listen on multiple IPs
			int AddDataListener(const std::string& pMyIP, uint16_t pMyDataReceivePort, int32_t pSocketBufferSize = -1);
			///
			/// Closes sockets for both slow control and DAQ
			void CloseSockets();
			void CloseDataListenerSockets();
			///
			/// Listens on all sockets registered via AddDataListener for fDataTimeout
			///  ms and returns true if there was data - filling the pointer tobefilled
			///  with the data read
			int GetDataPacket(void* tobefilled,
							uint32_t& bytes,  // NOLINT(runtime/references)
							size_t maxbytes);
			///
			/// Send a query/command and get the response - will try multiple times
			/// internally
			int SendAndReceive(const void* message, uint32_t length, void* response,
							 ssize_t& resplength,  // NOLINT(runtime/references)
							 uint32_t maxlength);

			void SetMaxAttempts(uint8_t max_attempts) { fMaxAttempts = max_attempts; }

			protected:
			/// Make a single attempt to read an arriving packet from the socket buffer
			////  int Receive(void* buffer, uint32_t& length, uint32_t maxbytes);
			/// Discard remaining packets in the socket buffer. This method should be used
			/// before sending a command packet to get rid of the possibility of
			/// duplicated response packets.
			int DiscardPacketsInTheSocketBuffer();
			///
			/// Make a single attempt to send a message/command/query to the server
			int Send(const void* buffer, uint32_t length);

			uint8_t fMaxAttempts;  //<! Number of maximum attemps for register operations
			/////  int32_t fResponseTimeOut;  //<! Time out in ms for awaiting a response
			/// from the server
			uint32_t fDAQTimeout;  //<! Time out in ms when listening for data packets

			std::vector<pollfd> fDAQPollList;  //<! A list of pollfd structs to be used by
			typedef std::vector<pollfd>::const_iterator PF_cit;
			/// the poll() call inside GetDataPacket() -
			/// the pollfd struct includes the socket
			/// file descriptor

			#ifdef WITH_MUTEX
			std::string fServerIPAddress;
			std::mutex fSendAndReceiveMutex;
			#endif
		};

	}  // namespace TargetDriver
}  // namespace CTA
#endif  // INCLUDE_TARGETDRIVER_UDPCLIENT_H_

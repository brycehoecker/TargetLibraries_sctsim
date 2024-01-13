// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include "TargetDriver/UDPClient.h"
#include <arpa/inet.h>
#include <errno.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <iostream>
#include <string>

namespace CTA {
	namespace TargetDriver {

		UDPClient::UDPClient(uint8_t pMaxAttempts, uint32_t pReceiveTimeout_ms, uint32_t pDAQTimeout_ms)
					: fMaxAttempts(pMaxAttempts), fDAQTimeout(pDAQTimeout_ms) {
			fReceiveTimeoutMs = pReceiveTimeout_ms;
			#ifdef WITH_MUTEX
			fServerIPAddress = "No Server IP";
			#endif
		}//UDPClient::UDPClient

		UDPClient::~UDPClient() { CloseSockets(); }

		int UDPClient::ConnectToServer(const std::string& pMyIP, uint16_t pMySourcePort,
						   const std::string& pServerIP,
						   uint16_t pServerPort,
						   int32_t pSocketBufferSize) {
			if (fSocket != -1) {
				return TC_ERR_USER_ERROR;  //  socket is already open
			}

			fSocket = socket(AF_INET, SOCK_DGRAM, 0);

			if (fSocket == -1) {
				std::cerr << "UDPClient::ConnectToServer: socket failed " << strerror(errno) << std::endl;
				return TC_ERR_COMM_FAILURE;
			}

			if (pSocketBufferSize > 0) {
				if (setsockopt(fSocket, SOL_SOCKET, SO_RCVBUF, &pSocketBufferSize, sizeof(pSocketBufferSize)) != 0) {
					std::cerr << "UDPClient::ConnectToServer: setsockopt failed "
						<< strerror(errno) << std::endl;
					return TC_ERR_COMM_FAILURE;  // can't change the buffer to the required
										   // size
				}
			}

			struct sockaddr_in sourceSocketAddress;
			memset(&sourceSocketAddress, 0, sizeof(sourceSocketAddress));
			sourceSocketAddress.sin_addr.s_addr = inet_addr(pMyIP.c_str());
			sourceSocketAddress.sin_port = htons(pMySourcePort);
			sourceSocketAddress.sin_family = AF_INET;

			int ret = bind(fSocket, (struct sockaddr*)&sourceSocketAddress, sizeof(sourceSocketAddress));

			if (ret != 0) {
				std::cerr << "UDPClient::ConnectToServer: bind failed " << strerror(errno) << ": port " << pMySourcePort << " ip " << pMyIP << std::endl;
				return TC_ERR_COMM_FAILURE;
			}
			std::cerr << "UDPClient::ConnectToServer: bind OK "	<< " port " << pMySourcePort << " ip " << pMyIP << std::endl;

			struct sockaddr_in destinationSocketAddress;
			memset(&destinationSocketAddress, 0, sizeof(destinationSocketAddress));
			if (std::string(pServerIP) != "" && pServerPort != 0) {
				destinationSocketAddress.sin_addr.s_addr = inet_addr(pServerIP.c_str());
				destinationSocketAddress.sin_port = htons(pServerPort);
				destinationSocketAddress.sin_family = AF_INET;
			}

			ret = connect(fSocket, (struct sockaddr*)&destinationSocketAddress, sizeof(destinationSocketAddress));

			if (ret != 0) {
				std::cerr << "UDPClient::ConnectToServer: connect failed " << strerror(errno) << std::endl;
				return TC_ERR_NO_RESPONSE;
			}

			if (fVerbose) {
				std::cout << "UDPClient set up to contact server on port " << pServerPort << " - will attempt all commands " << (int)fMaxAttempts << " times" << std::endl;
			}

			#ifdef WITH_MUTEX
			fServerIPAddress = pServerIP;
			#endif

			return TC_OK;
		}//int UDPClient::ConnectToServer

		int UDPClient::DiscardPacketsInTheSocketBuffer() {
			fd_set fds;
			FD_ZERO(&fds);
			FD_SET(fSocket, &fds);

			struct timeval tv;
			tv.tv_sec = 0;
			tv.tv_usec = 0;
			for (uint32_t i = 0; i < 100; ++i) {  // 100 is arbitrary, but should be enough
				int nselect = select(fSocket + 1, &fds, NULL, NULL, &tv);
				if (nselect == 0) {
				return TC_OK;
				}

				if (!FD_ISSET(fSocket, &fds)) {
				return TC_OK;
				}
				// If found, read the packet and discard it
				recvfrom(fSocket, 0, 1, 0, NULL, NULL);
			}
			return TC_ERR_COMM_FAILURE;
		}//int UDPClient::DiscardPacketsInTheSocketBuffer

		int UDPClient::Send(const void* buffer, uint32_t length) {
			if (fSocket == -1) {
				std::cerr << "socket = -1" << std::endl;
				return TC_ERR_COMM_FAILURE;
			}
			int64_t bytes_written = write(fSocket, buffer, length);

			if (fVerbose) {
				std::cout << "UDPClient::Send - sent " << bytes_written << " bytes" << std::endl;
			}
			if (bytes_written == (int64_t)length) return TC_OK;

			return TC_ERR_COMM_FAILURE;
		}//int UDPClient::Send

		int UDPClient::AddDataListener(const std::string& pMyIP,
										uint16_t pMyDataReceivePort,
										int32_t pSocketBufferSize) {
			int sock = socket(AF_INET, SOCK_DGRAM, 0);
			//int sock = socket(AF_INET, SOCK_RAW, 0); // Rich - hack for xdacq

			if (sock == -1) {
				std::cerr << strerror(errno) << ".\n";
				return TC_ERR_COMM_FAILURE;
			}

			if (pSocketBufferSize > 0) {
				if (setsockopt(sock, SOL_SOCKET, SO_RCVBUF, &pSocketBufferSize, sizeof(pSocketBufferSize)) != 0) {
					std::cerr << strerror(errno) << ".\n";
					return TC_ERR_COMM_FAILURE;
				}
			}

			struct sockaddr_in sourceSocketAddress;
			memset(&sourceSocketAddress, 0, sizeof(sourceSocketAddress));
			sourceSocketAddress.sin_addr.s_addr = inet_addr(pMyIP.c_str());
			sourceSocketAddress.sin_port = htons(pMyDataReceivePort);
			sourceSocketAddress.sin_family = AF_INET;

			int ret = bind(sock, (struct sockaddr*)&sourceSocketAddress, sizeof(sourceSocketAddress));

			if (ret != 0) {
				std::cerr << "Cannot bind. " << strerror(errno) << ".\n";
				return TC_ERR_COMM_FAILURE;
			}

			struct pollfd poll_in;
			poll_in.fd = sock;
			poll_in.events = POLLIN;
			poll_in.revents = 0;
			fDAQPollList.push_back(poll_in);
			
			std::cout << "UDPClient::AddDataListener - port " << std::dec << pMyDataReceivePort	<< " and ip " << pMyIP << std::endl;

			return TC_OK;
		}//int UDPClient::AddDataListener

		void UDPClient::CloseSockets() {
			CloseSocket();
			CloseDataListenerSockets();
		}//void UDPClient::CloseSockets

		void UDPClient::CloseDataListenerSockets() {
			if (fVerbose) {
				std::cout << "Closing data listener sockets" << std::endl;
			}

			for (unsigned int i = 0; i < fDAQPollList.size(); ++i) {
				close(fDAQPollList[i].fd);
			}
			fDAQPollList.clear();
		}//void UDPClient::CloseDataListenerSockets

		int UDPClient::SendAndReceive(const void* message, uint32_t length,
										void* response, ssize_t& resplength,
										uint32_t maxlength) {
			uint32_t attempts = 0;
			int stat;
			if (fSocket == -1) {
				std::cerr << "socket = -1" << std::endl;
				return TC_ERR_COMM_FAILURE;
			}

			#ifdef WITH_MUTEX
			fSendAndReceiveMutex.lock();
			// std::cout << "Locked mutex " << fServerIPAddress << std::endl;
			#endif
			while (attempts < fMaxAttempts) {
				DiscardPacketsInTheSocketBuffer();  // flush in case message/response has
											// got out of sync

				if ((stat = Send(message, length)) != TC_OK) {
					std::cerr << "Send failed in: UDPClient::SendAndReceive, error code: " << stat << ": " << ReturnCodeToString(stat) << std::endl;
					
					#ifdef WITH_MUTEX
					fSendAndReceiveMutex.unlock();
					// std::cout << "Unlocked mutex " << fServerIPAddress << std::endl;
					#endif
					
					return stat;
				}
				// NOTE:
				// Should not need to sleep here - this is sleep before we start listening
				// for a response - and there is a timeout on the response - BUT - removing
				// this may imply a need to add sleeps in higher level users of this class
				//    usleep(2000);
				usleep(5);

				///  -------
				stat = Receive(response, resplength, maxlength);

				// a fatal error
				if (stat < 0) {
					std::cerr << "Receive failed in: UDPClient::SendAndReceive, error code: " << stat << ": " << ReturnCodeToString(stat) << std::endl;
					#ifdef WITH_MUTEX
					fSendAndReceiveMutex.unlock();
					// std::cout << "Error - Unlocked mutex " << fServerIPAddress << std::endl;
					#endif
					return stat;
				}

				if (stat == TC_OK) {
					#ifdef WITH_MUTEX
					fSendAndReceiveMutex.unlock();
					// std::cout << "OK - Unlocked mutex " << fServerIPAddress << " - " << resplength << std::endl;
					#endif
					return TC_OK;  // everything fine
				}                // otherwise try again

				if (fVerbose) {
					std::cerr << "SendAndReceive attempt " << attempts + 1 << "\t last attempt failed because of error code: " << stat << ": " << ReturnCodeToString(stat) << std::endl;
				}
				++attempts;
			}//while (attempts < fMaxAttempts)

			#ifdef WITH_MUTEX
			fSendAndReceiveMutex.unlock();
			#endif

			return TC_ERR_NO_RESPONSE;
		}//int UDPClient::SendAndReceive

		int UDPClient::GetDataPacket(void* tobefilled, uint32_t& bytes, size_t maxbytes) {
			bytes = 0;
			// Poll multiple sockets for incoming data
			int rc = poll(&fDAQPollList[0], static_cast<uint32_t>(fDAQPollList.size()),
				static_cast<int>(fDAQTimeout));

			if (rc == 0) {
			return TC_TIME_OUT;
			} else if (rc < 0) {
			return TC_ERR_COMM_FAILURE;
			}

			// Return data of the first socket which has data available
			for (PF_cit cit = fDAQPollList.cbegin(); cit != fDAQPollList.end(); ++cit) {
				if (cit->revents & POLLIN) {
					ssize_t ret = recvfrom(cit->fd, tobefilled, maxbytes, 0, NULL, NULL);

					if (fVerbose) {
					std::cout << "UDPClient::GetDataPacket - received " << bytes << " bytes from server " << ret << std::endl;
					}

					if (ret > 0) {
						bytes = static_cast<uint32_t>(ret);
						return TC_OK;
					}
				}
			}
			return TC_ERR_COMM_FAILURE;
		}//int UDPClient::GetDataPacket
	}  // namespace TargetDriver
}  // namespace CTA

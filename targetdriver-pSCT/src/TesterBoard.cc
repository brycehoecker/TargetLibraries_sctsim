// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include <iomanip>

#include "TargetDriver/TesterBoard.h"

namespace CTA {
	namespace TargetDriver {

		int TesterBoard::Init(const std::string& my_ip, const std::string& tb_ip) {
			//  SetVerbose(true);
			fReceiveTimeoutMs = 300;

			int stat;
			if ((stat = ConnectToServer(my_ip, TESTER_COMMAND_PORT, tb_ip, TESTER_BOARD_PORT)) != TC_OK) return stat;

			std::cout << "Opened testerboard connection" << std::endl;

			// Initialize sync
			stat = SetTriggerModeAndType(1, 0);
			if (stat != TC_OK) {
				std::cout << "SetTriggerModeAndType: " << ReturnCodeToString(stat) << std::endl;
				return stat;
			}

			// timestamp difference tester to module
			if ((stat = SetClockOffset(0x48)) != TC_OK) return stat;
			if ((stat = SetTriggerDeadTime(0xFFF)) != TC_OK) return stat;

			StartTimeBaseCounting(0xABCD1234 << 29);

			SetTriggerModeAndType(1, 1);
			if (stat != TC_OK) {
				std::cout << "SetTriggerModeAndType: " << ReturnCodeToString(stat) << std::endl;
				return stat;
			}
			if ((stat = WriteRegisterPartially(0x10010, 31, 31, 0x0, 29, 29, 0x1)) != TC_OK) return stat;
			if ((stat = WriteRegisterPartially(0x10010, 31, 31, 0x0, 29, 29, 0x0)) != TC_OK) return stat;

			// Software trigger mode
			SetTriggerModeAndType(0, 2);

			// Change TACK Parity
			WriteRegisterPartially(0x10010, 30, 30, 0x0);

			return stat;
		}//int TesterBoard::Init

		void TesterBoard::PrintStatus() {
			uint32_t data = GetStatus();

			// clang-format off
			std::cout << std::setw(30) << std::left << "mgt_AVTT_OK:"                << ((data >> 11) & 0x1 ? "OK" : "NG") << "\n";  // NOLINT(whitespace/line_length)
			std::cout << std::setw(30) << std::left << "mgt_AVCCPLL_OK:"             << ((data >> 10) & 0x1 ? "OK" : "NG") << "\n";  // NOLINT(whitespace/line_length)
			std::cout << std::setw(30) << std::left << "mgt_AVCC_OK:"                << ((data >>  9) & 0x1 ? "OK" : "NG") << "\n";  // NOLINT(whitespace/line_length)
			std::cout << std::setw(30) << std::left << "+1.8 V:"                     << ((data >>  8) & 0x1 ? "OK" : "NG") << "\n";  // NOLINT(whitespace/line_length)
			std::cout << std::setw(30) << std::left << "OT (FPGA):"                  << ((data >>  7) & 0x1) << "\n";  // NOLINT(whitespace/line_length)
			std::cout << std::setw(30) << std::left << "EOS (FPGA):"                 << ((data >>  6) & 0x1) << "\n";  // NOLINT(whitespace/line_length)
			std::cout << std::setw(30) << std::left << "EOC (FPGA):"                 << ((data >>  5) & 0x1) << "\n";  // NOLINT(whitespace/line_length)
			std::cout << std::setw(30) << std::left << "DRDY (FPGA):"                << ((data >>  4) & 0x1) << "\n";  // NOLINT(whitespace/line_length)
			std::cout << std::setw(30) << std::left << "BUSY (FPGA):"                << ((data >>  3) & 0x1) << "\n";  // NOLINT(whitespace/line_length)
			std::cout << std::setw(30) << std::left << "USER_TEMP_ALARM_OUT (FPGA):" << ((data >>  2) & 0x1) << "\n";  // NOLINT(whitespace/line_length)
			std::cout << std::setw(30) << std::left << "VCCINT_ALARM_OUT (FPGA):"    << ((data >>  1) & 0x1) << "\n";  // NOLINT(whitespace/line_length)
			std::cout << std::setw(30) << std::left << "VCCAUX_ALARM_OUT (FPGA):"    << ((data >>  0) & 0x1) << "\n";  // NOLINT(whitespace/line_length)
			// clang-format on
		}//void TesterBoard::PrintStatus

		// void TesterBoard::SwitchAnalogInput(uint8_t asic, uint8_t channel) {
		//   if (asic > 3) {
		//     GERROR() << "ASIC must be 0, 1, 2, or 3.";
		//   }  // if
		//
		//   if (channel > 15) {
		//     GERROR() << "Channel number must be 15 or less.";
		//   }  // if
		//
		//   WriteRegisterPartially(0x10006, 19, 16, 0x1 << asic, 4 * asic + 3, 4 *
		//   asic,
		//                          channel);
		// }

		void TesterBoard::SetStatusOfBPLines(bool bp6, bool bp4) {
			WriteRegisterPartially(0x10007, 2, 2, bp6 ? 0x1 : 0x0, 0, 0, bp4 ? 0x1 : 0x0);
		}//void TesterBoard::SetStatusOfBPLines

		// uint16_t TesterBoard::ReadFPGAMonitor(uint8_t address) {
		//   WriteRegister(0x1000D, (0x7F & address) << 16);

		//   for (int32_t i = 0; i < 10; i++) {
		//     bool busy = (GetStatus() >> 3) & 0x1;
		//     if (busy) {
		//       usleep(10000);  // 10 ms
		//     } else {
		//       break;
		//     }  // if

		//     if (i == 9) {
		//       // TODO throw RuntimeError("FPGA monitor is still busy after 100 ms.");
		//     }  // if
		//   }    // i

		//   uint16_t adc = ReadRegister(0x1000C) & 0xFFFF;

		//   return adc;
		// }

		int TesterBoard::SetTriggerModeAndType(uint8_t mode, uint8_t type) {
			if (mode > 3 || type > 3) {
				// TODO(Harm) throw RuntimeError("mode and type must be between 0x0 and
				// 0x3.");
			}  // if

			// 20-21 Mode: 00 - trigger
			// 18-19 Type: 00 - TACK
			//             01 - TACK
			//             10 - SW
			//             11 - Unused
			//
			// 20-21 Mode: 01 - sync
			// 18-19 Type: 00 - Init
			//             01 - Re-sync
			//             10 - Stop sync
			//             11 - Unused
			//
			// WriteRegisterPartially(0x10010, 31, 31, 0);
			// usleep(1000);
			
			return WriteRegisterPartially(0x10010, 31, 31, 0, 21, 20, mode, 19, 18, type);
		}//int TesterBoard::SetTriggerModeAndType(

		void TesterBoard::EnableTrigger(uint8_t asic, bool b0, bool b1, bool b2, bool b3) {
			if (asic > 3) {
				// TODO(Harm) throw RuntimeError("ASIC must be 0, 1, 2, or 3.");
			}  // if

			uint8_t bits = 0x0;
			bits |= (b0 ? 0x1 : 0x0);
			bits |= (b1 ? 0x2 : 0x0);
			bits |= (b2 ? 0x4 : 0x0);
			bits |= (b3 ? 0x8 : 0x0);

			WriteRegisterPartially(0x10010, 31, 31, 0, 4 * asic + 3, 4 * asic, bits);
		}//void TesterBoard::EnableTrigger

		void TesterBoard::EnableTrigger(uint8_t asic, uint8_t group, bool enable) {
			if (asic > 3 || group > 3) {
			// TODO(Harm) throw RuntimeError("ASIC and group must be 3 or smaller");
			}  // if

			WriteRegisterPartially(0x10010, asic * 4 + group, asic * 4 + group, enable ? 0x1 : 0x0);
		}

		void TesterBoard::EnableTriggerCounterContribution(uint8_t asic, uint8_t group, bool enable) {
			if (asic > 3 || group > 3) {
			// TODO(Harm) throw RuntimeError("ASIC and group must be 3 or smaller");
			}  // if

			WriteRegisterPartially(0x10011, asic * 4 + group, asic * 4 + group, enable ? 0x1 : 0x0);
		}

		// double TesterBoard::GetMeasuredHV(double offset) {
		//   uint16_t adc = ReadFPGAMonitor(0x15);
		//   // 16 bits ADC is used, but the effective dynamic range is 10 bits only
		//   double v = ((adc & 0xFFFF) >> 6) * 109. / 4. / 1024. * 2000 - offset;
		//
		//   return v;
		// }

		void TesterBoard::StartTimeBaseCounting(uint64_t start) {
			if (start > 0x7FFFFFFF) {
			// TODO(Harm) throw RuntimeError("Start value must be 61 bits");
			}  // if

			WriteRegisterPartially(0x10015, 31, 3, start & 0x7FFFFFFF);
			WriteRegister(0x10016, static_cast<uint32_t>(start >> 29));
		}

		//////

		/*!
		@brief Write a value into a specified bit range of a register
		@param address An FPGA register address
		@param msb MSB of the bit range
		@param lsb LSB of the bit range
		*/
		int TesterBoard::WriteRegisterPartially(uint32_t address, uint8_t msb, uint8_t lsb, uint32_t data) {
			if (msb > 31 || lsb > 31) {
				//    GERROR() << "Bits must be in between 0 and 31.";
				return TC_ERR_USER_ERROR;
			}  // if

			if (msb < lsb) {
				uint8_t tmp = lsb;
				lsb = msb;
				msb = tmp;
			}  // if

			uint32_t originalData;
			int stat;
			if ((stat = ReadRegister(address, originalData)) != TC_OK) return stat;

			uint32_t mask = (0xFFFFFFFF << lsb) & (0xFFFFFFFF >> (31 - msb));

			WriteRegister(address, (originalData & ~mask) | ((data << lsb) & mask));
			return 0;
		}//int TesterBoard::WriteRegisterPartially

		/*!
		@brief Write a value into two specified bit ranges of a register
		@param address An FPGA register address
		@param msb1 MSB of the first bit range
		@param lsb1 LSB of the fist bit range
		@param value1 A value to be written into the first bit range.
		@param msb2 MSB of the second bit range
		@param lsb2 LSB of the second bit range
		@param value1 A value to be written into the second bit range.
		*/
		int TesterBoard::WriteRegisterPartially(uint32_t address, uint8_t msb1,
											uint8_t lsb1, uint32_t value1,
											uint8_t msb2, uint8_t lsb2,
											uint32_t value2) {
			if (msb1 > 31 || lsb1 > 31 || msb2 > 31 || lsb2 > 31) {
			//   GERROR() << "Bits must be in between 0 and 31.";
			return TC_ERR_USER_ERROR;
			}  // if

			if (msb1 < lsb1) {
			uint8_t tmp = lsb1;
			lsb1 = msb1;
			msb1 = tmp;
			}  // if

			if (msb2 < lsb2) {
			uint8_t tmp = lsb2;
			lsb2 = msb2;
			msb2 = tmp;
			}  // if

			uint32_t originalData;
			int stat;
			if ((stat = ReadRegister(address, originalData)) != TC_OK) return stat;

			uint32_t mask1 = (0xFFFFFFFF << lsb1) & (0xFFFFFFFF >> (31 - msb1));
			uint32_t mask2 = (0xFFFFFFFF << lsb2) & (0xFFFFFFFF >> (31 - msb2));

			return WriteRegister(address, (originalData & ~(mask1 | mask2)) |
											((value1 << lsb1) & mask1) |
											((value2 << lsb2) & mask2));
		}//int TesterBoard::WriteRegisterPartially

		/*!
		@brief Write a value into three specified bit ranges of a register
		@param address An FPGA register address
		@param msb1 MSB of the first bit range
		@param lsb1 LSB of the fist bit range
		@param value1 A value to be written into the first bit range.
		@param msb2 MSB of the second bit range
		@param lsb2 LSB of the second bit range
		@param value2 A value to be written into the second bit range.
		@param msb3 MSB of the third bit range
		@param lsb3 LSB of the third bit range
		@param value3 A value to be written into the third bit range.
		*/
		int TesterBoard::WriteRegisterPartially(uint32_t address, uint8_t msb1,
												uint8_t lsb1, uint32_t value1,
												uint8_t msb2, uint8_t lsb2,
												uint32_t value2, uint8_t msb3,
												uint8_t lsb3, uint32_t value3) {
												
			if (msb1 > 31 || lsb1 > 31 || msb2 > 31 || lsb2 > 31 || msb3 > 31 || lsb3 > 31) {
				//    GERROR() << "Bits must be in between 0 and 31.";
				return TC_ERR_USER_ERROR;
			}  // if

			if (msb1 < lsb1) {
				uint8_t tmp = lsb1;
				lsb1 = msb1;
				msb1 = tmp;
			}  // if

			if (msb2 < lsb2) {
				uint8_t tmp = lsb2;
				lsb2 = msb2;
				msb2 = tmp;
			}  // if

			if (msb3 < lsb3) {
				uint8_t tmp = lsb3;
				lsb3 = msb3;
				msb3 = tmp;
			}  // if

			uint32_t originalData;
			int stat;
			if ((stat = ReadRegister(address, originalData)) != TC_OK) return stat;

			uint32_t mask1 = (0xFFFFFFFF << lsb1) & (0xFFFFFFFF >> (31 - msb1));
			uint32_t mask2 = (0xFFFFFFFF << lsb2) & (0xFFFFFFFF >> (31 - msb2));
			uint32_t mask3 = (0xFFFFFFFF << lsb3) & (0xFFFFFFFF >> (31 - msb3));

			return WriteRegister(address, (originalData & ~(mask1 | mask2 | mask3)) |
											((value1 << lsb1) & mask1) |
											((value2 << lsb2) & mask2) |
											((value3 << lsb3) & mask3));
		}//int TesterBoard::WriteRegisterPartially
	}  // namespace TargetDriver
}  // namespace CTA

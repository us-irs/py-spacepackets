#!/usr/bin/env python3
from unittest import TestCase

from spacepackets.ecss.tc import PusTelecommand
from spacepackets.ecss.conf import set_default_tm_apid
from spacepackets.util import PrintFormats
from spacepackets.ecss.tm import (
    PusTelemetry,
    CdsShortTimestamp,
    PusVersion,
    get_service_from_raw_pus_packet,
    PusTmSecondaryHeader,
)
from spacepackets.ecss.pus_17_test import Service17Tm
from spacepackets.ecss.pus_1_verification import (
    Service1Tm,
    RequestId,
    Subservices,
    VerificationParams,
)


class TestTelemetry(TestCase):
    def test_telemetry(self):
        pus_17_tm = PusTelemetry(
            service=17,
            subservice=2,
            apid=0xEF,
            seq_count=22,
            source_data=bytearray(),
            time=CdsShortTimestamp.init_from_current_time(),
        )
        self.assertEqual(pus_17_tm.get_source_data_string(PrintFormats.HEX), "hex []")
        self.assertEqual(pus_17_tm.get_source_data_string(PrintFormats.DEC), "dec []")
        self.assertEqual(pus_17_tm.get_source_data_string(PrintFormats.BIN), "bin []")
        self.assertEqual(pus_17_tm.subservice, 2)
        self.assertEqual(pus_17_tm.service, 17)
        self.assertEqual(pus_17_tm.seq_count, 22)
        self.assertEqual(pus_17_tm.packet_len, 22)
        pus_17_raw = pus_17_tm.pack()
        self.assertEqual(get_service_from_raw_pus_packet(raw_bytearray=pus_17_raw), 17)
        self.assertRaises(ValueError, get_service_from_raw_pus_packet, bytearray())

        set_default_tm_apid(0x22)
        source_data = bytearray([0x42, 0x38])
        pus_17_tm = PusTelemetry(
            service=17,
            subservice=2,
            seq_count=22,
            source_data=source_data,
        )
        self.assertEqual(
            pus_17_tm.get_source_data_string(PrintFormats.HEX), "hex [42,38]"
        )
        self.assertEqual(
            pus_17_tm.get_source_data_string(PrintFormats.DEC), "dec [66,56]"
        )
        self.assertEqual(
            pus_17_tm.get_source_data_string(PrintFormats.BIN),
            "bin [\n0:01000010\n1:00111000\n]",
        )
        self.assertEqual(pus_17_tm.apid, 0x22)
        self.assertEqual(pus_17_tm.pus_tm_sec_header.pus_version, PusVersion.PUS_C)
        self.assertTrue(pus_17_tm.valid)
        self.assertEqual(pus_17_tm.tm_data, source_data)
        self.assertEqual(pus_17_tm.packet_id.raw(), 0x0822)
        pus_17_tm.print_full_packet_string(PrintFormats.HEX)
        self.assertEqual(pus_17_tm.packet_len, 24)
        crc16 = pus_17_tm.crc16
        crc_string = f"{(crc16 & 0xff00) >> 8:02x},{crc16 & 0xff:02x}"
        raw_time = pus_17_tm.pus_tm_sec_header.time.pack()
        raw_space_packet_header = pus_17_tm.sp_header.pack()
        sp_header_as_str = raw_space_packet_header.hex(sep=",", bytes_per_sep=1)
        raw_secondary_packet_header = pus_17_tm.pus_tm_sec_header.pack()
        self.assertEqual(raw_secondary_packet_header[0], 0x20)
        # Service
        self.assertEqual(raw_secondary_packet_header[1], 17)
        # Subservice
        self.assertEqual(raw_secondary_packet_header[2], 2)
        second_header_as_str = raw_secondary_packet_header.hex(sep=",", bytes_per_sep=1)
        expected_printout = f"hex [{sp_header_as_str},{second_header_as_str},"
        expected_printout += "42,38,"
        expected_printout += f"{crc_string}]"
        self.assertEqual(
            pus_17_tm.get_full_packet_string(PrintFormats.HEX), expected_printout
        )
        pus_17_raw = pus_17_tm.pack()

        pus_17_tm_unpacked = PusTelemetry.unpack(raw_telemetry=pus_17_raw)
        print(pus_17_tm)
        print(pus_17_tm.__repr__())
        self.assertEqual(pus_17_tm_unpacked.apid, 0x22)
        self.assertEqual(
            pus_17_tm_unpacked.pus_tm_sec_header.pus_version, PusVersion.PUS_C
        )
        self.assertTrue(pus_17_tm_unpacked.valid)
        self.assertEqual(pus_17_tm_unpacked.tm_data, source_data)
        self.assertEqual(pus_17_tm_unpacked.packet_id.raw(), 0x0822)
        self.assertRaises(ValueError, PusTelemetry.unpack, None)
        self.assertRaises(ValueError, PusTelemetry.unpack, bytearray())
        correct_size = pus_17_raw[4] << 8 | pus_17_raw[5]
        # Set length field invalid
        pus_17_raw[4] = 0x00
        pus_17_raw[5] = 0x00
        self.assertRaises(ValueError, PusTelemetry.unpack, pus_17_raw)
        pus_17_raw[4] = 0xFF
        pus_17_raw[5] = 0xFF
        self.assertRaises(ValueError, PusTelemetry.unpack, pus_17_raw)

        pus_17_raw[4] = (correct_size & 0xFF00) >> 8
        pus_17_raw[5] = correct_size & 0xFF
        pus_17_raw.append(0)
        # Should work with a warning
        pus_17_tm_unpacked = PusTelemetry.unpack(raw_telemetry=pus_17_raw)

        # This should cause the CRC calculation to fail
        incorrect_size = correct_size + 1
        pus_17_raw[4] = (incorrect_size & 0xFF00) >> 8
        pus_17_raw[5] = incorrect_size & 0xFF
        pus_17_tm_unpacked = PusTelemetry.unpack(raw_telemetry=pus_17_raw)

        invalid_secondary_header = bytearray([0x20, 0x00, 0x01, 0x06])
        self.assertRaises(
            ValueError, PusTmSecondaryHeader.unpack, invalid_secondary_header
        )
        with self.assertRaises(ValueError):
            # Message Counter too large
            PusTmSecondaryHeader(
                service=0,
                subservice=0,
                time=CdsShortTimestamp.init_from_current_time(),
                message_counter=129302,
            )
        valid_secondary_header = PusTmSecondaryHeader(
            service=0,
            subservice=0,
            time=CdsShortTimestamp.init_from_current_time(),
            message_counter=22,
        )

        ccsds_packet = pus_17_tm.to_space_packet()
        self.assertEqual(ccsds_packet.apid, pus_17_tm.apid)
        self.assertEqual(ccsds_packet.pack(), pus_17_tm.pack())
        self.assertEqual(ccsds_packet.seq_count, pus_17_tm.seq_count)
        self.assertEqual(ccsds_packet.sec_header_flag, True)
        pus_17_from_composite_fields = PusTelemetry.from_composite_fields(
            sp_header=pus_17_tm.sp_header,
            sec_header=pus_17_tm.pus_tm_sec_header,
            tm_data=pus_17_tm.tm_data,
        )
        print(pus_17_from_composite_fields.pack().hex(sep=","))
        print(pus_17_tm.pack().hex(sep=","))
        self.assertEqual(pus_17_from_composite_fields.pack(), pus_17_tm.pack())
        # Hand checked to see if all __repr__ were implemented properly
        print(f"{pus_17_tm!r}")

    def test_service_17_tm(self):
        srv_17_tm = Service17Tm(subservice=2)
        self.assertEqual(srv_17_tm.pus_tm.subservice, 2)
        srv_17_tm_raw = srv_17_tm.pack()
        srv_17_tm_unpacked = Service17Tm.unpack(
            raw_telemetry=srv_17_tm_raw, pus_version=PusVersion.PUS_C
        )
        self.assertEqual(srv_17_tm_unpacked.pus_tm.subservice, 2)

    def test_service_1_tm(self):
        pus_tc = PusTelecommand(service=17, subservice=1)
        srv_1_tm = Service1Tm(
            subservice=Subservices.TM_ACCEPTANCE_SUCCESS,
            verif_params=VerificationParams(
                RequestId(pus_tc.packet_id, pus_tc.packet_seq_ctrl)
            ),
        )
        self.assertEqual(srv_1_tm.pus_tm.subservice, Subservices.TM_ACCEPTANCE_SUCCESS)
        self.assertEqual(srv_1_tm.tc_req_id.tc_packet_id, pus_tc.packet_id)
        self.assertEqual(srv_1_tm.tc_req_id.tc_psc, pus_tc.packet_seq_ctrl)
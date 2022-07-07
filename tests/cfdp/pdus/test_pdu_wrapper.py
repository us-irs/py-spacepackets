from unittest import TestCase

from spacepackets.cfdp import ChecksumTypes, ConditionCode
from spacepackets.cfdp.conf import PduConfig
from spacepackets.cfdp.pdu import (
    MetadataPdu,
    AckPdu,
    DirectiveType,
    TransactionStatus,
    NakPdu,
    PromptPdu,
    EofPdu,
    FinishedPdu,
    KeepAlivePdu,
)
from spacepackets.cfdp.pdu.file_data import FileDataPdu
from spacepackets.cfdp.pdu.finished import DeliveryCode, FileDeliveryStatus
from spacepackets.cfdp.pdu.prompt import ResponseRequired
from spacepackets.cfdp.pdu.wrapper import PduWrapper


class TestPduWrapper(TestCase):
    def setUp(self) -> None:
        self.pdu_conf = PduConfig.empty()
        self.file_data = "hello world"
        self.file_data_bytes = self.file_data.encode()
        self.pdu_wrapper = PduWrapper(None)

    def test_file_data(self):
        file_data_pdu = FileDataPdu(
            pdu_conf=self.pdu_conf,
            file_data=self.file_data_bytes,
            offset=0,
            segment_metadata_flag=False,
        )
        self.pdu_wrapper.base = file_data_pdu
        pdu_casted_back = self.pdu_wrapper.to_file_data_pdu()
        self.assertEqual(pdu_casted_back, file_data_pdu)

    def test_invalid_to_file_data(self):
        metadata_pdu = MetadataPdu(
            pdu_conf=self.pdu_conf,
            closure_requested=False,
            file_size=2,
            source_file_name="test.txt",
            dest_file_name="test2.txt",
            checksum_type=ChecksumTypes.MODULAR,
        )
        self.pdu_wrapper.base = metadata_pdu
        with self.assertRaises(TypeError) as cm:
            self.pdu_wrapper.to_file_data_pdu()
        exception = cm.exception
        self.assertIn("Stored PDU is not 'FileDataPdu'", str(exception))

    def test_metadata(self):
        metadata_pdu = MetadataPdu(
            pdu_conf=self.pdu_conf,
            closure_requested=False,
            file_size=2,
            source_file_name="test.txt",
            dest_file_name="test2.txt",
            checksum_type=ChecksumTypes.MODULAR,
        )
        self.pdu_wrapper.base = metadata_pdu
        metadata_casted_back = self.pdu_wrapper.to_metadata_pdu()
        self.assertEqual(metadata_casted_back, metadata_pdu)

    def test_invalid_cast(self):
        file_data_pdu = FileDataPdu(
            pdu_conf=self.pdu_conf,
            file_data=self.file_data_bytes,
            offset=0,
            segment_metadata_flag=False,
        )
        self.pdu_wrapper.base = file_data_pdu
        with self.assertRaises(TypeError) as cm:
            self.pdu_wrapper.to_metadata_pdu()
        exception = cm.exception
        self.assertTrue("Stored PDU is not 'MetadataPdu'" in str(exception))

    def test_ack_cast(self):
        ack_pdu = AckPdu(
            directive_code_of_acked_pdu=DirectiveType.FINISHED_PDU,
            condition_code_of_acked_pdu=ConditionCode.NO_ERROR,
            transaction_status=TransactionStatus.TERMINATED,
            pdu_conf=self.pdu_conf,
        )
        self.pdu_wrapper.base = ack_pdu
        ack_pdu_converted = self.pdu_wrapper.to_ack_pdu()
        self.assertEqual(ack_pdu_converted, ack_pdu)

    def test_nak_cast(self):
        nak_pdu = NakPdu(start_of_scope=0, end_of_scope=200, pdu_conf=self.pdu_conf)
        self.pdu_wrapper.base = nak_pdu
        nak_pdu_converted = self.pdu_wrapper.to_nak_pdu()
        self.assertEqual(nak_pdu_converted, nak_pdu)

    def test_prompt_cast(self):
        prompt_pdu = PromptPdu(
            pdu_conf=self.pdu_conf, response_required=ResponseRequired.KEEP_ALIVE
        )
        self.pdu_wrapper.base = prompt_pdu
        prompt_pdu_converted = self.pdu_wrapper.to_prompt_pdu()
        self.assertEqual(prompt_pdu_converted, prompt_pdu)

    def test_eof_cast(self):
        zero_checksum = bytes([0x00, 0x00, 0x00, 0x00])
        eof_pdu = EofPdu(
            file_checksum=zero_checksum, file_size=0, pdu_conf=self.pdu_conf
        )
        self.pdu_wrapper.base = eof_pdu
        eof_pdu_converted = self.pdu_wrapper.to_eof_pdu()
        self.assertEqual(eof_pdu_converted, eof_pdu)

    def test_finished_cast(self):
        finish_pdu = FinishedPdu(
            delivery_code=DeliveryCode.DATA_COMPLETE,
            file_delivery_status=FileDeliveryStatus.FILE_STATUS_UNREPORTED,
            condition_code=ConditionCode.NO_ERROR,
            pdu_conf=self.pdu_conf,
        )
        self.pdu_wrapper.base = finish_pdu
        finish_pdu_converted = self.pdu_wrapper.to_finished_pdu()
        self.assertEqual(finish_pdu_converted, finish_pdu)

    def test_keep_alive_cast(self):
        keep_alive_pdu = KeepAlivePdu(progress=0, pdu_conf=self.pdu_conf)
        self.pdu_wrapper.base = keep_alive_pdu
        keep_alive_pdu_converted = self.pdu_wrapper.to_keep_alive_pdu()
        self.assertEqual(keep_alive_pdu_converted, keep_alive_pdu)
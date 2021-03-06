from __future__ import annotations
from dataclasses import dataclass
from typing import TypedDict, Tuple

from spacepackets.cfdp.defs import (
    TransmissionModes,
    LargeFileFlag,
    CrcFlag,
    Direction,
    SegmentationControl,
)
from spacepackets.log import get_console_logger
from spacepackets.util import UnsignedByteField, ByteFieldU8, ByteFieldEmpty


@dataclass
class PduConfig:
    """Common configuration fields for a PDU.

    Setting the GLOBAL_CONFIG property or creating an empty configuration will automatically
    determine the flag values of the respective fields from the global configuration to avoid
    specifying parameter which rarely change repeatedly
    """

    source_entity_id: UnsignedByteField
    dest_entity_id: UnsignedByteField
    transaction_seq_num: UnsignedByteField
    trans_mode: TransmissionModes
    file_flag: LargeFileFlag = LargeFileFlag.NORMAL
    crc_flag: CrcFlag = CrcFlag.NO_CRC
    direction: Direction = Direction.TOWARDS_RECEIVER
    seg_ctrl: SegmentationControl = (
        SegmentationControl.NO_RECORD_BOUNDARIES_PRESERVATION
    )

    @classmethod
    def empty(cls) -> PduConfig:
        """Empty PDU configuration which is not valid for usage because the contained unsigned
        byte fields are empty (sequence number and both entity IDs)
        """
        return PduConfig(
            transaction_seq_num=ByteFieldEmpty(),
            trans_mode=TransmissionModes.ACKNOWLEDGED,
            source_entity_id=ByteFieldEmpty(),
            dest_entity_id=ByteFieldEmpty(),
            file_flag=LargeFileFlag.NORMAL,
            crc_flag=CrcFlag.NO_CRC,
        )

    @classmethod
    def default(cls):
        """Valid PDU configuration"""
        return PduConfig(
            transaction_seq_num=ByteFieldU8(0),
            trans_mode=TransmissionModes.ACKNOWLEDGED,
            source_entity_id=ByteFieldU8(0),
            dest_entity_id=ByteFieldU8(0),
            file_flag=LargeFileFlag.NORMAL,
            crc_flag=CrcFlag.NO_CRC,
        )


class CfdpDict(TypedDict):
    source_dest_entity_ids: Tuple[bytes, bytes]


# TODO: Protect dict access with a dedicated lock for thread-safety
__CFDP_DICT: CfdpDict = {
    "source_dest_entity_ids": (bytes(), bytes()),
}


def set_entity_ids(source_entity_id: bytes, dest_entity_id: bytes):
    __CFDP_DICT["source_dest_entity_ids"] = (source_entity_id, dest_entity_id)


def get_entity_ids() -> Tuple[bytes, bytes]:
    """Return a tuple where the first entry is the source entity ID"""
    return __CFDP_DICT["source_dest_entity_ids"]


def check_packet_length(
    raw_packet_len: int, min_len: int, warn_on_fail: bool = True
) -> bool:
    """Check whether the length of a raw packet is shorter than a specified expected minimum length.
    By defaults, prints a warning if this is the case
    :param raw_packet_len:
    :param min_len:
    :param warn_on_fail:
    :return: Returns True if the raw packet is larger than the specified minimum length, False
    otherwise
    """
    if raw_packet_len < min_len:
        if warn_on_fail:
            logger = get_console_logger()
            logger.warning(
                f"Detected packet length {raw_packet_len}, smaller than expected {min_len}"
            )
        return False
    return True

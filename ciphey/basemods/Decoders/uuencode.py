from binascii import a2b_uu
from codecs import decode
from typing import Dict, Optional

import logging
from rich.logging import RichHandler

from ciphey.iface import Config, Decoder, ParamSpec, T, U, registry


@registry.register
class Uuencode(Decoder[str]):
    def decode(self, ctext: T) -> Optional[U]:
        """
        UUEncode (Unix to Unix Encoding) is a symmetric encryption
        based on conversion of binary data (split into 6-bit blocks) into ASCII characters.

        This function decodes the input string 'ctext' if it has been encoded using 'uuencoder'
        It will return None otherwise
        """
        logging.debug("Attempting UUencode")
        result = ""
        try:
            # UUencoded messages may begin with prefix "begin" and end with suffix "end"
            # In that case, we use the codecs module in Python
            ctext_strip = ctext.strip()
            if ctext_strip.startswith("begin") and ctext_strip.endswith("end"):
                result = decode(bytes(ctext, "utf-8"), "uu").decode()
            else:
                # If there isn't a "being" prefix and "end" suffix, we use the binascii module instead
                # It is possible that the ctext has multiple lines, so convert each line and append
                ctext_split = list(filter(None, ctext.splitlines()))
                for value in ctext_split:
                    result += a2b_uu(value).decode("utf-8")
            logging.info(f"UUencode successful, returning '{result}'")
            return result
        except Exception:
            logging.debug("Failed to decode UUencode")
            return None

    @staticmethod
    def priority() -> float:
        # Not expected to show up often, but also very fast to check.
        return 0.05

    def __init__(self, config: Config):
        super().__init__(config)

    @staticmethod
    def getParams() -> Optional[Dict[str, ParamSpec]]:
        return None

    @staticmethod
    def getTarget() -> str:
        return "uuencode"

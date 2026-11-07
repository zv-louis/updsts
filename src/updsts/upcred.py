# encoding : utf_8_sig

import os
import re
from typing import Callable

from argparse import ArgumentParser
from pathlib import Path

from .logutil import get_logger

# Read with utf-8-sig to accept a BOM (e.g. saved by Notepad or Windows PowerShell 5.1).
# The file is written back as plain UTF-8, which also drops the BOM that botocore cannot parse.
CREDENTIAL_FILE_ENCODING = "utf-8-sig"
CREDENTIAL_FILE_WRITE_ENCODING = "utf-8"

# ----------------------------------------------------------------------------
def credential_decode_error_message(credential_file: os.PathLike, e: UnicodeDecodeError) -> str:
    """
    Build a user-facing message for a credentials file that is not UTF-8 encoded.
    """
    # e.start is relative to the decoded chunk, not the file, so it is not shown
    return (f"Credential file '{credential_file}' is not UTF-8 encoded ({e.reason}). "
            f"Please re-save it as UTF-8.")

# ############################################################################
class CredentialUpdater:
    """
    Update AWS credentials file.
    """
    # ----------------------------------------------------------------------------
    def __init__(self, credential_path: str | os.PathLike = None):
        self.creds  = {}
        self.target_tag_name = None
        self.credential_file_path = None
        self.sts_profile_name = None
        self.message_handler = None
        if (credential_path):
            self.set_credentials_path(credential_path)

    # ----------------------------------------------------------------------------
    def set_credentials_path(self, cred_path: os.PathLike):
        """
        set credentials file path
        Args:
            cred_path (_type_): credentials file path
        """
        self.credential_file_path = cred_path if isinstance(cred_path, Path) else Path(cred_path)

    # ----------------------------------------------------------------------------
    def set_target_tag_name(self, target_tag_name: str):
        """
        set target key name
        Args:
            target_tag_name (str): target key name in the credentials file to be replaced
        """
        self.target_tag_name = target_tag_name

    # ----------------------------------------------------------------------------
    def set_credentials(self, creds: dict):
        """
        set aws sts credentials
        Args:
            creds (dict): AWS STS credentials dictionary
        """
        self.creds = creds

    def set_sts_profile_name(self, sts_profile_name: str):
        """
        set sts profile name
        Args:
            sts_profile_name (str | None): STS profile name
        """
        self.sts_profile_name = sts_profile_name

    # ----------------------------------------------------------------------------
    def set_message_handler(self, message_handler: Callable[[str], None] | None):
        """
        set message handler for user-facing progress messages
        Args:
            message_handler (Callable[[str], None] | None): e.g. print for CLI. None to suppress.
        """
        self.message_handler = message_handler

    # ----------------------------------------------------------------------------
    def update_credential_file(self) -> dict[str, str] | None:
        """
        update the credentials file
        """
        logger = get_logger()
        bgn_tag = re.compile(r"^(\s*)#\s+\$\{\{\{\s+key=([\w\-_]+)\s+.*\r?\n")
        end_tag = re.compile(r"^(\s*)#\s+\$\}\}\}\s+.*\r?\n")
        out_path = self.credential_file_path.with_suffix(".tmp")
        updated_profile_info = None
        try:
            with self.credential_file_path.open(mode='r', encoding=CREDENTIAL_FILE_ENCODING) as fin:
                # create the temp file owner-only from the start (umask may otherwise leave it readable by others).
                # remove a stale one first so that O_EXCL guarantees the mode is applied.
                out_path.unlink(missing_ok=True)
                fd = os.open(out_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
                with os.fdopen(fd, mode='w', encoding=CREDENTIAL_FILE_WRITE_ENCODING) as fout:
                    is_break = False
                    is_in_replace_tag = None
                    sts_profile_name = self.sts_profile_name if self.sts_profile_name else f'{self.target_tag_name}_sts'
                    while not is_break: 
                        line = fin.readline()
                        if (not line):
                            is_break = True
                            continue
                        if not is_in_replace_tag:
                            # search begin tag
                            fout.write(line)
                            obj = bgn_tag.search(line)
                            if (obj):
                                matched_key         = obj.group(2)
                                if (self.target_tag_name == matched_key):
                                    msg = f"found key : key='{self.target_tag_name}'"
                                    logger.info(msg)
                                    if self.message_handler:
                                        self.message_handler(msg)
                                    # write credentials
                                    aws_access_key_id     = self.creds.get("AccessKeyId",     "")
                                    aws_secret_access_key = self.creds.get("SecretAccessKey", "")
                                    aws_session_token     = self.creds.get("SessionToken",    "")
                                    aws_token_expiration  = self.creds.get("Expiration",      "")
                                    # write section header
                                    prof_tag = f"[{sts_profile_name}]\n"
                                    fout.write(prof_tag)
                                    # write items
                                    ak_str    = f"aws_access_key_id={aws_access_key_id}\n"
                                    asak_str  = f"aws_secret_access_key={aws_secret_access_key}\n"
                                    token_str = f"aws_session_token={aws_session_token}\n"
                                    exp_str   = f"expiration_datetime={aws_token_expiration}\n"
                                    fout.write(ak_str)
                                    fout.write(asak_str)
                                    fout.write(token_str)
                                    fout.write(exp_str)
                                    # ignore until end tag
                                    is_in_replace_tag = matched_key
                                    updated_profile_info = {
                                        "updated_profile_name" : sts_profile_name,
                                        "aws_access_key_id"    : self.creds.get("AccessKeyId", ""),
                                        "aws_token_expiration" : self.creds.get("Expiration",      "")
                                    }
                                else:
                                    # regular line
                                    is_in_replace_tag = None
                        else:
                            # in replace tag, search end tag
                            eobj = end_tag.search(line)
                            if (eobj):
                                is_in_replace_tag = None
                                fout.write(line)

                    if not updated_profile_info:
                        logger.warning(f"the target block key='{self.target_tag_name}' is not found. creating new block for the target key.")
                        # create section
                        aws_access_key_id     = self.creds.get("AccessKeyId",     "")
                        aws_secret_access_key = self.creds.get("SecretAccessKey", "")
                        aws_session_token     = self.creds.get("SessionToken",    "")
                        aws_token_expiration  = self.creds.get("Expiration",      "")
                        # write with indentation
                        prof_tag = f"[{sts_profile_name}]\n"
                        ak_str    = f"aws_access_key_id={aws_access_key_id}\n"
                        asak_str  = f"aws_secret_access_key={aws_secret_access_key}\n"
                        token_str = f"aws_session_token={aws_session_token}\n"
                        exp_str   = f"expiration_datetime={aws_token_expiration}\n"
                        # write begin tag
                        fout.write(f"# ${{{{{{ key={self.target_tag_name} [auto update by updsts]\n")
                        fout.write(prof_tag)
                        fout.write(ak_str)
                        fout.write(asak_str)
                        fout.write(token_str)
                        fout.write(exp_str)
                        # write end tag
                        fout.write(f"# $}}}}}} [auto update by updsts]\n")
                        logger.info(f"added  : key='{self.target_tag_name}', profile='{sts_profile_name}'")
                        updated_profile_info = {
                            "updated_profile_name" : sts_profile_name,
                            "aws_access_key_id"    : self.creds.get("AccessKeyId", ""),
                            "aws_token_expiration" : self.creds.get("Expiration",      "")
                        }

            # replace original file
            logger.info(f"modifying : '{self.credential_file_path}'")
            # copy file permissions
            st = os.stat(self.credential_file_path)
            os.chmod(out_path, st.st_mode)
            # os.replace is atomic, so the credentials file never goes missing even if this fails
            os.replace(out_path, self.credential_file_path)
        except BaseException as e:
            # remove the temp file (it may contain other profiles' secrets); the original is left untouched
            out_path.unlink(missing_ok=True)
            if isinstance(e, UnicodeDecodeError):
                raise ValueError(credential_decode_error_message(self.credential_file_path, e)) from e
            raise
        logger.info(f"modified  : '{self.credential_file_path}'")

        return updated_profile_info

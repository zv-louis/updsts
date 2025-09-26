# encoding : utf_8_sig

import os
import re

from argparse import ArgumentParser
from pathlib import Path

from .logutil import get_logger

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
    def update_credential_file(self) -> dict[str, str] | None:
        """
        update the credentials file
        """
        logger = get_logger()
        bgn_tag = re.compile(r"^(\s*)#\s+\$\{\{\{\s+key=([\w\-_]+)\s+.*\r?\n")
        end_tag = re.compile(r"^(\s*)#\s+\$\}\}\}\s+.*\r?\n")
        out_path = self.credential_file_path.with_suffix(".tmp")
        updated_profile_info = None
        with self.credential_file_path.open(mode='r', encoding="utf-8") as fin:
            with out_path.open(mode='w', encoding="utf-8") as fout:
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
                            matched_whitespaces = obj.group(1)
                            matched_key         = obj.group(2)
                            if (self.target_tag_name == matched_key):
                                print(f"found key : key='{self.target_tag_name}'")
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
                    logger.warning(f"key='{self.target_tag_name}' not found in the credential file.")
                    # create section
                    fout.write(f"\n[{self.target_tag_name}_sts]\n")
                    aws_access_key_id     = self.creds.get("AccessKeyId",     "")
                    aws_secret_access_key = self.creds.get("SecretAccessKey", "")
                    aws_session_token     = self.creds.get("SessionToken",    "")
                    aws_token_expiration  = self.creds.get("Expiration",      "")
                    # write with indentation
                    prof_tag = f"[{sts_profile_name}]\n"
                    fout.write(prof_tag)
                    ak_str    = f"aws_access_key_id={aws_access_key_id}\n"
                    asak_str  = f"aws_secret_access_key={aws_secret_access_key}\n"
                    token_str = f"aws_session_token={aws_session_token}\n"
                    exp_str   = f"expiration_datetime={aws_token_expiration}\n"
                    # write begin tag
                    fout.write(f"# ${{{{{{ key={self.target_tag_name} [auto update by updsts]\n")
                    fout.write(ak_str)
                    fout.write(asak_str)
                    fout.write(token_str)
                    fout.write(exp_str)
                    # write end tag
                    fout.write(f"# $}}}}}} [auto update by updsts]\n")
                    logger.info(f"added  : key='{self.target_tag_name}_sts'")
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
        self.credential_file_path.unlink()
        out_path.rename(self.credential_file_path)
        logger.info(f"modified  : '{self.credential_file_path}'")
        if out_path.exists():
            out_path.unlink()

        return updated_profile_info

#!/usr/bin/env python3
# Run this script from a directory with encrypted files and it will attempt to decrypt them

# not my code
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sh import touch, gpg, echo, awk, sha256sum, ErrorReturnCode_2

# my code
from encrypt_cwd import salt, nonce_cleartext_filename, nonce_encrypted_filename, \
                        ignored_files, examine, add_line_if_not_present, getkey, yes_or_no, \
                        update_sha

# this is the decryption command
def get_cleartext(filename, key):
    print(f"decrypting {filename}...")
    try:
        cleartext = str(gpg(echo(key), ['--passphrase-fd', '0',
                                         '--batch', '--yes',
                                        '--decrypt', f'./{filename}']))

    except ErrorReturnCode_2 as err:
        print(f"Error while decrypting {filename}:")
        print(err)
        return err
    else:
        return cleartext

# only decrypt encrypted stuff, also ignore directories
def ignore(file):
    if os.path.isdir(file) or (not file.endswith('.asc')) or file in ignored_files:
        return True
    else:
        return False


def main():

    ## Scan the current directory for decryptions that can be done
    ###

    nonce_asc_found = any(examine(lambda x: x == nonce_encrypted_filename))
    examine(lambda x: ignore(x), prompt="Ignoring: ")
    to_decrypt = { y : None for y in examine(lambda x: not ignore(x), prompt="Decrypting: ") }

    if not to_decrypt:
        print("Nothing to do, exiting")
        sys.exit(2)

    ## Prompt the user for their passphrase, use scrypt to generate a key from it
    ###

    key = getkey()

    ## Ensure .gitignore ignores the cleartext files
    ###

    for filename in to_decrypt:
        touch('.gitignore')
        decrypted_filename = filename[0:-4] # 'foo.asc' - '.asc' = 'foo'
        add_line_if_not_present(decrypted_filename, '.gitignore')
        to_decrypt[filename] = decrypted_filename

    if not nonce_asc_found:
        print(f"{nonce_encrypted_filename} not found.  Skipping passphrase consistency check.")
    else:
        cleartext = get_cleartext(nonce_encrypted_filename, key)

        if type(cleartext) is ErrorReturnCode_2:
            print(f"Unable to decrypt ./{nonce_encrypted_filename}, this could be a bad passphrase.")
            if not yes_or_no("Try Anyway?"):
                exit(4)
        else:
            print(f"Successfully decrypted ./{nonce_encrypted_filename}.  You're using the right passphrase for this directory.")
        print()

    ## Decrypt files
    ###

    first_error = None
    for ciphertext_filename, cleartext_filename in to_decrypt.items():

        cleartext_or_err = get_cleartext(ciphertext_filename, key)

        if type(cleartext) is ErrorReturnCode_2:
            print(f"Error while decrypting {ciphertext_filename}:")
            print(cleartext_or_err)
            if not first_error:
                first_error = err
        else:

            with open(cleartext_filename, 'w') as file:
                file.write(cleartext_or_err)

            sha256 = update_sha(cleartext_filename)
            print(f"sha256sum: {sha256}")

            print(f"decrypted file name: {cleartext_filename}")

            print('\ndone')
        print()

    if not first_error:
        print("Be careful that you don't edit these in a way that will create hidden copies.\n"
              "For vim, consider:\n"
              '''    alias vimcognito='vim -i NONE -u DEFAULTS -U DEFAULTS -n -c "set nomodeline"'\n'''
              "\n")
    else:
        print("Throwing first error encountered...")
        raise first_error

if __name__ == "__main__":
    main()

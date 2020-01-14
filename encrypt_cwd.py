#!/usr/bin/env python3
# Run this script from a directory with encrypted files and it will attempt to encrypt them

import random
import string
import base64
from getpass import getpass
import sys
import os
import re

from argon2 import argon2_hash as argon2
import scrypt
from sh import gpg, echo, sha256sum, shred, rm, touch, awk, ErrorReturnCode_2

## Constants
###

# Generate a pseudorandom string:
#     cat /dev/urandom | tr -dc 'a-zA-Z0-9!@#$%^&*~' | fold -w 32 | head -1
# and replace the value below with it

# This ensures that attacks against Alice's passphrase are useless for reuse against Bob
# If Alice has powerful enemies, and you're Bob, you'll want to make this string unique to you
salt='zfd8RafsLjMOPyigWARwadAujJ7daGX9'

nonce_cleartext_filename = '.nonce'
nonce_encrypted_filename = f'{nonce_cleartext_filename}.asc'
ignored_files = ['hint', nonce_cleartext_filename, nonce_encrypted_filename, '.gitignore']

## Helper Functions
###

# it would be bad if a user accidentally decrypted with one passphrase and encrypted with another
# we use the ability to decrypt the nonce as an indicator that they're using the same passphrase they did previously
def generate_nonce(first_key):
    second_key = getkey(prompt='Confirm Password: ')
    if first_key != second_key:
        print("passphrases don't match")
        exit(1)

    print(f"Creating ./{nonce_encrypted_filename} with random contents")
    nonce = random_string(random.randint(1000,10000))

    echo(nonce, _out=nonce_cleartext_filename)

    found = gpg(echo(first_key), ['--s2k-mode', '3',
                            '--s2k-count', '65011712',
                            '--s2k-digest-algo', 'SHA512',
                            '--s2k-cipher-algo', 'AES256',
                            '--armor', '--symmetric',
                            '--passphrase-fd', '0',
                            '--batch', '--yes',
                            f'{nonce_cleartext_filename}'])
    rm(nonce_cleartext_filename)

def update_sha(filename):
    sha_filename = f'{filename}.sha256'
    sha256 = str(awk(sha256sum(filename),
                     '{print $1}', _out=sha_filename, _tee=True)).strip()
    return sha256

# which files are ready to be encrypted?
def examine(predicate, prompt=None):

    found = []

    notified = False
    for file in os.listdir():
        if predicate(file):
            found.append(file)
            if prompt:
                if not notified:
                    print(prompt)
                    notified = True
                print('    - ', file)
    if notified:
        print()

    return found

# return true if file is a directory, already encrypted, or a special file
def ignore(file):
    if os.path.isdir(file) or file.endswith('.asc') or file.endswith('.sha256') or file in ignored_files:
        return True
    else:
        return False

# prompt the user for a passphrase, and use scrypt to generate a key from it
def getkey(prompt='Password: '):

    with open('hint', 'r') as hint:
        print(f"Hint: {hint.read().strip()}")

    passphrase = getpass(prompt=prompt)

    print("Generating Key...", end='')
    sys.stdout.flush()

    # use scrypt to generate a key from the passphrase
    # If this doesn't take a second or so, try increasing the exponent until it does
    N=2**16
    r=16
    p=1
    buflen=64

    step1 = base64.b64encode(scrypt.hash(passphrase, salt, N=N, r=r, p=p, buflen=buflen)).decode('utf-8')

    print(".", end="")
    sys.stdout.flush()

    time=2048
    mem=128
    threads=2
    buflen=128
    step2 = base64.b64encode(argon2(step1, salt, t=time, m=mem, p=threads, buflen=buflen)).decode('utf-8')

    print(".done")
    return step2

# a function for manipulating .gitignore
def add_line_if_not_present(string, filename):
    with open(filename, "r+") as file:
        for line in file:
            if string in line:
               break
        else: # not found, we are at the eof
            file.write(string + '\n') # append missing data
            print(f"    adding {string} to {filename}")

# prompts the user
def yes_or_no(question):
    while "Y or N please...":
        reply = str(input(question+' (y/n): ')).lower().strip()
        if reply[:1] in 'y':
            return True
        if reply[:1] == 'n':
            return False

# for generating the nonce
def random_string(length):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))

def main():

    ## Find Targets
    ###

    nonce_asc_found = any(examine(lambda x: x == nonce_encrypted_filename))
    examine(lambda x: ignore(x), prompt="Ignoring: ")
    to_encrypt = examine(lambda x: not ignore(x), prompt="Encrypting: ")

    if not to_encrypt:
        print("Nothing to do, exiting")
        sys.exit(2)

    ## Generate Key
    ###

    key = getkey()
    print()

    ## Ensure gitignore ignores the cleartext files
    ###

    for file in to_encrypt:
        touch('.gitignore')
        add_line_if_not_present(file, '.gitignore')

    ## Check if key correct
    ###

    if not nonce_asc_found:
        print(f"./{nonce_encrypted_filename} not found, this is the first use of this passphrase to encrypt the files in this directory.")
        print()
        generate_nonce(key)
        print()

    else:
        print(f"Decrypting ./{nonce_encrypted_filename}")
        try:
            _ = str(gpg(echo(key), ['--passphrase-fd', '0',
                                        '--batch', '--yes',
                                        '--decrypt', f'./{nonce_encrypted_filename}']))
        except ErrorReturnCode_2:
            print(f"Unable to decrypt ./{nonce_encrypted_filename}\n"
                  "The passphrase you're about to encrypt with is different than the one previously used.")
            if not yes_or_no("Do you want to continue?"):
                sys.exit(3)
            else:
                print(f"Ok, regenerating the ./{nonce_encrypted_filename} so you don't see this warning next time.")
                generate_nonce(key)

        else:
            print("Success, you're using the right passphrase for this directory.")

    ## Encrypt files
    ###

    for file in to_encrypt:

        print(f"encrypting {file}...")

        sha256 = update_sha(file)
        print(f"sha256sum: {sha256}")
        gpg(echo(key), ['--s2k-mode', '3',
                        '--s2k-count', '65011712',
                        '--s2k-digest-algo', 'SHA512',
                        '--s2k-cipher-algo', 'AES256',
                        '--armor', '--symmetric',
                        '--passphrase-fd', '0',
                        '--batch', '--yes',
                        file])
        print(f"created encrypted file: {file}.asc")

        if yes_or_no(f"Shred {file}?"):
            shred(file)
            rm(file)

    print()
    print("If any copies of the cleartext were made, consider deleting them with `shred -u` instead of `rm`")

if __name__ == "__main__":
    main()

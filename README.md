# gitcrypt

This is a framework for encrypting secrets and storing them in git.  It might be a bad idea altogether.  It might also be an OK idea, with bad ideas hiding inside--use it only if you understand it.

## System Dependencies

This project assumes that you have [gpg](https://gnupg.org/download/) installed.

## Installing Python Dependencies

This is probably enough for most environments
```
pip install -r requirements.txt
```

If you're using [tails](https://tails.boum.org/) you might need:
```
sudo apt update && sudo apt install python3-pip python3-setuptools python3-dev gcc libssl-dev
sudo torsocks pip install -r requirements.txt
```

## Usage

Test out the workflow by walking through the section below.  If you like it, fork this repo, delete the test folder, and start making encrypted folders of your own.

### Decrypt-View-Edit-Encrypt-Push

I've included a sample payload for you to decrypt. To see how it works, walk through these steps:

```
cd test
../decrypt_cwd.py
# you should see the passphrase hint: foo
# type the passphrase: bar
# payload.txt.asc will be decrypted into payload.txt, go ahead and edit this file
../encrypt_cwd.py
# you should see the passphrase hint: foo
# type the passphrase: bar
# when prompted to shred payload.txt, say yes
git status
```

You'll notice that payload.txt.asc and payload.txt.sha256 have changed.  If you used a good passphrase, I believe these files are safe to push to github.  It's probably best to use a private repo, but the goal is that your secrets are now encrypted so heavily that it wouldn't matter

### Creating a new encrypted folder

1. create the folder within the repo
2. create a file called `hint` with the password hint
3. create a file with secrets in it (your filenames are visible even when encrypted, be careful)
4. run `../encrypt_cwd.py`
5. run `git status` and make sure that your cleartext files don't show up (the script should create .gitignores for them)
6. run `../decrypt_cwd.py`

### A few things to think about

[encrypt_cwd.py](encrypt_cwd.py) contains a salt which you should regenerate if you fork this project.  Also, you should probably audit that code while you're in there (and [decrypt_cwd.py](decrypt_cwd.py) while you're at it).  I'll do my best to answer questions in the form of issues, but I won't be held responsible for data loss or compromise.



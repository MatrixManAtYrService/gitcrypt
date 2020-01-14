# gitcrypt

This is a framework for encrypting secrets and storing them in git.  It might be a bad idea altogether.  It might also be an OK idea, with bad ideas hiding inside--use it only if you understand it.

## System Dependencies

Assumes that you have [gpg](https://gnupg.org/download/) installed.

## Installing Python Dependencies

This is probably enough for most environments
```
pip install -r requirements.txt
```

If you're on tails, you might need:
```
sudo apt update && sudo apt install python3-pip python3-dev gcc libssl-dev
sudo torsocks pip install -r requirements.txt
```

### From this repo

I've noticed that [tails](https://tails.boum.org/) python3 doesn't include pip.  Maybe this is to prevent you from pulling in untrustworthy software.  Maybe it's a bug.  Either way, to work around this I've downloaded the two dependencies and included copies of them in this repo.  I make no promises that the packages I've downloaded will work for you.  They work for me.  You should redownload them yourself just in case I've sneaked something nasty into the ones here (I haven't).

I downloaded them like this:
```
pip download sh
pip download scrypt
```

To unpack them:
```
unzip sh-1.12.14-py2.py3-none-any.whl
tar xvfz scrypt-0.8.13.tar.gz
```

The import sections of [encrypt_cwd.py](encrypt_cwd.py) and [decrypt_cwd.py](decrypt_cwd.py) modify the PYTHONPATH to point to these dependencies, you shouldn't have to do anything further.

## Usage

Test out the workflow by walking through the section below.  If you like it, fork this repo, delete the test folder, and start making folders of your own.  New encrypted folders will at least need a file called `hint` in them.

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

You'll notice that payload.txt.asc and payload.txt.sha256 have changed.  If you used a good passphrase, I believe these files are safe to push to github.  It's probably best to use a private repo, but your passphrase has been [stretched](https://en.wikipedia.org/wiki/Key_stretching) so that it will be resistant to offline attacks.


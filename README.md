# Organizing MP3s

A few hours worth of work to take MP3 files (which were probably acquired from Napster 20+ years ago), figure out what they actually are, then organize them into folders by artist.

This will probably be useful if you are old-school and listen to music with [Winamp](https://winamp.com) or [VLC](https://www.videolan.org).

Or maybe you want to stream your music from Plex (e.g., with [Plexamp](https://plexamp.com)) instead of using [Apple Music](https://music.apple.com), [Spotify](https://www.spotify.com), [Pandora](https://www.pandora.com), [YouTube Music](https://music.youtube.com), or one of the other popular streaming services since you already have the damn songs anyway.

This is itch-and-scratch-ware. I had an itch, then I scratched it. Now it doesn't itch anymore. _Issues_ are disabled. You can submit a PR if you want to see something added, or you can fork it and do whatever you want with it.

## What does this do

1. Use AcoustID to create an acoustic fingerprint and compare it to the MusicBrainz database.
1. Get back the results.
1. Look at the ID3 tags (if any) and merge them into the results.
1. Which results do we see the most? Is there an obvious winner? If so, use it.
1. Not an obvious winner? Look at the top results, and compare them against the filename using Levenshtein Distance.
1. Now that we have a high-probability artist and song title, create folders and move files as appropriate.
1. If there are any failures along the way, stop processing that file, and move onto the next file. This allows _you_ to do manual cleanup instead of having this script probably screw it up on your behalf.

## What does this NOT do

* It does not support writing ID3 tags back into the MP3 file (although it could).
* It does not support formats beyond MP3 (e.g., AAC, M4A) (although it could).
* It does not do anything with albums. Album metadata is generally a mess when it comes to homegrown databases (e.g., AcoustID).
* Aim for perfection. We're using databases that were developed _outside_ the music industry, by music fans. If you're looking for data infallibility, be prepared to spend some coin on a [Gracenote](https://www.gracenote.com/music/music-recognition/) license.

## Requirements

### Prerequisites

* Python 3.6 or newer, with `pip`.
* Download [Chromaprint-fpcalc](https://acoustid.org/chromaprint) for your platform and CPU architecture, and add it to your path. If you can't add it to your path, set the `FPCALC` environment variable to point to it. (This is a requirement of [pyacoustid](https://github.com/beetbox/pyacoustid).)
* [Register a new application](https://acoustid.org/login?return_url=https%3A%2F%2Facoustid.org%2Fnew-application) on AcoustID, and save your API key as the value of the `ACOUSTICID_KEY` environment variable.

If you want to further develop this, there is a `yapf` definition to help you maintain consistency in formatting.

### Installation (macOS/Linux)

It's a very, very standard Python installation. However, it's **critical** that you don't confuse any possible Python2 installation with a Python3 installation. Python2 is _explicitly unsupported_.

#### Activate an isolated `virtualenv` virtual environment

> ℹ️ **NOTE:** While I'm using `python3` and `pip3` in these instructions, they _may_ be called `python` or `pip` on your system. Adjust as necessary.

1. Install `virtualenv` using `pip`.

    ```bash
    pip3 install -U virtualenv
    ```

1. Create a new, isolated `virtualenv` virtual environment for running this Python code, so that it doesn't impact any other Python code you have on your system.

    ```bash
    virtualenv .venv
    ```

1. Now _activate_ your isolated `virtualenv` virtual environment.

    ```bash
    source .venv/bin/activate
    ```

    (You may need to substitute `activate` ([Bash](https://en.wikipedia.org/wiki/Bash_(Unix_shell))) for `activate.csh` ([C-shell](https://en.wikipedia.org/wiki/C_shell)), `activate.fish` ([Fish](https://en.wikipedia.org/wiki/Friendly_interactive_shell)), or `activate.ps1` ([Windows PowerShell](https://en.wikipedia.org/wiki/PowerShell)), depending on your platform.)

#### Working inside your isolated `virtualenv` virtual environment

> ℹ️ **NOTE:** Now that we're _inside_ the isolated `virtualenv` virtual environment, `pip` is always called `pip`, and `python` is always called `python`. Don't worry about the `3`s anymore.

1. Validate that it's working. If you get a result, you're good.

    ```bash
    which pip | grep ".venv/bin/pip"
    ```

1. Install the Python packages that this script depends on.

    ```bash
    pip install -r requirements.txt
    ```

    Some of these dependencies are GPL-licensed. This will matter more in the "Licensing" section, at the end of this document.

## Basic usage (macOS/Linux)

> ℹ️ **NOTE:** This snippet assumes you're using GNU tools, which do not ship by default on macOS (which uses BSD tools). If you're using macOS, see “[Using GNU command line tools in macOS instead of FreeBSD tools](https://ryanparman.com/posts/2019/using-gnu-command-line-tools-in-macos-instead-of-freebsd-tools/)” for more information. This script should work without modification in common Linuxes, as well as the [Windows Subsystem for Linux (WSL2)](https://docs.microsoft.com/en-us/windows/wsl/install-win10).

This will automatically move/organize the MP3s into _artist_ folders (not _album artist_) and rename the files to match the _song title_.

### One file

Let's say you have a filename called `09 Paradise in Me.mp3` (Napster, remember?). You can run the script against this one file to test it out.

**Starting File structure (relevant files only):**

```plain
.
├── 09 Paradise in Me.mp3
└── aidmatch.py
```

**Command:**

```bash
./aidmatch.py "09 Paradise in Me.mp3"
```

**Output:**

```plain
09 Paradise in Me.mp3 ~> "Paradise in Me" by K's Choice
```

**Ending File structure (relevant files only):**

```plain
.
├── K's Choice
│   └── Paradise in Me.mp3
└── aidmatch.py
```

### Find all MP3s in the current directory and pass them through the script

This script does not support `*`, such as `*.mp3`. It only supports one file at a time. However, we can use `find` to discover all of the MP3s, then `xargs` to execute this script once-for-each-file.

**Starting File structure (relevant files only):**

```plain
.
├── 09 Paradise in Me.mp3
├── 09 The Click Five - Just the Girl.mp3
├── 10 Far Behind.mp3
├── 10 Higher.mp3
├── 11 Only God Knows Why.mp3
└── aidmatch.py
```

**Command:**

```bash
find . -maxdepth 1 -type f -name "*.mp3" -print0 | xargs -0 --no-run-if-empty -I% ./aidmatch.py "%"
```

**Output:**

```plain
./10 Far Behind.mp3 ~> "Far Behind" by Candlebox
./09 Paradise in Me.mp3 ~> "Paradise in Me" by K’s Choice
./11 Only God Knows Why.mp3 ~> "Only God Knows Why" by Kid Rock
./10 Higher.mp3 ~> "Higher" by Creed
./09 The Click Five - Just the Girl.mp3 ~> "Just the Girl" by The Click Five
```

**Ending File structure (relevant files only):**

```plain
.
├── Candlebox/
│   └── Far Behind.mp3
├── Creed/
│   └── Higher.mp3
├── K's Choice/
│   └── Paradise in Me.mp3
├── Kid Rock/
│   └── Only God Knows Why.mp3
├── The Click Five/
│   └── Just the Girl.mp3
└── aidmatch.py
```

### Find all MP3s in the current directory AND all child directories, and pass them through the script

**WAIT!** This will also include any files that you have _already_ run through in a previous run. Move those out of the way first.

**Starting File structure (relevant files only):**

```plain
.
├── sub/
│   └── subsub/
│       └── subsubsub/
│           ├── Candlebox/
│           │   └── Far Behind.mp3
│           ├── Creed/
│           │   └── Higher.mp3
│           ├── K’s Choice/
│           │   └── Paradise in Me.mp3
│           ├── Kid Rock/
│           │   └── Only God Knows Why.mp3
│           └── The Click Five/
│               └── Just the Girl.mp3
└── aidmatch.py
```

**Command:**

```bash
find . -type f -name "*.mp3" -print0 | xargs -0 --no-run-if-empty -I% ./aidmatch.py "%"
```

**Output:**

```plain
./sub/subsub/subsubsub/K’s Choice/Paradise in Me.mp3 ~> "Paradise in Me" by K’s Choice
./sub/subsub/subsubsub/Candlebox/Far Behind.mp3 ~> "Far Behind" by Candlebox
./sub/subsub/subsubsub/Kid Rock/Only God Knows Why.mp3 ~> "Only God Knows Why" by Kid Rock
./sub/subsub/subsubsub/Creed/Higher.mp3 ~> "Higher" by Creed
./sub/subsub/subsubsub/The Click Five/Just the Girl.mp3 ~> "Just the Girl" by The Click Five
```

**Ending File structure (relevant files only):**

```plain
.
├── Candlebox/
│   └── Far Behind.mp3
├── Creed/
│   └── Higher.mp3
├── K’s Choice/
│   └── Paradise in Me.mp3
├── Kid Rock/
│   └── Only God Knows Why.mp3
├── sub/
│   └── subsub/
│       └── subsubsub/
│           ├── Candlebox/
│           ├── Creed/
│           ├── K's Choice/
│           ├── Kid Rock/
│           └── The Click Five/
├── The Click Five/
│   └── Just the Girl.mp3
└── aidmatch.py
```

### Dealing with errors or missing data

In this example, you may have a file (e.g., `Munkafust - Down For Days(1).mp3`) who's Acoustic ID doesn' match anything in the AcoustID database. It will fallback to using the ID3 tags (exclusively). If there are also no ID3 tags, this script will give up and let you deal with it yourself.

There may also be some files where Chromaprint cannot determine the acoustic fingerprint of the song _at all_.

**Command:**

```bash
./aidmatch.py "Fuel - Shimmer.mp3"
```

**Output:**

```plain
!!!!!!!!!! fingerprint could not be calculated (Fuel - Shimmer.mp3)
```

Maybe you can try to identify it with [Shazam](https://www.shazam.com) or [SoundHound](https://www.soundhound.com)? Or (ahem) _obtain_ a better quality version of the file?

## License

This is a little tricky, so I'll do my best to be specific.

I support intellectual property, therefore, I _choose_ not to license my software under "Free Software" licenses such as those from the [Free Software Foundation](https://fsf.org) (e.g., GPL).

Instead, I support empowering people to build the best software they can without the intellectual property restrictions required by the GPL. For this purpose, I tend to use "Open Source" licenses such as MIT, BSD, or Apache 2.0 which essentially boil down to "use this software for whatever you want; hide your source code if you want; don't be a dick" (I am not a lawyer; this is not legal advice).

The `aidmatch.py` file in this repo is essentially a completely rewritten sample taken from the MIT-licensed [pyacoustid](https://github.com/beetbox/pyacoustid) project. As such, _this source code in this repository_ is MIT licensed because that's the license I _choose_.

Here's the wrinkle: GPLv2 has a provision about code that is intermingled with GPLv2 code, in that it becomes GPL code itself. However this has limits at the process boundary. This precludes the output of one app being passed as the input to another app (e.g., shell piping). However, because Python is interpreted, and all Python code in this project runs in the same _process_, the code **while it's being run** is GPLv2.

So, if you plan to download and run this code as-is with all of its dependencies, it's GPLv2. If you find this code on GitHub and just want to copy bits of it without necessarily _running_ it, it's MIT.

At least, that's my intention. This stance is based on my understanding of [Implications of using GPL-licensed client-side JavaScript](http://greendrake.info/#nfy0) and [The JavaScript Trap](https://www.gnu.org/philosophy/javascript-trap.html) — which apply (I _believe_) because Python code is also interpreted (although it's not explicitly pushed to user's computers like JavaScript-on-a-webpage is.)

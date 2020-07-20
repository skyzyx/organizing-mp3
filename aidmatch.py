#! /usr/bin/env python3

# MIT license
#
# Copyright 2011, Adrian Sampson.
# Copyright 2020, Ryan Parman.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from pprint import pprint
from collections import OrderedDict
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from natsort import natsort_keygen
from itertools import chain
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import acoustid
import json
import os
import shutil
import sys

# API key for this demo script only. Get your own API key at AcoustID for your
# application, then save it as an environment variable.
# https://acoustid.org/my-applications
API_KEY = os.environ.get('ACOUSTICID_KEY')

def fetch_acoust_id(filename):
    """
    Accepts an absolute or relative file system path as `filename`.

    This function will use the `fpcalc` executable installed on the system to
    generate an acoustic fingerprint, send that fingerprint to the AcoustID
    service (which MusicBrainz) uses on the backend, and yield back a generated
    tuple datatype.

    The yielded generator of tuples is the returned value.
    """

    try:
        results = acoustid.match(API_KEY, filename, force_fpcalc=True, parse=True)
    except acoustid.NoBackendError:
        print("!!!!!!!!!! chromaprint library/tool not found", file=sys.stderr)
        sys.exit(1)
    except acoustid.FingerprintGenerationError:
        print(
            f"!!!!!!!!!! fingerprint could not be calculated ({filename})",
            file=sys.stderr
        )
        sys.exit(1)
    except acoustid.WebServiceError as exc:
        print("!!!!!!!!!! web service request failed:", exc.message, file=sys.stderr)
        sys.exit(1)

    return results

def get_most_likely_result(d, filename):
    """
    We want to have one, clear, unambiguous "winner". If the AcoustID API
    returns enough matches that multiple values have come back as a "tie",
    we need to build a "tie-breaker".
    """

    # Here, we will figure out if there are multiple artists/titles with the
    # same number of results.
    dmap = {}
    for key, value in d.items():
        dmap.setdefault(str(value), set()).add(key)

    # Use "reverse natural sorting", meaning that 2 should come after 10, not
    # before. We want the largest "natural" number to be at the beginning of
    # the list.
    natsort_key = natsort_keygen()
    dmap = OrderedDict(sorted(dmap.items(), key=natsort_key, reverse=True))

    # Is this list empty? Nothing to do. Bail out.
    if len(list(dmap)) == 0:
        print(
            f"!!!!!!!!!! cannot find artist for <{filename}>. bailing out.",
            file=sys.stderr
        )
        sys.exit(1)
    else:
        # Figure out the first key in the map (which would be the highest-rated
        # names), then once we have that key, use it to lookup the value in the
        # map.
        winners = list(dmap[list(dmap)[0]])

        # Do we have one, clear, unambiguous winner?
        if len(winners) == 1:
            return winners[0]

        # If not, fall back to using a "Levenshtein Distance" algorithm to
        # compare the available matches to the filename (hoping that there's a
        # clue inside the filename that it can base its decision on).
        # https://en.wikipedia.org/wiki/Levenshtein_distance
        elif len(winners) > 1:
            selection, score = process.extractOne(filename, winners, scorer=fuzz.token_sort_ratio)
            return selection

def main(filename):
    # Fetch the results from AcoustID.
    results = fetch_acoust_id(filename)

    # Set up some variables we're about to use.
    artists = {}
    titles = {}

    # Iterate over the list of results, where each result is a tuple of 4.
    # As we iterate, we extract the individual pieces of the tuple into discrete
    # variables that are valid for this specific iteration of the loop.
    for score, rid, title, artist in results:

        # As long as the Artist and Title aren't empty, and the score comes back
        # above 90% certainty...
        if (title != None) and (artist != None) and (int(score * 100) > 90):

            # We've never encountered this artist before, so add it to the list
            # for the first time.
            if artist not in artists:
                artists[artist] = 1

            # We've never encountered this title before, so add it to the list
            # for the first time.
            if title not in titles:
                titles[title] = 1

            # We've definitely seen this artist and title before. Increment.
            artists[artist] += 1
            titles[title] += 1

    # Also lookup the existing ID3 tags and use those as input. Built-in ID3
    # tags are heavier-weight than the acoustic fingerprinting results.
    id3tags = MP3(filename, ID3=EasyID3)

    # It's possible to have zero or more artist ID3 tags.
    if "artist" in id3tags:
        for a in id3tags["artist"]:
            if a not in artists:
                artists[a] = 2
            else:
                artists[a] += 2

    # It's possible to have zero or more title ID3 tags.
    if "title" in id3tags:
        for t in id3tags["title"]:
            if t not in titles:
                titles[t] = 2
            else:
                titles[t] += 2

    # See function above for explanation.
    artist = get_most_likely_result(artists, filename)
    title = get_most_likely_result(titles, filename)

    # Correct this
    artist = artist.replace("; ", " feat. ")

    # Print it out to the CLI.
    print(
        '{filename} ~> "{title}" by {artist}'.format(
            filename=filename,
            artist=artist,
            title=title,
        )
    )

    # Create directory named after our detected artist.
    try:
        os.mkdir(f"./{artist}", 0o777)
    except FileExistsError:
        pass

    # Move the audio file into that directory while also renaming it to the
    # title of the song.
    shutil.move(filename, f"./{artist}/{title}.mp3")

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main(sys.argv[1])

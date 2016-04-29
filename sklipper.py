import sys
import cv2
import sqlite3
import argparse
import math

# TODO save clips as new video file


APPNAME = "sklipper"


class Video(object):
    """Represents a video and the database of events associated with it.
    """
    def __init__(self, filename):
        """Open a video file and prepare it for playback.

        Args:
            filename: The video file to open.

        Raises:
            cv2.error: An error occurred opening the video file.
        """
        self._filename = filename
        self._video = cv2.VideoCapture(self._filename)
        if not self._video.isOpened():
            raise cv2.error
        self._title = "%s - %s" % (APPNAME, self._filename)
        # TODO use a different database per video hash?
        self._db = VideoDatabase("sklipper.db")

    def play(self, events=[]):
        """Play the video (or a list of events from the video).

        Will play the entire video if the list of events is empty,
        otherwise only the specified events will be played.

        Args:
            events: Optional list of events from the video to play.
        """
        if events:
            for event in events:
                # TODO what about playing only specific clips from an event?
                # or clips tagged in some fashion
                for clip in self._db.load(event):
                    self._play_clip(clip["start"], clip["end"])
        else:
            self._play_clip(0, sys.maxint)

    def _play_clip(self, start, end):
        """Play a single clip from the video.

        Will play the portion of the video specified by the time indices
        given. If they extend past the end of the video then they will be
        clamped.

        Args:
            start: milliseconds to start playback from.
            end: milliseconds to end playback at.
        """
        self._video.set(cv2.CAP_PROP_POS_MSEC, start)
        while self._video.get(cv2.CAP_PROP_POS_MSEC) < end:
            ret, frame = self._video.read()
            if frame is None:
                return
            cv2.imshow(self._title, frame)
            if not self._keypress():
                return

    def _keypress(self):
        """Wait briefly for a keypress and process it if required.

        Check if the user has pressed a key and if so perform the action
        associated with that key press. Actions include saving an event
        or quitting video playback.

        Returns:
            True: video playback should continue
            False: video playback should stop
        """
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return False
        elif key >= ord('1') and key <= ord('9'):
            # TODO better event values than the number that was pressed
            event = key - 48
            position = self._video.get(cv2.CAP_PROP_POS_MSEC)
            # TODO adjust start and end based on event type
            # TODO what about toggling record on/off
            start = math.floor(position - 2000)
            if start < 0:
                start = 0
            end = math.floor(position + 5000)
            self._db.save(event, start, end)
        return True


class VideoDatabase(object):
    def __init__(self, filename, clobber=False):
        self._filename = filename
        self._db = sqlite3.connect(self._filename)
        self._db.row_factory = sqlite3.Row
        cursor = self._db.cursor()
        if clobber:
            cursor.execute('''DROP TABLE clips''')
        # TODO events should have unique identifiers, other tags/metadata
        cursor.execute('''CREATE TABLE IF NOT EXISTS
                          clips (event integer, start integer, end integer)''')
        self._db.commit()

    def save(self, event, start, end):
        """Save a event clip with the given start and end times.

        Args:
            event: event id to save this event clip as.
            start: milliseconds to start the event at.
            end: milliseconds to end the event at.
        """
        print "saving", event, start, end
        cursor = self._db.cursor()
        cursor.execute('''INSERT INTO clips (event, start, end)
                          VALUES (?, ?, ?)''', [event, start, end])
        self._db.commit()

    def load(self, event):
        """Load a list of clips with the given event id.

        Args:
            event: event id to load from the database.

        Returns:
            A list of all clips matching the given event id, or an empty list.
        """
        cursor = self._db.cursor()
        cursor.execute('''SELECT * FROM clips WHERE event = ?''', [event])
        return cursor.fetchall()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("--event", type=int, action="append",
            help="play only events of this type (may be given multiple times)")
    args = parser.parse_args()

    try:
        video = Video(args.filename)
    except cv2.error as e:
        print "failed to open video, aborting"
        sys.exit(1)

    video.play(args.event)

    # dump the internal database to stdout for debugging
    cursor = video._db._db.cursor()
    for row in cursor.execute("SELECT * FROM clips"):
        print row

    #video.release()
    cv2.destroyAllWindows()

# vim: set ts=4 sw=4 hlsearch expandtab :

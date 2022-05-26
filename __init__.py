from concurrent.futures import Future
from aqt.mediacheck import MediaChecker
from aqt import mw
from aqt.utils import tooltip

TAGNAME = "MissingMedia"


def on_finished(self: MediaChecker, fut: Future) -> None:
    self._on_finished(fut)
    output = fut.result()
    missing = output.missing
    mw.col.tags.remove(TAGNAME)
    nids = []
    for filename in missing:
        for nid, mid, flds in mw.col.db.execute("select id, mid, flds from notes"):
            media_refs = mw.col.media.filesInStr(mid, flds)
            if filename in media_refs:
                nids.append(nid)
    mw.col.tags.bulkAdd(nids, TAGNAME)
    tooltip(f"Tagged {len(nids)} notes with {TAGNAME}")


def on_check(self: MediaChecker) -> None:
    self.progress_dialog = self.mw.progress.start()
    self._set_progress_enabled(True)
    self.mw.taskman.run_in_background(self._check, lambda fut: on_finished(self, fut))


MediaChecker.check = on_check

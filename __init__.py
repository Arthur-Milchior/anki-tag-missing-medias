from concurrent.futures import Future

from aqt import mw
from aqt.mediacheck import MediaChecker
from aqt.utils import tooltip
from aqt.operations import CollectionOp
from anki.collection import Collection, OpChangesWithCount

TAGNAME = "MissingMedia"


def on_finished(self: MediaChecker, fut: Future) -> None:
    self._on_finished(fut)
    output = fut.result()
    missing = output.missing

    def task(col: Collection):
        col.tags.remove(TAGNAME)
        nids = []
        for filename in missing:
            for nid, mid, flds in col.db.execute("select id, mid, flds from notes"):
                media_refs = col.media.filesInStr(mid, flds)
                if filename in media_refs:
                    nids.append(nid)
        col.tags.bulkAdd(nids, TAGNAME)
        ret = OpChangesWithCount(count=len(nids))
        return ret

    def on_success(changes: OpChangesWithCount):
        tooltip(f"Tagged {changes.count} notes with {TAGNAME}")

    CollectionOp(parent=mw, op=task).success(on_success).run_in_background()


def check(self: MediaChecker) -> None:
    self.progress_dialog = self.mw.progress.start()
    self._set_progress_enabled(True)
    self.mw.taskman.run_in_background(self._check, lambda fut: on_finished(self, fut))


MediaChecker.check = check

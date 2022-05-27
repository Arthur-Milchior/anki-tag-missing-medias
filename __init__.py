from concurrent.futures import Future

from aqt import mw
from aqt.mediacheck import MediaChecker
from aqt.utils import tooltip, showWarning

ADDON_NAME = "Tag Notes with Missing Media"
TAGNAME = "MissingMedia"


def on_finished(self: MediaChecker, fut: Future) -> None:
    self._on_finished(fut)
    output = fut.result()
    missing = set(output.missing)

    def task() -> int:
        col = mw.col
        col.tags.remove(TAGNAME)
        total = mw.col.note_count()
        progress_step = max(100, min(1000, total // 100))
        count = 0
        tagged_nids = []
        want_cancel = False
        for nid, mid, flds in col.db.execute("select id, mid, flds from notes"):
            if want_cancel:
                break
            media_refs = set(col.media.filesInStr(mid, flds))
            if missing & media_refs:
                tagged_nids.append(nid)
            if count % progress_step == 0:

                def update_cancel() -> None:
                    nonlocal want_cancel
                    want_cancel = mw.progress.want_cancel()

                mw.taskman.run_on_main(update_cancel)
                mw.taskman.run_on_main(
                    lambda: mw.progress.update(
                        f"Processed {count+1} out of {total} notes.",
                        value=count + 1,
                        max=total,
                    )
                )
            count += 1
            if want_cancel:
                break

        col.tags.bulkAdd(tagged_nids, TAGNAME)
        return len(tagged_nids)

    def on_done(fut: Future):
        try:
            count = fut.result()
            tooltip(f"Tagged {count} notes with {TAGNAME}")
        except Exception as exc:
            showWarning(str(exc), title=ADDON_NAME)
        finally:
            mw.progress.finish()

    mw.progress.start(min=0)
    mw.progress.set_title(ADDON_NAME)
    mw.taskman.run_in_background(task, on_done=on_done)


def check(self: MediaChecker) -> None:
    self.progress_dialog = self.mw.progress.start()
    self._set_progress_enabled(True)
    self.mw.taskman.run_in_background(self._check, lambda fut: on_finished(self, fut))


MediaChecker.check = check

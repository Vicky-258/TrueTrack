import shutil
import os

def safe_move(src, dst):
    import tempfile
    import errno

    dst_dir = os.path.dirname(dst)

    try:
        os.replace(src, dst)
        return
    except OSError as e:
        if e.errno != errno.EXDEV:
            raise

    # Cross-device copy
    with tempfile.NamedTemporaryFile(delete=False, dir=dst_dir) as tmp:
        tmp_path = tmp.name

    shutil.copy2(src, tmp_path)
    os.replace(tmp_path, dst)
    os.unlink(src)
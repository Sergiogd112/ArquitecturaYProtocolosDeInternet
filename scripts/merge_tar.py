from multiprocessing import Pool,cpu_count
import os
from tqdm import tqdm
import subprocess
OUTPATH="lxc"
INPATH="lxc_split"
def merge_100_MB_tar(tar_file):
    #get all the 100 MB chunks of the tar file
    chunks = [f for f in os.listdir(os.path.join(INPATH, tar_file)) if f.endswith(".tar.gz")]
    print(f"Merging {len(chunks)} chunks of {tar_file}")
    #merge the chunks
    with open(os.path.join(OUTPATH, tar_file), "wb") as f:
        for chunk in chunks:
            with open(os.path.join(INPATH, tar_file, chunk), "rb") as c:
                f.write(c.read())
    #delete the chunks
    for chunk in chunks:
        os.remove(os.path.join(INPATH, tar_file, chunk))
    os.rmdir(os.path.join(INPATH, tar_file))
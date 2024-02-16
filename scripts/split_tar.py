from multiprocessing import Pool,cpu_count
import os
from tqdm import tqdm
import subprocess
INPATH="lxc"
OUTPATH="lxc_split"
def split_100_MB_tar(tar_file):
    #create a new directory for the tar file
    if not(os.path.exists(os.path.join(OUTPATH, tar_file.split(".")[0]))):
        os.mkdir(os.path.join(OUTPATH, tar_file.split(".")[0]))
    with open(os.path.join(INPATH, tar_file), "rb") as f:
        #split the tar file into 100 MB chunks
        content=f.read()
    print(f"Splitting {tar_file} of size{len(content)} into {len(content)//100000000} 100 MB chunks")
    for i in range(0, len(content), 100000000):
        with open(os.path.join(OUTPATH, tar_file.split(".")[0], f"{i//100000000}.tar.gz"), "wb") as f:
            f.write(content[i:i+100000000])
def main():
    #create the output directory
    if not(os.path.exists(OUTPATH)):
        os.mkdir(OUTPATH)
    #get all the tar files in the input directory
    tar_files = [f for f in os.listdir(INPATH) if f.endswith(".tar.gz")]
    print(f"Splitting {len(tar_files)} tar files")
    #create a pool of workers
    with Pool(cpu_count()) as p:
        #split the tar files
        res=list(tqdm(p.imap(split_100_MB_tar, tar_files), total=len(tar_files)))
    print("\n".join(res))
if __name__ == "__main__":
    main()
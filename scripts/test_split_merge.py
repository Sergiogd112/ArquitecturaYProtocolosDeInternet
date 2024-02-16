import os
from multiprocessing import Pool, cpu_count
from tqdm import tqdm


def compare_splited_files_to_original(file):
    INPATH = "lxc"
    OUTPATH = "lxc_split"

    if not file.endswith(".tar.gz"):
        return 0
    with open(os.path.join(INPATH, file), "rb") as f:
        original_content = f.read()
    splited_files = os.listdir(os.path.join(OUTPATH, file.split(".")[0]))
    splited_content = b""
    for sfile in splited_files:
        with open(os.path.join(OUTPATH, file.split(".")[0], sfile), "rb") as f:
            splited_content += f.read()
    return int(original_content == splited_content)


def test_split_100_MB_tar():
    INPATH = "lxc"
    OUTPATH = "lxc_split"

    with Pool(cpu_count()) as p:
        res = list(tqdm(p.imap(compare_splited_files_to_original, os.listdir(INPATH)), total=len(os.listdir(INPATH))))
    print(res)
    assert sum(res) == len(os.listdir(INPATH))


def main(args=None):
    test_split_100_MB_tar()
    print("All tests passed")


if __name__ == "__main__":
    main()

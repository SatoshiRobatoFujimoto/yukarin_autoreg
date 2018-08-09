import argparse
import glob
import multiprocessing
from functools import partial
from pathlib import Path
from typing import Optional

import librosa
import numpy as np
import tqdm

from yukarin_autoreg.utility.json_utility import save_arguments
from yukarin_autoreg.wave import Wave


def process(p: Path, sampling_rate: int):
    return Wave.load(p, sampling_rate).wave


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_glob', '-ig')
    parser.add_argument('--output_directory', '-od', type=Path)
    parser.add_argument('--sampling_rate', '-sr', type=int)
    parser.add_argument('--silence_top_db', '-st', type=float)
    config = parser.parse_args()

    input_glob = config.input_glob
    output_directory: Path = config.output_directory
    sampling_rate: int = config.sampling_rate
    silence_top_db: Optional[float] = config.silence_top_db

    output_directory.mkdir(exist_ok=True)
    save_arguments(config, output_directory / 'arguments.json')

    paths = [Path(p) for p in glob.glob(str(input_glob))]

    _process = partial(process, sampling_rate=sampling_rate)

    pool = multiprocessing.Pool()
    waves = list(tqdm.tqdm(pool.imap(_process, paths), total=len(paths)))
    lengths = [len(w) for w in waves]

    wave = np.concatenate(waves)
    intervals = librosa.effects.split(wave, top_db=silence_top_db)
    silence = np.ones(len(wave), dtype=bool)

    for s, t in intervals:
        silence[s:t] = False

    for i, (s, l) in enumerate(zip(np.cumsum([0] + lengths), lengths)):
        out = output_directory / (paths[i].stem + '.npy')
        np.save(str(out), dict(array=silence[s:s + l], rate=sampling_rate))


if __name__ == '__main__':
    main()
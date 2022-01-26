from concurrent.futures import ThreadPoolExecutor
from pandas.errors import ParserError
from typing import Dict, Iterable, List, Union, IO
import pandas as pd
from os import PathLike
import os
import re

visitag_misc_data_re_i = re.compile("^\s+(\w+)=\s+(-?\d+)")
visitag_misc_data_re_f = re.compile("^\s+(\w+)=\s+(-?\d+\.\d+)")
visitag_misc_data_re = re.compile("^\s+(\w+)=\s+(\w+)")

def parse_misc_visitag_data(file_h : Union[IO, PathLike]):
    with open(file_h, "r") as f:
        lines = f.readlines()
    data = {}
    for line in lines:
        for re_try, dtype in [(visitag_misc_data_re_i, int), (visitag_misc_data_re_f, float), (visitag_misc_data_re, str)]:
            match = re_try.match(line)
            if match is not None:
                data[match.group(1)] = dtype(match.group(2))
                break

    return data

def parse_visitag_file(file_h : Union[IO, PathLike], *args, **kwargs) -> Union[pd.DataFrame, Dict[str,str]]:
    try:
        return pd.read_csv(file_h, *args, **kwargs)
    except ParserError as err:
        return parse_misc_visitag_data(file_h)

def parse_visitag_files(file_hs : Iterable[Union[IO, PathLike]]) -> List[pd.DataFrame]:
    data = []
    with ThreadPoolExecutor() as pool:
        for file_h in file_hs:
            data.append(pool.submit(parse_visitag_file, file_h, sep="\s+"))

    return [d.result() for d in data]

def read_visitag_dir(dir_path : str) -> Dict[str, pd.DataFrame]:
    #visitag_data = {}
    visitag_fnames = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".txt"):
                visitag_fnames.append(os.path.join(root, file))

    data = parse_visitag_files(visitag_fnames)
    visitag_data = {os.path.splitext(os.path.basename(file))[0]: d for file, d in zip(visitag_fnames, data)}
    return visitag_data
from cartoreader_lite.low_level.utils import snake_to_camel_case, simplify_dataframe_dtypes, convert_df_dtypes
import pandas as pd
import numpy as np

def test_snake_to_camel_case():
    test_strings = ["camel_case", "imp_ort_ant_var"]
    expected_strings = ["camelCase", "impOrtAntVar"]
    assert all([snake_to_camel_case(t) == e for t, e in zip(test_strings, expected_strings)])
    assert all([snake_to_camel_case(t, capitalize=True) == (e[0].upper() + e[1:]) for t, e in zip(test_strings, expected_strings)])

def test_simplify_dataframe_dtypes():
    df = pd.DataFrame({"a": np.arange(3, dtype=np.int64), "b": np.array([0, 0.1, 2.], dtype=np.float64), "c": ["a", "b", "c"]})

    df_conv = simplify_dataframe_dtypes(df, {"a": np.float16}, inplace=False, double_to_float=True)
    assert df_conv.a.dtype == np.float16
    assert df_conv.b.dtype == np.float32
    assert df.a.dtype == np.int64
    assert df.b.dtype == np.float64

    #df_orig = df.copy()
    simplify_dataframe_dtypes(df, {"a": np.float16}, inplace=True, double_to_float=True)
    assert df.a.dtype == np.float16
    assert df.b.dtype == np.float32

def test_convert_df_dtypes():
    df = pd.DataFrame({"a": np.arange(3, dtype=np.int64), "b": np.array([0, 0.1, 2.], dtype=np.float64), "c": ["a", "b", "c"]})
    df.a = df.a.astype(str)
    df.b = df.b.astype(str)

    df_conv = convert_df_dtypes(df, inplace=False)
    assert np.issubdtype(df_conv.a.dtype, np.integer)
    assert np.issubdtype(df_conv.b.dtype, np.floating)
    assert np.issubdtype(df.a.dtype, np.object0)
    assert np.issubdtype(df.b.dtype, np.object0)

    convert_df_dtypes(df, inplace=True)
    assert np.issubdtype(df.a.dtype, np.integer)
    assert np.issubdtype(df.b.dtype, np.floating)
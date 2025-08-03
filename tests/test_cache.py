import pandas as pd

from qtools.data.cache import clear_cache, read_parquet, write_parquet


def test_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr("qtools.data.cache.CACHE_ROOT", tmp_path)

    df = pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
    write_parquet("test_ns", "test_key", df)

    loaded = read_parquet("test_ns", "test_key")
    assert loaded is not None
    pd.testing.assert_frame_equal(df, loaded)


def test_read_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("qtools.data.cache.CACHE_ROOT", tmp_path)
    assert read_parquet("no", "such_key") is None


def test_clear(tmp_path, monkeypatch):
    monkeypatch.setattr("qtools.data.cache.CACHE_ROOT", tmp_path)

    write_parquet("ns1", "a", pd.DataFrame({"x": [1]}))
    write_parquet("ns2", "b", pd.DataFrame({"x": [2]}))

    assert clear_cache("ns1") == 1
    assert read_parquet("ns1", "a") is None
    assert read_parquet("ns2", "b") is not None

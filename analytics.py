from __future__ import annotations
import pandas as pd
from typing import List, Dict

def conversations_df(rows: List[Dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # best-effort parse timestamps
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    return df

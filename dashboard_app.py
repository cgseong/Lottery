from __future__ import annotations

import csv
from typing import Dict, List

import streamlit as st

from analyzers.statistical_analyzer import StatisticalAnalyzer


@st.cache_data
def load_data(path: str = "로또당첨번호.csv") -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    st.set_page_config(page_title="Lotto Dashboard", layout="wide")
    st.title("Lotto Recommendation Dashboard")

    data = load_data()
    analyzer = StatisticalAnalyzer(data)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Frequency Top 10")
        freq = analyzer.analyze_frequency().get("most_common", [])
        st.table(freq[:10])

    with c2:
        st.subheader("Generate Recommendations")
        count = st.slider("Count", min_value=1, max_value=10, value=5)
        if st.button("Recommend"):
            recs = analyzer.generate_recommendations(num_recommendations=count)
            st.json(recs)


if __name__ == "__main__":
    main()

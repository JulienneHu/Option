"""
yf_session.py

Provides a yfinance Ticker backed by a curl_cffi session.
curl_cffi impersonates a real browser's TLS fingerprint, which bypasses
Yahoo Finance's bot detection on cloud servers (Streamlit Cloud, AWS, GCP, etc.).

Usage:
    from tools.yf_session import Ticker
    t = Ticker("AAPL")
    t.history(period="1d")
"""

import yfinance as yf

_session = None

def _get_session():
    global _session
    if _session is None:
        try:
            from curl_cffi import requests as curl_requests
            _session = curl_requests.Session(impersonate="chrome")
        except ImportError:
            _session = False  # curl_cffi not available, fall back to default
    return _session if _session is not False else None


def Ticker(symbol):
    session = _get_session()
    if session is not None:
        return yf.Ticker(symbol, session=session)
    return yf.Ticker(symbol)

"""Train-only sklearn pipelines. Structured signals are draft fixture rules."""

import re
import unicodedata
from html.parser import HTMLParser
from urllib.parse import urlsplit

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import StandardScaler

from phishing.features import extract
from phishing.features.domains import domain_relation

VARIANTS = ('M0', 'M1', 'M2', 'M3', 'M3-no-organization', 'M3-no-domain', 'M3-no-intention', 'B-rule')
BLOCKS = ('organization', 'domain', 'intention')


class _Intent(HTMLParser):
    def __init__(self, host):
        super().__init__()
        self.host = host
        self.password = self.external_form = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.password += int(tag == 'input' and attrs.get('type', '').lower() == 'password')
        action_host = urlsplit(attrs.get('action', '')).hostname
        self.external_form += int(tag == 'form' and bool(action_host) and action_host != self.host)


def structured(snapshot, dictionary):
    text = unicodedata.normalize('NFKC', extract(snapshot).text or '').casefold()
    candidates = [item for item in dictionary if any(
        re.search(r'(?<!\w)' + re.escape(alias.casefold()) + r'(?!\w)', text)
        for alias in item['aliases'])]
    relations = [domain_relation(snapshot.url, item['rules']) for item in candidates]
    parser = _Intent(urlsplit(snapshot.url).hostname)
    parser.feed(snapshot.html or '')
    return {
        'organization': [len(candidates), int(bool(candidates))],
        'domain': [int('verified_first_party' in relations),
                   int('verified_authorized' in relations),
                   int('unverified_shared_hosting' in relations),
                   int(bool(relations) and all(r.startswith('unverified') for r in relations))],
        'intention': [parser.password, parser.external_form,
                      int(bool(re.search(r'\b(login|sign in|verify|verification|otp)\b', text)))],
    }


class SnapshotNumeric(TransformerMixin, BaseEstimator):
    def __init__(self, variant='M0', dictionary=()):
        self.variant = variant
        self.dictionary = dictionary

    def fit(self, X, y=None):
        self.transform(X)  # Validate PreparedSnapshot input before fitting downstream.
        return self

    def transform(self, X):
        rows = []
        for snapshot in X:
            features = extract(snapshot)
            row = list(features.url.values())
            if self.variant != 'M0':
                if features.dom is None:
                    raise ValueError('HTML is required for the common M1–M3 cohort')
                row.extend(features.dom.values())
            if self.variant.startswith('M3'):
                signals = structured(snapshot, self.dictionary)
                for block in BLOCKS:
                    if self.variant != 'M3-no-' + block:
                        row.extend(signals[block])
            rows.append(row)
        return np.asarray(rows, dtype=float)


class SnapshotText(TransformerMixin, BaseEstimator):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        result = []
        for snapshot in X:
            text = extract(snapshot).text
            if text is None:
                raise ValueError('HTML required for TF-IDF')
            result.append(text)
        return result


def make_pipeline(variant, dictionary=(), *, C=1.0, seed=17):
    if variant not in VARIANTS or variant == 'B-rule':
        raise ValueError('Expected a trainable M0–M3/ablation variant')
    branches = [('numeric', Pipeline([
        ('extract', SnapshotNumeric(variant, dictionary)),
        ('scale', StandardScaler(with_mean=False)),
    ]))]
    if variant in ('M2', 'M3') or variant.startswith('M3-no-'):
        for name, analyzer, ngrams, budget in (
            ('word', 'word', (1, 2), 1000), ('char', 'char', (3, 5), 1500)):
            branches.append((name, Pipeline([
                ('text', SnapshotText()),
                ('tfidf', TfidfVectorizer(analyzer=analyzer, ngram_range=ngrams,
                                        max_features=budget, sublinear_tf=True)),
            ])))
    return Pipeline([
        ('features', FeatureUnion(branches)),
        ('classifier', LogisticRegression(C=C, solver='liblinear', max_iter=1000,
                                         class_weight='balanced', random_state=seed)),
    ])


def rule_scores(snapshots, dictionary):
    """Fixed toy weights, no official B-rule claim and no safe-domain bypass."""
    result = []
    for snapshot in snapshots:
        signal = structured(snapshot, dictionary)
        result.append(min(0.95, 0.1 + 0.2 * signal['organization'][1]
                          + 0.25 * signal['domain'][3]
                          + 0.2 * int(signal['intention'][0] > 0)
                          + 0.2 * int(signal['intention'][1] > 0)))
    return result

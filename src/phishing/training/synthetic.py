"""Invented balanced fixtures; not a source of research evidence."""

from dataclasses import dataclass
from phishing.features.domains import DomainRule
from phishing.preprocessing import PreparedSnapshot, prepare_snapshot


@dataclass(frozen=True)
class Sample:
    sample_id: str
    group_id: str
    label: int
    snapshot: PreparedSnapshot


def make_dataset(groups=40):
    if groups < 10:
        raise ValueError('At least 10 synthetic groups required')
    names = ('Northstar Fixture', 'Bluebay Fixture', 'Cedar Fixture')
    dictionary = tuple({'id': f'fixture-{i}', 'aliases': (name,), 'rules': (
        DomainRule(f'identity{i}.fixture.test', 'first_party_identity'),
        DomainRule('pages.fixture.test', 'user_content_hosting'),
    )} for i, name in enumerate(names))
    samples = []
    for group in range(groups):
        host = (f'identity{group}.fixture.test' if group < 3 else
                'pages.fixture.test' if group == 3 else f'page{group:02d}.fixture.test')
        name = names[group % 3]
        bodies = (
            f'<h1>{name}</h1><p>Verify your account</p><form action="https://collector.fixture.test/send"><input type="password"></form>',
            f'<h1>News</h1><p>Article about {name} community activities</p>',
            f'<h1>{name}</h1><p>Sign in</p><form action="/submit"><input type="password"></form>',
            '<h1>Member portal</h1><p>OTP verification required</p><form action="https://collector.fixture.test/send"><input name="otp"></form>',
        )
        for page, body in enumerate(bodies):
            html = f'<html><head><title>Portal</title></head><body>{body}<footer>Edition {group} page {page}</footer></body></html>'
            samples.append(Sample(f'g{group}-p{page}', f'synthetic-domain-{group}',
                                  int(page in (0, 3)), prepare_snapshot(f'https://{host}/section/{page}', html)))
    return samples, dictionary

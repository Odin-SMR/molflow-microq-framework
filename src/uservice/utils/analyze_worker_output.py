import math
import re
from collections import Counter
from operator import itemgetter

RE_PREFIX = re.compile(r'^.*? - (STDOUT|STDERR|EXECUTOR)\:\s*')
RE_SPACE = re.compile(r'\s+')
RE_URITRUNCATE = re.compile(r'^.*https?://[^?]+\?')


def rank_errors(jobs):
    """Rank lines in the output from the failed jobs.

    We want to give the interesting lines a high rank.

    Common errors are not as interesting as more seldom errors, because
    the common errors are easy to find by just looking at some examples of
    failed jobs.

    Lines with high amount of information should get a higher rank.
    But lines with a lot of numbers and other random data should get a lower
    rank.

    Args:
       jobs (list): List of job dicts that at least must contain the keys
         'id' and 'worker_output'.
    Returns:
       list: {score: float,
              line: str,
              common_lines: [{score: float, line: str}],
              jobids: [str]}
    """
    # TODO: Merge lines with similar structure. Could for example replace all
    #       digits with \d in this kind of output:
    # The server returned the message: "NOT FOUND" for URL,
    # 'http://malachite.rss.chalmers.se/rest_api/v4/ptz/2006-09-20/AC1
    # /21/2817364517/' (with HTTP response code 404)
    tri_probs = get_trigram_prob([job['worker_output'] for job in jobs])
    lines = {}
    for job in jobs:
        output = job.pop('worker_output')
        for line, clean_line in iter_unique_lines(output):
            if line in lines:
                lines[line]['jobids'].append(job['id'])
            else:
                lines[line] = {
                    'entropy': trigram_entropy(line, tri_probs),
                    'clean_line': clean_line,
                    'jobids': [job['id']]}
    ranked = {}

    N = float(len(lines))
    for line, data in lines.items():
        # log entropy to ensure that crazy lines with extremely high entropy
        # do not get ranked too high.
        score = math.log(data['entropy'] or 1) * len(data['jobids']) / N
        job_ids_key = ' '.join(sorted(data['jobids']))
        if job_ids_key in ranked:
            item = ranked[job_ids_key]
            item['common_lines'].append(
                {'line': data['clean_line'], 'score': score})
            if score > item['score']:
                item['score'] = score
                item['line'] = data['clean_line']
        else:
            ranked[job_ids_key] = {
                'score': score,
                'line': data['clean_line'],
                'common_lines': [{'line': data['clean_line'], 'score': score}],
                'jobids': data['jobids']}

    ranked = sorted(ranked.values(), key=itemgetter('score'), reverse=True)
    for item in ranked:
        item['common_lines'].sort(key=itemgetter('score'), reverse=True)
    return ranked


def trigram_entropy(string, tri_probs):
    "Calculates the Shannon entropy of a string"

    # Get probability of trigrams in string
    prob = [tri_probs[tri] for tri in get_trigrams(string)]

    # Calculate the entropy
    entropy = - sum(p * math.log(p) / math.log(2.0) for p in prob)

    return entropy


def get_trigrams(string):
    """Generate trigrams in a string"""
    for i in range(len(string) - 3 + 1):
        yield string[i:i+3]


def remove_prefix(line):
    """Remove datetime etc in output line"""
    return RE_PREFIX.sub(u'', line)


def get_clean_line(line):
    line = remove_prefix(line)
    line = line.strip()
    return RE_SPACE.sub(u' ', line)


def get_compare_line(line):

    match = RE_URITRUNCATE.match(line)
    if match:
        return match.group(0)
    return line


def iter_unique_lines(output):
    """Generate cleaned lines from the job output text"""
    if output:
        seen = set()
        for line in output.split('\n'):
            clean_line = get_clean_line(line)
            if not clean_line:
                continue
            compare_line = get_compare_line(clean_line)
            if compare_line in seen:
                continue
            seen.add(compare_line)
            yield compare_line, clean_line


def get_output_trigrams(txt):
    """Generate unique trigrams in a job output text"""
    seen = set()
    for line, _ in iter_unique_lines(txt):
        for tri in get_trigrams(line):
            if tri in seen:
                continue
            yield tri
            seen.add(tri)


def count_trigrams(txts):
    """Return number of occurences of trigrams in the job output texts and
    the total number of texts
    """
    tricount = Counter()
    N = None
    for N, txt in enumerate(txts):
        tricount.update(get_output_trigrams(txt))
    if N is None:
        return tricount, 0
    else:
        return tricount, N + 1


def get_trigram_prob(txts):
    """Return dict with {trigram: probability}"""
    count, N = count_trigrams(txts)
    if not N:
        return {}
    N = float(N)
    return {tri: n / N for tri, n in count.items()}

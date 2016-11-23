import math
import re
from collections import Counter
from operator import itemgetter

RE_PREFIX = re.compile(u'^.*? - (STDOUT|STDERR|EXECUTOR)\:\s*', re.U)
RE_SPACE = re.compile(u'\s+', re.U)


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
        for line in iter_unique_lines(output):
            if line in lines:
                lines[line]['jobids'].append(job['id'])
            else:
                lines[line] = {
                    'entropy': trigram_entropy(line, tri_probs),
                    'jobids': [job['id']]}
    ranked = {}
    N = float(len(lines))
    for line, data in lines.iteritems():
        # log entropy to ensure that crazy lines with extremely high entropy
        # do not get ranked too high.
        score = math.log(data['entropy'] or 1) * len(data['jobids'])/N
        job_ids_key = ' '.join(sorted(data['jobids']))
        if job_ids_key in ranked:
            item = ranked[job_ids_key]
            item['common_lines'].append({'line': line, 'score': score})
            if score > item['score']:
                item['score'] = score
                item['line'] = line
        else:
            ranked[job_ids_key] = {
                'score': score,
                'line': line,
                'common_lines': [{'line': line, 'score': score}],
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
    entropy = - sum([p * math.log(p) / math.log(2.0) for p in prob])

    return entropy


def get_trigrams(string):
    """Generate trigrams in a string"""
    for i in range(len(string) - 3 + 1):
        yield string[i:i+3]


def remove_prefix(line):
    """Remove datetime etc in output line"""
    return RE_PREFIX.sub(u'', line)


def clean_line(line):
    line = remove_prefix(line)
    line = line.strip()
    return RE_SPACE.sub(u' ', line)


def iter_unique_lines(output):
    """Generate cleaned lines from the job output text"""
    seen = set()
    for line in output.split('\n'):
        line = clean_line(line)
        if not line:
            continue
        if line in seen:
            continue
        seen.add(line)
        yield line


def get_output_trigrams(txt):
    """Generate unique trigrams in a job output text"""
    seen = set()
    for line in iter_unique_lines(txt):
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
    for N, txt in enumerate(txts):
        tricount.update(get_output_trigrams(txt))
    return tricount, N + 1


def get_trigram_prob(txts):
    """Return dict with {trigram: probability}"""
    count, N = count_trigrams(txts)
    N = float(N)
    return {tri: n/N for tri, n in count.iteritems()}

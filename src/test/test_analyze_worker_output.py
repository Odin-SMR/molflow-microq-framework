from collections import Counter
import pytest

from uservice.utils import analyze_worker_output as analout


class TestAnalyzeWorkerOutput:

    def test_get_trigrams(self):
        """Test extraction of trigrams from a string"""
        trigrams = list(analout.get_trigrams(u'Stopping ARTS execution.'))

        expected = ['Sto', 'top', 'opp', 'ppi', 'pin', 'ing', 'ng ', 'g A',
                    ' AR', 'ART', 'RTS', 'TS ', 'S e', ' ex', 'exe', 'xec',
                    'ecu', 'cut', 'uti', 'tio', 'ion', 'on.']
        assert trigrams == expected

    def test_remove_prefix(self):
        """Test removal of datetime etc from log line"""
        orig = u'2016-11-22T09:29:58.176677 - STDOUT: Stopping ARTS execution.'
        expected = u'Stopping ARTS execution.'
        assert analout.remove_prefix(orig) == expected

    def test_clean_line(self):
        """Test clean of stdout log line"""
        orig = (u'2016-11-22T20:58:10.745097 - STDOUT: '
                u'| -99 \t10.0 \t3.579 \t0.00 \t3.58 \tNaN  |  ')
        expected = u'| -99 10.0 3.579 0.00 3.58 NaN |'
        assert analout.get_clean_line(orig) == expected

    def test_iter_unique_lines(self):
        """Test generation of clean lines from stdout log"""
        orig = (
            u'2016-11-22T20:57:28.232355 - STDOUT: Using Q config with '
            u'freqmode 21 and invmode meso\n'
            u'2016-11-22T20:57:32.355568 - STDOUT: Using Q config with '
            u'freqmode 21 and invmode meso\n'
            u'2016-11-22T20:57:34.016252 - STDOUT:\n'
            u'2016-11-22T20:57:34.159448 - STDOUT: /------------------------'
            u'------------------------------------------------------\\\n'
            u'2016-11-22T20:57:34.160096 - STDOUT: | Gamma Total Profile '
            u'Spectrum Converg. |\n'
            u'2016-11-22T20:57:34.160542 - STDOUT: | Iteration factor cost '
            u'cost cost measure |\n'
            u'2016-11-22T20:58:01.610377 - STDOUT: | 1 NaN 1.315 0.00 1.32 NaN'
            u' |\n'
            u'2016-11-22T20:58:10.745097 - STDOUT: | -99 10.0 3.579 0.00 3.58 '
            u'NaN |'
        )

        expected = [
            u'Using Q config with freqmode 21 and invmode meso',
            (u'/----------------------------------------------------------'
             u'--------------------\\'),
            u'| Gamma Total Profile Spectrum Converg. |',
            u'| Iteration factor cost cost cost measure |',
            u'| 1 NaN 1.315 0.00 1.32 NaN |',
            u'| -99 10.0 3.579 0.00 3.58 NaN |'
        ]

        assert list(
            compare_line for compare_line, _ in
            analout.iter_unique_lines(orig)) == expected

    def test_get_output_trigrams(self):
        """Test extraction of trigrams from stdout log"""
        txt = (
            u'2016-11-22T20:57:34.016252 - STDOUT:\n'
            u'2016-11-22T20:57:34.159448 - STDOUT: /------------------------'
            u'------------------------------------------------------\\\n'
            u'2016-11-22T20:57:34.160096 - STDOUT: | Gamma |\n'
        )
        expected = ['/--', '---', '--\\', '| G', ' Ga', 'Gam', 'amm', 'mma',
                    'ma ', 'a |']
        assert list(analout.get_output_trigrams(txt)) == expected

    def test_count_trigrams_and_get_trigram_prob(self):
        """Test counting of trigrams in texts and calculation of trigram
        probabilities
        """
        txts = [
            (
                u'2016-11-22T20:57:34.016252 - STDOUT:\n'
                u'2016-11-22T20:57:34.159448 - STDOUT: /----------------------'
                u'--------------------------------------------------------\\\n'
                u'2016-11-22T20:57:34.160096 - STDOUT: | Gamma |\n'),
            (
                u'2016-11-22T20:57:34.016252 - STDOUT:\n'
                u'2016-11-22T20:57:34.159448 - STDOUT: /----------------------'
                u'--------------------------------------------------------\\\n'
                u'2016-11-22T20:57:34.160096 - STDOUT: | Alpha |\n'),
        ]

        expected = Counter()
        expected.update([
            '/--', '---', '--\\', '| G', ' Ga', 'Gam', 'amm', 'mma', 'ma ',
            'a |'])
        expected.update([
            '/--', '---', '--\\', '| A', ' Al', 'Alp', 'lph', 'pha', 'ha ',
            'a |'])

        count, N = analout.count_trigrams(txts)
        assert count == expected
        assert N == 2

        prob = analout.get_trigram_prob(txts)
        expected = {
            '/--': 1, '---': 1, '--\\': 1, '| G': .5, ' Ga': .5, 'Gam': .5,
            'amm': .5, 'mma': .5, 'ma ': .5, 'a |': 1, '| A': .5, ' Al': .5,
            'Alp': .5, 'lph': .5, 'pha': .5, 'ha ': .5}
        assert prob == expected

    def test_trigram_entropy(self):
        """Test calculation of entropy for a string"""
        txts = [
            'line1\nline2',
            'line1\nline3',
        ]
        prob = analout.get_trigram_prob(txts)
        assert analout.trigram_entropy('line1', prob) == 0
        assert analout.trigram_entropy('line2', prob) > 0

    def test_rank_errors(self):
        """Test ranking of error output lines"""
        jobs = [
            {'worker_output': 'line1\nline2\nlineX',
             'id': '1'},
            {'worker_output': 'line1\nline3\nlineX',
             'id': '2'},
        ]
        ranking = analout.rank_errors(jobs)
        assert len(ranking) == 3

        assert ranking[0]['line'] in ('line1', 'lineX')
        assert ranking[0]['score'] == 0
        assert len(ranking[0]['jobids']) == 2

        assert ranking[1]['line'] in ('line2', 'line3')
        assert ranking[1]['score'] < 0
        assert len(ranking[1]['jobids']) == 1

    @pytest.mark.parametrize('orig,expected', [

        (
            u'This is a test',
            'This is a test',
        ),
        (
            u'This is a http://test.com/help?no thank you',
            u'This is a http://test.com/help?',
        ),
        (
            u'This is a http://test.com/help no thank you',
            u'This is a http://test.com/help no thank you',
        ),
    ])
    def test_truncationbehaviour(self, orig, expected):

        assert analout.get_compare_line(orig) == expected

import unittest


from newrelic_logging import NewRelicApiException, newrelic


class TestNewRelic(unittest.TestCase):
    def test_get_region_raises_new_relic_api_exception_given_invalid_region(self):
        '''
        get_region() raises a NewRelicApiException given an invalid region
        given: a string
        when: get_region() is called
        and when: the string is not a valid region identifier
        then: raise a NewRelicApiException
        '''

        # execute / verify
        with self.assertRaises(NewRelicApiException) as _:
            newrelic.get_region('invalid')

    def test_get_region_returns_us_region_given_us_string(self):
        '''
        get_region() returns Region.US given the string 'us'
        given: a string
        when: get_region() is called
        and when: the string is 'us'
        then: return Region.US
        '''

        # execute
        region = newrelic.get_region('us')

        # verify
        self.assertEqual(region, newrelic.Region.US)

    def test_get_region_returns_eu_region_given_eu_string(self):
        '''
        get_region() returns Region.EU given the string 'eu'
        given: a string
        when: get_region() is called
        and when: the string is 'eu'
        then: return Region.EU
        '''

        # execute
        region = newrelic.get_region('eu')

        # verify
        self.assertEqual(region, newrelic.Region.EU)

    def test_get_region_returns_fedramp_region_given_fedramp_string(self):
        '''
        get_region() returns Region.FEDRAMP given the string 'fedramp'
        given: a string
        when: get_region() is called
        and when: the string is 'fedramp'
        then: return Region.FEDRAMP
        '''

        # execute
        region = newrelic.get_region('fedramp')

        # verify
        self.assertEqual(region, newrelic.Region.FEDRAMP)

    def test_get_logs_endpoint_raises_new_relic_api_exception_if_get_region_does(self):
        '''
        get_logs_endpoint() raises a NewRelicApiException if get_region() does
        given: a string
        when: get_logs_endpoint() is called
        and when: get_region() is called
        and when: get_region() raises a NewRelicApiException
        then: raise a NewRelicApiException
        '''

        # execute / verify
        with self.assertRaises(NewRelicApiException) as _:
            newrelic.get_logs_endpoint('invalid')

    def test_get_logs_endpoint_returns_us_endpoint_given_us_string(self):
        '''
        get_logs_endpoint() returns US_LOGS_ENDPOINT given the string 'us'
        given: a string
        when: get_logs_endpoint() is called
        and when: the string is 'us'
        then: return US_LOGS_ENDPOINT
        '''

        # execute
        endpoint = newrelic.get_logs_endpoint('us')

        # verify
        self.assertEqual(endpoint, newrelic.US_LOGS_ENDPOINT)

    def test_get_logs_endpoint_returns_eu_endpoint_given_eu_string(self):
        '''
        get_logs_endpoint() returns EU_LOGS_ENDPOINT given the string 'eu'
        given: a string
        when: get_logs_endpoint() is called
        and when: the string is 'eu'
        then: return EU_LOGS_ENDPOINT
        '''

        # execute
        endpoint = newrelic.get_logs_endpoint('eu')

        # verify
        self.assertEqual(endpoint, newrelic.EU_LOGS_ENDPOINT)

    def test_get_logs_endpoint_returns_fedramp_endpoint_given_fedramp_string(self):
        '''
        get_logs_endpoint() returns FEDRAMP_LOGS_ENDPOINT given the string 'fedramp'
        given: a string
        when: get_logs_endpoint() is called
        and when: the string is 'fedramp'
        then: return FEDRAMP_LOGS_ENDPOINT
        '''

        # execute
        endpoint = newrelic.get_logs_endpoint('fedramp')

        # verify
        self.assertEqual(endpoint, newrelic.FEDRAMP_LOGS_ENDPOINT)

    def test_get_events_endpoint_raises_new_relic_api_exception_if_get_region_does(self):
        '''
        get_events_endpoint() raises a NewRelicApiException if get_region() does
        given: a string
        and given: an account ID
        when: get_events_endpoint() is called
        and when: get_region() is called
        and when: get_region() raises a NewRelicApiException
        then: raise a NewRelicApiException
        '''

        # execute / verify
        with self.assertRaises(NewRelicApiException) as _:
            newrelic.get_events_endpoint('invalid', 12345)

    def test_get_events_endpoint_returns_us_endpoint_given_us_string_and_account_id(self):
        '''
        get_events_endpoint() returns US_EVENTS_ENDPOINT for the given account ID given the string 'us'
        given: a string
        and given: an account ID
        when: get_events_endpoint() is called
        and when: the string is 'us'
        then: return US_EVENTS_ENDPOINT for the given account ID
        '''

        # execute
        endpoint = newrelic.get_events_endpoint('us', 12345)

        # verify
        self.assertEqual(
            endpoint,
            newrelic.US_EVENTS_ENDPOINT.format(account_id=12345),
        )

    def test_get_events_endpoint_returns_eu_endpoint_given_eu_string_and_account_id(self):
        '''
        get_events_endpoint() returns EU_EVENTS_ENDPOINT for the given account ID given the string 'eu'
        given: a string
        and given: an account ID
        when: get_events_endpoint() is called
        and when: the string is 'eu'
        then: return EU_EVENTS_ENDPOINT for the given account ID
        '''

        # execute
        endpoint = newrelic.get_events_endpoint('eu', 12345)

        # verify
        self.assertEqual(
            endpoint,
            newrelic.EU_EVENTS_ENDPOINT.format(account_id=12345),
        )

    def test_get_events_endpoint_returns_fedramp_endpoint_given_fedramp_string_and_account_id(self):
        '''
        get_events_endpoint() returns FEDRAMP_EVENTS_ENDPOINT for the given account ID given the string 'fedramp'
        given: a string
        and given: an account ID
        when: get_events_endpoint() is called
        and when: the string is 'fedramp'
        then: return FEDRAMP_EVENTS_ENDPOINT for the given account ID
        '''

        # execute
        endpoint = newrelic.get_events_endpoint('fedramp', 12345)

        # verify
        self.assertEqual(
            endpoint,
            newrelic.FEDRAMP_EVENTS_ENDPOINT.format(account_id=12345),
        )

# Jordan Cazamias
# Sub Zones Performance Testing

import argparse
import sys
import timeit as t

import zones as z

def run_create_tests(zonesnums, **kwargs):
    """
    Runs test_create_zones with a list of zone numbers

    :param zonesnums: List of zone numbers to run tests for
    :return: Dict mapping number of zones tested to elapsed test time
    """
    print "*** RUNNING CREATE TEST WITH AMOUNTS {0}... ***".format(zonesnums)
    z.delete_zones(**kwargs)
    results = {}
    for num in zonesnums:
        print "*** TESTING WITH {0} ZONES ***".format(num)
        testtime = test_create_zones(num, **kwargs)
        results[num] = testtime
        print "Test completed in {0} s".format(testtime)
        z.delete_zones(**kwargs)
    print "***CREATE TEST RESULTS:***"
    for numzones, time in results.iteritems():
        print " - {0} zones: {1}s".format(numzones, time)

    return results

def test_create_zones(numzones, **kwargs):
    """
    Calculates the amount of time to create a number of zones

    :param numzones: Number of zones to create
    :return: Test runtime, in seconds
    """

    setup = "import zones as z"
    func = "z.create_zones({0}, {1})".format(
        numzones, _kwargs_as_str(kwargs))
    timer = t.Timer(func, setup)
    return timer.timeit(number=1)

def run_create_another_tests(zonesnums, **kwargs):
    """
    Runs test_create_another_zone with a list of zone numbers

    :param zonesnums: List of zone numbers to run tests for
    :return: Dict mapping number of zones tested to elapsed test time
    """
    print "*** RUNNING CREATE_ANOTHER TEST WITH AMOUNTS {0}... ***".\
        format(zonesnums)
    results = {}
    for num in zonesnums:
        print "*** TESTING WITH {0} ZONES ***".format(num)
        times = test_create_another_zone(basezones=num, numtests=5, **kwargs)
        results[num] = times
        for time in times:
            print time
    print "***CREATE TEST RESULTS:***"
    for numzones, times in results.iteritems():
        print " - {0} zones: {1}s".format(numzones, time_stats(times))

    return results


def test_create_another_zone(basezones=None, numtests=100, **kwargs):
    """
    Creates <basezones> zones as a base, then times the creation
    of an additional zone

    :param basezones: Number of zones to be created as a base
    :param numtests: Number of times to run test
    :return: List of elapsed time for each test
    """
    curr_num_zones = z.get_num_zones(**kwargs)
    if basezones is None:
        basezones = curr_num_zones

    zones_diff = curr_num_zones - basezones

    # Change number of zones to match <basezones>
    if zones_diff < 0:
        print "Creating {0} zones to reach base of {1} zones".format(
            abs(zones_diff), basezones)
        z.create_zones(abs(zones_diff), **kwargs)
    elif zones_diff > 0:
        print "Deleting {0} zones to reach base of {1} zones".format(
            abs(zones_diff), basezones)
        z.delete_zones(abs(zones_diff), **kwargs)

    times = []
    zone_name = "testtesttest.com."
    setup = "import zones as z".format(zone_name)
    func = "z.create_zone('{0}', {1})".format(
        zone_name, _kwargs_as_str(kwargs))
    timer = t.Timer(stmt=func, setup=setup)

    # Run test <numtests> times
    print "Running test {0} times...".format(numtests)
    for i in range(numtests):
        sys.stdout.write("\rCompleted test {0} of {1}".format(i, numtests))
        sys.stdout.flush()
        time = timer.timeit(number=1)
        times.append(time)

        # Delete created zone
        id = z.get_zone_id(zone_name, **kwargs)
        if id:
            z.delete_zone(id, **kwargs)
    print ""

    return times

def time_stats(times):
    """
    Given list of test times, prints useful information
    """
    timestr = ""

    # Print statistics
    mintime = min(times)
    avgtime = (sum(times) / len(times))
    maxtime = max(times)

    timestr += "(min={0}s, ".format(min(times))
    timestr += "avg={0}s, ".format(sum(times) / len(times))
    timestr += "max={0}s)".format(max(times))

    return timestr

def _kwargs_as_str(kwargs):
    """
    Inject kwargs key-value pairs in string form, to create func strings
    """
    kwstr = ', '.join("{0}={1}".format(key, repr(value)) for
                      key,value in kwargs.iteritems())

    return kwstr

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Test the creation of zones")

    parser.add_argument("--host")
    #parser.add_argument("--numzones", default=10, type=int)
    parser.add_argument("--numprocs", default=1, type=int)
    parser.add_argument("--tenant")
    parser.add_argument("--zonesnums",
                        default=[10, 100, 1000, 10000, 100000],
                        nargs='+')

    args = parser.parse_args()

    print vars(args)

    run_create_tests(test_create_zones, **vars(args))



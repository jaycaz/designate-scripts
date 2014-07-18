# Jordan Cazamias
# Sub Zones Performance Testing

import argparse
import sys
import timeit as t

import zones as z

def test_create_zones(numzones, numprocs=None, tenant=None, host=None):
    setup = "import zones as z"
    func = "z.create_zones({0}{1}{2}{3})".format(
        numzones,
        (", numprocs={0}".format(numprocs) if numprocs else ""),
        (", tenant={0}".format(tenant) if tenant else ""),
        (", host='{0}'".format(host) if host else ""))
    timer = t.Timer(func, setup)
    return timer.timeit(number=1)

def run_create_tests(zonesnums, **kwargs):
    print "*** RUNNING CREATE TEST WITH AMOUNTS {0}... ***".format(zonesnums)
    z.delete_zones(**kwargs)
    results = {}
    for num in zonesnums:
        print "*** TESTING WITH {0} ZONES ***".format(num)
        testtime = test_create_zones(num, **kwargs)
        results[num] = testtime
        z.delete_zones(**kwargs)
        print "Test completed in {0} s".format(testtime)
    print "***CREATE TEST RESULTS:***"
    for numzones, time in results.iteritems():
        print " - {0} zones: {1}s".format(numzones, time)

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

    run_create_tests(**vars(args))



# Jordan Cazamias
# Sub Zones Performance Testing

import timeit as t
import zones as z

def test_create_zones(numzones, tenant=None, host=None):
    setup = "import zones as z"
    func = "z.create_zones({0}{1}{2})".format(
        numzones,
        (", tenant={0}".format(tenant) if tenant else ""),
        (", host={0}".format(host) if host else ""))
    timer = t.Timer(func, setup)
    return timer.timeit(number=1)

def run_create_tests(zonesnums):
    print "*** RUNNING CREATE TEST WITH AMOUNTS {0}... ***".format(zonesnums)
    results = {}
    for num in zonesnums:
        print "*** TESTING WITH {0} ZONES ***".format(num)
        testtime = test_create_zones(num)
        results[num] = testtime
        z.delete_zones()

    print "***CREATE TEST RESULTS:***"
    for numzones, time in results.iteritems():
        print " - {0} zones: {1}s".format(numzones, time)

if __name__ == '__main__':
    z.create_zones(20)
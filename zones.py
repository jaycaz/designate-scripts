# Jordan Cazamias
# Rackspace Cloud DNS

# zones.py: Zone utility functions

import json
from multiprocessing import Process
from multiprocessing import Queue
from Queue import Empty as QueueEmpty
import os
import random
import sys
import time


import requests

tlds = ['com.', 'org.', 'net.', 'edu.']
words = ['adult', 'aeroplane', 'air', 'airforce', 'airport', 'album', 'alphabet',
         'apple', 'arm', 'army', 'baby', 'baby', 'backpack', 'balloon', 'banana',
         'bank', 'barbecue', 'bathroom', 'bathtub', 'bed', 'bee', 'bible', 'bible',
         'bird', 'bomb', 'book', 'boss', 'bottle', 'bowl', 'box', 'boy', 'brain',
         'bridge', 'butterfly', 'button', 'cappuccino', 'car', 'carpet', 'carrot',
         'cave', 'chair', 'chessboard', 'chief', 'child', 'chisel', 'chocolates',
         'church', 'circle', 'circus', 'clock', 'clown', 'coffee', 'comet', 'compass',
         'computer', 'crystal', 'cup', 'cycle', 'database', 'desk', 'diamond', 'dress',
         'drill', 'drink', 'drum', 'dung', 'ears', 'earth', 'egg', 'electricity',
         'elephant', 'eraser', 'explosive', 'eyes', 'family', 'fan', 'feather', 'festival',
         'film', 'finger', 'fire', 'floodlight', 'flower', 'foot', 'fork', 'freeway',
         'fruit', 'fungus', 'game', 'garden', 'gas', 'gate', 'gemstone', 'girl', 'gloves',
         'god', 'grapes', 'guitar', 'hammer', 'hat', 'hieroglyph', 'highway', 'horoscope',
         'horse', 'hose', 'ice', 'insect', 'junk', 'kaleidoscope', 'kitchen', 'knife',
         'leg', 'library', 'liquid', 'magnet', 'man', 'map', 'maze', 'meat', 'meteor',
         'microscope', 'milk', 'milkshake', 'mist', 'money', 'monster', 'mosquito', 'mouth',
         'nail', 'navy', 'necklace', 'needle', 'onion', 'paintbrush', 'pants', 'parachute',
         'passport', 'pebble', 'pendulum', 'pepper', 'perfume', 'pillow', 'plane', 'planet',
         'pocket', 'potato', 'printer', 'prison', 'pyramid', 'radar', 'rainbow', 'record',
         'restaurant', 'rifle', 'ring', 'robot', 'rock', 'rocket', 'roof', 'room', 'rope',
         'saddle', 'salt', 'sandpaper', 'sandwich', 'satellite', 'school', 'sex', 'ship',
         'shoes', 'shop', 'shower', 'signature', 'skeleton', 'slave', 'snail', 'software',
         'solid', 'spectrum', 'sphere', 'spice', 'spiral', 'spoon', 'square', 'staircase',
         'star', 'stomach', 'sun', 'sunglasses', 'surveyor', 'swimming', 'sword', 'table',
         'tapestry', 'teeth', 'telescope', 'television', 'thermometer', 'tiger', 'toilet',
         'tongue', 'torch', 'torpedo', 'train', 'treadmill', 'triangle', 'tunnel',
         'typewriter', 'umbrella', 'vacuum', 'vampire', 'videotape', 'vulture', 'water',
         'weapon', 'web', 'wheelchair', 'window', 'woman', 'worm']

TENANTS = [str(n) for n in range(50)]
TENANT = TENANTS[0]
HOST = "http://192.168.33.8:9001"


def create_server(servername="ns.servers.com.", host=HOST):
    """
    Creates nameserver on host.
    :param servername: Name of nameserver to be created
    """
    server_url, headers = _get_request_data("/v1/servers",
                                            tenant="",
                                            host=host)
    data = {
        "name": servername
    }

    r = requests.post(server_url, data=json.dumps(data), headers=headers)
    if r.status_code == 200:
        print "Server {0} successfully created".format(servername)
    else:
        print "Server creation failed."
        _print_error(r.status_code, r.text)
        return


def change_zones_quota(newquota, tenant=TENANT, host=HOST):
    """
    Changes quota for specified tenant on host
    :param newquota: New maximum number of zones the tenant should have
    """
    quota_url, headers = _get_request_data("/v2/quotas/{0}".format(tenant),
                                           tenant=tenant,
                                           host=host)
    data = {
        "quota": {
        "zones": newquota
        }
    }

    r = requests.patch(quota_url, data=json.dumps(data), headers=headers)
    if r.status_code == 200:
        print "Max zones quota for tenant '{0}' updated to {1}".format(
            tenant, newquota)
    else:
        print "Quota update failed."

        return


def get_num_zones(tenant=TENANT, host=HOST):
    """
    Retrieves the number of zones for a given tenant
    """
    zone_url, headers = _get_request_data("/v1/reports/counts",
                                          tenant=tenant,
                                          host=host)
    r = requests.get(zone_url, headers=headers)

    if r.status_code != 200:
        _print_error(r.status_code, r.text)
        return

    j = r.json()
    numzones = j['domains']

    return numzones


def delete_zones_multitenant(tenants=TENANTS, host=HOST):
    """
    Deletes all zones for the given list of tenants
    """
    for tenant in tenants:
        if get_num_zones(tenant, host=host) != 0:
            delete_zones(tenant=tenant, host=host)


def delete_zones(numdelete=None, tenant=TENANT, host=HOST):
    """
    Deletes a number of zones, or all zones, for a specified tenant.
    :param numdelete: number of zones to delete. If omitted, deletes all zones.
    """
    zone_url, headers = _get_request_data("/v2/zones",
                                          tenant=tenant,
                                          host=host)
    r = requests.get(zone_url, headers=headers)
    j = r.json()
    zones = j['zones']

    # Sort zones so deepest level subdomains are deleted first
    print "Sorting zones to delete...",
    depth = lambda x: x['name'].count(".")
    sorted_zones = sorted(zones, key=depth, reverse=True)
    print "done."

    # Determine number to be deleted
    if numdelete is None:
        numdelete = len(zones)
    else:
        numdelete = min(numdelete, len(zones))

    print "Deleting {0} zones...".format(numdelete),
    successes = 0

    for i in range(numdelete):
        z = sorted_zones[i]
        r = delete_zone(z['id'], tenant=tenant, host=host)

        if r.status_code == 204:
            sys.stdout.write("\rDeleted zone {0} of {1}".format(
                i+1, numdelete
            ))
            sys.stdout.flush()
            successes += 1
        else:
            _print_error(r.status_code, r.text)

    print ""

    print "* Successes: {0} out of {1}".format(successes, numdelete)
    print "* Tenant {0} now has {1} zones\n".format(
        tenant, get_num_zones(tenant, host))


def delete_zone(zoneid, tenant=TENANT, host=HOST):
    """
    Deletes a specific zone under the given tenant
    :param zoneid: ID of the zone to be deleted
    """
    zone_url, headers = _get_request_data("/v2/zones/{0}".format(zoneid),
                                          tenant=tenant,
                                          host=host)
    r = requests.delete(zone_url, headers=headers)
    return r


def create_zones_multitenant(numzones, numprocs=1, tenants=TENANTS, host=HOST):
    """
    # Creates zones, randomly distributed among a list of tenant IDs
    :param numzones: Number of zones to create
    :param tenants: List of tenants to distribute zones to
    """

    print "Distributing {0} zones among {1} tenants...".format(
        numzones, len(tenants)
    )

    # Randomly distribute zones among tenants
    tenantcounts = {}
    for i in range(numzones):
        randtenant = random.choice(tenants)
        if randtenant in tenantcounts:
            tenantcounts[randtenant] += 1
        else:
            tenantcounts[randtenant] = 1

    # Create queue of tenants and spawn processes to process queue
    tenantqueue = Queue()
    for tenantcount in sorted(tenantcounts.iteritems()):
        tenantqueue.put(tenantcount)

    newzones = []
    procs = []
    results = Queue()

    if numprocs != 1:
        print "Starting {0} processes...".format(numprocs)

    for i in range(numprocs):
        # TODO: Pass in existing zones to oldzonequeue
        p = Process(target=_create_zones_proc,
                    args=(None,),
                    kwargs={
                        'newzonequeue': results,
                        'tenantqueue': tenantqueue,
                        'host': host
                    })
        procs.append(p)
        p.start()
        if numprocs != 1:
            print "Process {0} spawned".format(p.pid)

    # Check on queue status
    # TODO: Find out a way to output number of tenants completed
    successes = 0
    while len(procs) > 0:
        for p in procs:
            if p.is_alive():
                time.sleep(0.05)
                break
            else:
                if numprocs != 1:
                    print "\nProcess {0} completed".format(p.pid),
                procs.remove(p)
        while not results.empty():
            newzones.append(results.get(block=True))
            successes += 1
            sys.stdout.write("\rCreated zone {0} of {1}".format(
                successes, numzones))
            sys.stdout.flush()
    print ""

    # Compile and print results
    while not results.empty():
        newzones.append(results.get())

    depthcounts = {}
    for newzone in newzones:
        depth = _zone_depth(newzone)
        depthcounts[depth] = depthcounts.get(depth, 0) + 1

    print "\n* Successes: {0} of {1}".format(successes, numzones)
    print "* Depth Report:"
    for depth, count in depthcounts.iteritems():
        print "*   {0} order zones created: {1}".format(
            _ordinal(depth), count
        )


def create_zones(numzones, numprocs=1, tenant=TENANT, host=HOST):
    """
    Creates random zones, with the option to split zone creation among multiple processes
    :param numzones: Number of zones to create
    :param numprocs: Number of processes to spawn for zone creation
    """
    procs = []
    results = Queue()
    newzones = []
    for i in range(numprocs):
        # Delegate zones to proccess
        zones_to_delegate = numzones / numprocs
        if i == numprocs - 1:
            zones_to_delegate += numzones % numprocs

        # Spawn process
        # TODO: Pass in existing zones to oldzonequeue
        p = Process(target=_create_zones_proc,
                    args=(zones_to_delegate,),
                    kwargs={
                        'newzonequeue': results,
                        'tenant': tenant,
                        'host': host
                    })
        procs.append(p)
        p.start()
        if numprocs != 1:
            print "Process {0} spawned".format(p.pid)

    # Wait until processes are finished
    successes = 0
    while len(procs) > 0:
        for p in procs:
            if p.is_alive():
                time.sleep(0.05)
                break
            else:
                if numprocs != 1:
                    print "\nProcess {0} completed".format(p.pid),
                procs.remove(p)
        while not results.empty():
            newzones.append(results.get(block=True))
            successes += 1
            sys.stdout.write("\rCreated zone {0} of {1}".format(
                successes, numzones))
            sys.stdout.flush()
    print ""

    # Compile and print results
    while not results.empty():
        newzones.append(results.get())

    depthcounts = {}
    for newzone in newzones:
        depth = _zone_depth(newzone)
        depthcounts[depth] = depthcounts.get(depth, 0) + 1

    successes = len(newzones)
    print "\n* Successes: {0} of {1}".format(successes, numzones)
    print "* Depth Report:"
    for depth, count in depthcounts.iteritems():
        print "*   {0} order zones created: {1}".format(
            _ordinal(depth), count
        )

    print "* Tenant {0} now has {1} zones\n".format(tenant, get_num_zones(tenant, host))


def create_zone(zone_name, zone_email="host@example.com",
                tenant=TENANT, host=HOST):
    """
    Create a zone with the specified zone name
    :param zone_name: Name of zone to create
    :param zone_email: Zone's admin email
    """
    zone_url, headers = _get_request_data("/v2/zones",
                                          tenant=tenant,
                                          host=host)
    data = {
        "zone": {
            "name": zone_name,
            "email": zone_email
        }
    }
    r = requests.post(zone_url, data=json.dumps(data), headers=headers)
    return r


def get_zone_id(zone_name, tenant=TENANT, host=HOST):
    """
    Retrieve ID for the zone with the specified name
    :param zone_name: Name of zone to search for
    """
    zone_url, headers = _get_request_data("/v2/zones?name={0}".format(zone_name),
                                          tenant=tenant,
                                          host=host)
    r = requests.get(zone_url, headers=headers)

    if r.status_code != 200:
        _print_error(r.status_code, r.text)
        return None

    zones = r.json()['zones']

    if len(zones) == 0:
        return None

    zone = zones[0]
    return zone['id']


def _create_zones_proc(numzones, newzonequeue=None, oldzones=None, tenantqueue=None, tenant=TENANT, host=HOST):
    """
    Individual zone creation process

    :param numzones: Number of zones to create. Ignored if tenantqueue is not None
    :param newzones: (optional) Shared queue for putting created zones into
    :param oldzones: (optional) List of zones that already exist. May help avoid name collisions.
    :param tenantqueue: (optional) Shared queue of (tenant, numzone) pairs. Will override numzones and tenants.
    :param tenants: Tenant ID to create zones for. Ignored if tenantqueue is not None
    """

    if not tenantqueue:
        tenantqueue = Queue()
        tenantqueue.put((tenant, numzones))

    # Pop tenant and numzones from tenant queue
    while not tenantqueue.empty():
        # Get next tenant
        try:
            currtenant, currnumzones = tenantqueue.get(block=True, timeout=0.1)
            print "\nTenant '{0}': Creating {1} zones...".format(
                currtenant, currnumzones)
        except QueueEmpty:
            break

        zones = set()

        if oldzones:
            for oldzone in oldzones:
                zones.add(oldzone)

        # Generate new zone name
        # Add PID so multiple processes can add zones w/o collisions
        # Add Tenant ID so multiple tenants can add zones w/o collisions
        for zonenum in range(currnumzones):
            newzone = "{0}-{1}-{2}.{3}".format(
                random.choice(words),
                os.getpid(),
                currtenant,
                random.choice(tlds),
            )

            while newzone in zones:
                # Collision: make a random subzone of newzone and check again
                newzone = "{0}.{1}".format(random.choice(words), newzone)

            # Add zone
            r = create_zone(newzone, tenant=currtenant, host=host)

            # Check response
            if r.status_code != 201:
                _print_error(r.status_code, r.text)
                continue

            # Log successful zone creation
            zones.add(newzone)

            # Add new zones to shared queue
            if newzonequeue:
                newzonequeue.put(newzone, block=True)


def _get_request_data(url="", tenant=TENANT, host=HOST):
    """
    Retrieve the necessary data for making request calls
    :param url: Everything after the port number.
    Combined with the host to form the full URL.
    :return: Tuple with the full request URL, followed by the HTTP headers
    """
    full_url = "{0}{1}".format(host, url)

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Auth-Project-ID': tenant,
        'X-Roles': 'admin'
    }

    return full_url, headers


def _print_error(errcode, message=None):
    print "\nERROR {0}{1}{2}".format(
        errcode,
        ": " if message else "",
        message)


def _zone_depth(zonename):
    return zonename.count(".")


def _ordinal(num):
    return "%d%s" % (num, "tsnrhtdd"[((num / 10 % 10) != 1) *
                                     ((num % 10) < 4) *
                                     num % 10::4])

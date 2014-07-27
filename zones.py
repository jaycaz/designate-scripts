# Jordan Cazamias
# Zone Generator

import json
from multiprocessing import Process
import os
import random
import string
import sys
import time


import requests

HOST = "http://192.168.33.8:9001"
TENANT_ID = 'A'

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
TENANTS = range(50)

def create_server(servername="ns.servers.com.", host=HOST):
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
        print "\n** Error code {0}: {1}".format(
            r.status_code, r.text)
        return


def change_zones_quota(newquota, tenant=TENANT_ID, host=HOST):
    quota_url, headers = _get_request_data("/v2/quotas/" + tenant,
                                           tenant=tenant,
                                           host=host)
    data = {
        "quota": {
        "zones": newquota
        }
    }

    r = requests.patch(quota_url, data=json.dumps(data), headers=headers)
    if r.status_code == 200:
        print "Max zones quota updated to {0}".format(newquota)
    else:
        print "Quota update failed."
        print "\n** Error code {0}: {1}".format(
            r.status_code, r.text)
        return

def get_num_zones(tenant=TENANT_ID, host=HOST):
    zone_url, headers = _get_request_data("/v1/reports/counts",
                                          tenant=tenant,
                                          host=host)
    r = requests.get(zone_url, headers=headers)

    if r.status_code != 200:
        print "\n** Error code {0}: {1}".format(
            r.status_code, r.text)
        return

    j = r.json()
    numzones = j['domains']

    return numzones

# Deletes all zones for tenants in tenants list
def delete_zones_multitenant(tenants=TENANTS, host=HOST):
    for tenant in tenants:
        if get_num_zones(tenant, host=HOST) != 0:
            delete_zones(tenant=tenant, host=host)


# Deletes a certain number of zones, or all zones
def delete_zones(numdelete=None, numprocs=1, tenant=TENANT_ID, host=HOST):
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

    print "Deleting {0} zones...\n".format(numdelete),
    successes = 0

    for i in range(numdelete):
        z = sorted_zones[i]
        r = delete_zone(z['id'], tenant=tenant, host=HOST)

        if r.status_code == 204:
            sys.stdout.write("\rDeleted zone {0} of {1}".format(
                i+1, numdelete
            ))
            sys.stdout.flush()
            successes += 1
        else:
            print "\n** Error code {0}: {1}".format(
                r.status_code, r.text)

    print "\n"
    print "> Successes: {0} of {1}".format(successes, numdelete)
    print "> Tenant {0} now has {1} zones".format(
        tenant, get_num_zones(tenant, host))

# Deletes a specific zone
def delete_zone(zoneid, tenant=TENANT_ID, host=HOST):
    zone_url, headers = _get_request_data("/v2/zones/" + zoneid,
                                          tenant=tenant,
                                          host=host)
    r = requests.delete(zone_url, headers=headers)
    return r

# Create zones, randomly distributed among a list of tenant IDs
def create_zones_multitenant(numzones, tenants=TENANTS, host=HOST):
    tenantcounts = {}
    for i in range(numzones):
        randtenant = random.choice(tenants)
        if randtenant in tenantcounts:
            tenantcounts[randtenant] += 1
        else:
            tenantcounts[randtenant] = 1

    print "Creating zones for tenants..."
    for tenant, num in tenantcounts.iteritems():
        print "Tenant '{0}': {1} zones".format(tenant, num)
        create_zones(num, tenant=tenant, host=HOST)


# Creates a certain number of randomly named zones/subzones
# Supports multiple processes which operate in their own namespace
def create_zones_multiproc(numzones, numprocs=1, tenant=TENANT_ID, host=HOST):
    print "Generating {0} zones...".format(numzones)

    procs = []
    for i in range(numprocs):
        # Delegate zones to proccess
        zones_to_delegate = numzones / numprocs
        if i == numprocs - 1:
            zones_to_delegate += numzones % numprocs

        # Spawn process
        p = Process(target=create_zones,
                    args=(zones_to_delegate, tenant, host))
        procs.append(p)
        p.start()
        if numprocs != 1:
            print "Spawned process {0}".format(p.pid)

    # Wait until processes are finished
    procs_alive = True
    while procs_alive:
        for p in procs:
            if p.is_alive():
                time.sleep(0.05)
                break
        else:
            procs_alive = False

    print "* Tenant {0} now has {1} zones".format(tenant, get_num_zones(tenant, host))

# Create specific zone
def create_zone(zone_name, zone_email="host@example.com",
                tenant=TENANT_ID, host=HOST):
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

def get_zone_id(zone_name, tenant=TENANT_ID, host=HOST):
    zone_url, headers = _get_request_data("/v2/zones?name=" + zone_name,
                                          tenant=tenant,
                                          host=host)
    r = requests.get(zone_url, headers=headers)

    if r.status_code != 200:
        print "\n** Error code {0}: {1}".format(
            r.status_code, r.text)
        return None

    zones = r.json()['zones']

    if len(zones) == 0:
        return None

    zone = zones[0]
    return zone['id']


# Function for individual create_zones process
def create_zones(numzones, tenant=TENANT_ID, host=HOST):
    zone_url, headers = _get_request_data("/v2/zones",
                                          tenant=tenant,
                                          host=host)

    # Retrieve list of existing zones
    r = requests.get(zone_url, headers=headers)
    if r.status_code != 200:
        print "\n** Error code {0}: {1}".format(
            r.status_code, r.text)
        return
    j = r.json()
    zones = set()
    for oldzone in [zone['name'] for zone in j['zones']]:
        zones.add(oldzone)

    depthcounts = {}

    # Generate new zone name
    # Add PID so multiple processes can add zones w/o collisions
    # Add Tenant ID so multiple tenants can add zones w/o collisions
    for zonenum in range(numzones):
        newzone = "{0}.{1}.{2}.{3}".format(
            random.choice(words),
            tenant,
            os.getpid(),
            random.choice(tlds),
        )

        while newzone in zones:
            # Collision: make a random subzone of newzone and check again
            newzone = "{0}.{1}".format(random.choice(words), newzone)

        # Add zone
        r = create_zone(newzone, tenant=tenant, host=host)

        # Check response
        if r.status_code != 201:
            print "\n** Error code {0}: {1}".format(
                r.status_code, r.text)
            continue

        zones.add(newzone)

        # Log successfully created zone
        depth = _zone_depth(newzone)
        depthcounts[depth] = depthcounts.get(depth, 0) + 1
        sys.stdout.write("\rCreated zone {0} of {1}".format(zonenum+1, numzones))
        sys.stdout.flush()


    successes = sum([v for v in depthcounts.values()])
    print "\n\n*** Process {0}: Zone creation successful ***".format(os.getpid())
    print "* Successes: {0} of {1}".format(successes, numzones)
    print "* Depth Report:"
    for depth, count in depthcounts.iteritems():
        print "* - {0} order zones created: {1}".format(
            _ordinal(depth), count
        )

def _get_request_data(url="", host=HOST, tenant=TENANT_ID):
    full_url = "{0}{1}".format(host, url)

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Auth-Project-ID': tenant,
        'X-Roles': 'admin'
    }

    return full_url, headers

def _zone_depth(zonename):
    return zonename.count(".")

def _ordinal(n):
    return "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])


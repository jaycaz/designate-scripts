# Jordan Cazamias
# Zone Generator

import json
import os
import random
import sys


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
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'X-Auth-Project-ID': TENANT_ID,
    'X-Roles': 'admin'
}

def change_zones_quota(newquota, tenant=TENANT_ID, host=HOST):
    quota_url = "{0}/v2/quotas/{1}".format(host, tenant)
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
    zone_url = "{0}/v2/zones".format(host)
    r = requests.get(zone_url, headers=headers)

    if r.status_code != 200:
        print "\n** Error code {0}: {1}".format(
            r.status_code, r.text)
        return

    j = r.json()
    numzones = len(j['zones'])

    print "Number of zones for tenant {0}: {1}".format(
        tenant, numzones
    )

# Deletes a certain number of zones, or all zones
def delete_zones(numdelete=None, tenant=TENANT_ID, host=HOST):
    zone_url = "{0}/v2/zones".format(host)
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
        r = requests.delete("{0}/{1}".format(zone_url, z['id']),
                            headers=headers)

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
        tenant, len(j['zones']) - successes)

# Creates a certain number of randomly named zones/subzones
def create_zones(numzones, tenant=TENANT_ID, host=HOST):
    zone_url = "{0}/v2/zones".format(host)
    print "Generating {0} zones...".format(numzones)

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

    for zonenum in range(numzones):
        newzone = "{0}.{1}".format(
            random.choice(words),
            random.choice(tlds)
        )

        while newzone in zones:
            # Make newzone a subzone of itself instead
            newzone = "{0}.{1}".format(random.choice(words), newzone)
            #print "{0}: Creating subzone '{1}'".format(zonenum, newzone)

        newzone_with_pid = "{0}-{1}".format(os.getpid(), newzone)

        # Add zone
        data = {
            "zone": {
                "name": newzone_with_pid,
                "email": "host@example.com"
            }
        }
        r = requests.post(zone_url, data=json.dumps(data), headers=headers)

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
    print "\n> Successes: {0} of {1}".format(successes, numzones)
    print "> Depth Report:"
    for depth, count in depthcounts.iteritems():
        print "> - {0} order zones created: {1}".format(
            _ordinal(depth), count
        )
    print "> Tenant {0} now has {1} zones".format(tenant, len(zones))

def _zone_depth(zonename):
    return zonename.count(".")

def _ordinal(n):
    return "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])


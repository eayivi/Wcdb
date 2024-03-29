from models import *

import datetime
from datetime import time
from xml.etree.ElementTree import tostring

def insert(root):
    """
    root is an ElementTree object
    insert distributes each case depending on its etype
    specific 'handlers' are called for each element in a given entity which fills 
    database with necessary info to match the xml
    """
    assert root is not None
    for elem in root:
        if elem.tag == 'Crisis':
            criHandler(elem)
        elif elem.tag == 'Organization':
            orgHandler(elem)
        elif elem.tag == 'Person':
            perHandler(elem)

def getEntity(etype, eid):
    """
    etype is the entity's type
    eid is the entity's ID
    getEntity returns the matching ID object if it exists
    if it doesn't exist, it creates and returns a new one
    """
    assert etype in (Crisis, Organization, Person)
    assert eid[:3] in ('CRI', 'ORG', 'PER')
    e = None
    try:
        e = etype.objects.get(id=eid)
    except etype.DoesNotExist:
        e = etype(id=eid)
    e.save()
    assert e is not None
    return e

def criHandler(node):
    """
    node is the start node of a Crisis
    criHandler parses the xml info for this crisis
    gathered info is stored in django module database
    """
    assert node is not None
    c = getEntity(Crisis, node.attrib.get('ID'))
    c.name = node.attrib.get('Name')
    for attr in node:
        if attr.tag == 'Organizations':
            for elem in attr:
                c.organizations.add(getEntity(Organization, elem.attrib.get('ID')))
        if attr.tag == 'People':
            for elem in attr:
                c.people.add(getEntity(Person, elem.attrib.get('ID')))
        if attr.tag == 'Kind':
            c.kind = attr.text
        if attr.tag == 'Date':
            c.date = attr.text
        if attr.tag == 'Time':
            c.time = attr.text
        if attr.tag == 'Locations':
            c.location += ''.join([v for v in [tostring(li).strip() for li in attr] if v not in c.location])
        if attr.tag == 'HumanImpact':
            c.himpact += ''.join([v for v in [tostring(li).strip() for li in attr] if v not in c.himpact])
        if attr.tag == 'EconomicImpact':
            c.eimpact += ''.join([v for v in [tostring(li).strip() for li in attr] if v not in c.eimpact])
        if attr.tag == 'ResourcesNeeded':
            c.resources += ''.join([v for v in [tostring(li).strip() for li in attr] if v not in c.resources])
        if attr.tag == 'WaysToHelp':
            c.help += ''.join([v for v in [tostring(li).strip() for li in attr] if v not in c.help])
        if attr.tag == 'Common':
            comHandler(attr, c)
    assert c is not None
    c.save()

def orgHandler(node):
    """
    node is the start node of an Organization
    orHandler parses the xml info for this organizaton
    gathered info is stored in django module database
    """
    assert node is not None
    o = getEntity(Organization, node.attrib.get('ID'))
    o.name = node.attrib.get('Name')
    for attr in node:
        if attr.tag == 'Crises':
            for elem in attr:
                o.crises.add(getEntity(Crisis, elem.attrib.get('ID')))
        if attr.tag == 'People':
            for elem in attr:
                o.people.add(getEntity(Person, elem.attrib.get('ID')))
        if attr.tag == 'Kind':
            o.kind = attr.text
        if attr.tag == 'Location':
            o.location = attr.text
        if attr.tag == 'History':
            o.history += ''.join([v for v in [tostring(li).strip() for li in attr] if v not in o.history])
        if attr.tag == 'ContactInfo':
            o.contact += ''.join([v for v in [tostring(li).strip() for li in attr] if v not in o.contact])
        if attr.tag == 'Common':
            comHandler(attr, o)
    assert o is not None
    o.save()

def perHandler(node):
    """
    node is the start node of a Person
    perHandler parses the xml info for this person
    gathered info is stored in django module database
    """
    assert node is not None
    p = getEntity(Person, node.attrib.get('ID'))
    p.name = node.attrib.get('Name')
    for attr in node:
        if attr.tag == 'Crises':
            for elem in attr:
                p.crises.add(getEntity(Crisis, elem.attrib.get('ID')))
        if attr.tag == 'Organizations':
            for elem in attr:
                p.organizations.add(getEntity(Organization, elem.attrib.get('ID')))
        if attr.tag == 'Kind':
            p.kind = attr.text
        if attr.tag == 'Location':
            p.location = attr.text
        if attr.tag == 'Common':
            comHandler(attr, p)
    assert p is not None
    p.save()

def insertElem(query, attr):
    """
    query is a dict specifying the type of element we want to insert
    attr  is a dict utilized if the query type does not exist
    insertElem is a helper method for comHandler
    """
    assert type(query) is dict
    assert type(attr) is dict
    try:
        WebElement.objects.get(**query)
    except WebElement.DoesNotExist:
        attr.update(query)
        w = WebElement(**attr)
        w.save()

def comHandler(node, e):
    """
    node is the common element of the entity calling it
    e is the entity
    comHandler parses the xml info nested under common for
    the entity calling it.
    """
    assert node is not None
    assert e is not None
    for attr in node:
        if attr.tag == 'Citations':
            for elem in attr:
                insertElem({'href' : elem.attrib.get('href')}, {'entity' : e, 'ctype' : 'CITE', 'text' : elem.text})
        if attr.tag == 'ExternalLinks':
            for elem in attr:
                insertElem({'href' : elem.attrib.get('href')}, {'entity' : e, 'ctype' : 'LINK', 'text' : elem.text})
        if attr.tag == 'Images':
            for elem in attr:
                insertElem({'embed' : elem.attrib.get('embed')}, {'entity' : e, 'ctype' : 'IMG', 'text' : elem.text})
        if attr.tag == 'Videos':
            for elem in attr:
                if 'youtube' in elem.attrib.get('embed'):
                    insertElem({'embed' : elem.attrib.get('embed')}, {'entity' : e, 'ctype' : 'VID', 'text' : elem.text})
        if attr.tag == 'Maps':
            for elem in attr:
                if 'google' in elem.attrib.get('embed'):
                    insertElem({'embed' : elem.attrib.get('embed')}, {'entity' : e, 'ctype' : 'MAP', 'text' : elem.text})
        if attr.tag == 'Feeds':
            for elem in attr:
                insertElem({'embed' : elem.attrib.get('embed')}, {'entity' : e, 'ctype' : 'FEED', 'text' : elem.text})
        if attr.tag == 'Summary':
            e.summary = attr.text

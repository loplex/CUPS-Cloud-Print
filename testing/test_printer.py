#    CUPS Cloudprint - Print via Google Cloud Print
#    Copyright (C) 2011 Simon Cadman
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
import cups
import urllib
import logging
import sys
import subprocess
import os
import pytest
import shutil
sys.path.insert(0, ".")
from printermanager import PrinterManager
from mockrequestor import MockRequestor
from ccputils import Utils

global printers, printerManagerInstance

testCapabilities1 = {'printer':
                     {'color':
                      {
                          'option':
                          [
                              {'is_default': True, 'vendor_id': '2', 'type': 'STANDARD_COLOR'},
                              {'vendor_id': '1', 'type': 'STANDARD_MONOCHROME'}
                          ]
                     },
                     'media_size':
                     {
                          'option':
                          [
                                {'vendor_id': '1', 'height_microns': 279400, 'width_microns': 215900, 'name': 'NA_LETTER', 'custom_display_name': 'Letter'},
                                {'vendor_id': '3', 'height_microns': 431800, 'width_microns': 279400, 'name': 'NA_LEDGER', 'custom_display_name': 'Tabloid'},
                                {'vendor_id': '5', 'height_microns': 355600, 'width_microns': 215900, 'name': 'NA_LEGAL', 'custom_display_name': 'Legal'},
                                {'vendor_id': '6', 'height_microns': 215900, 'width_microns': 139700, 'name': 'NA_INVOICE', 'custom_display_name': 'Statement'},
                                {'vendor_id': '7', 'height_microns': 266700, 'width_microns': 184100, 'name': 'NA_EXECUTIVE', 'custom_display_name': 'Executive'},
                                {'vendor_id': '8', 'height_microns': 420000, 'width_microns': 297000, 'name': 'ISO_A3', 'custom_display_name': 'A3'},
                                {'width_microns': 210000, 'vendor_id': '9', 'is_default': True, 'height_microns': 297000, 'custom_display_name': 'A4', 'name': 'ISO_A4'},
                                {'vendor_id': '11', 'height_microns': 210000, 'width_microns': 148000, 'name': 'ISO_A5', 'custom_display_name': 'A5'},
                                {'vendor_id': '12', 'height_microns': 364000, 'width_microns': 257000, 'name': 'JIS_B4', 'custom_display_name': 'B4 (JIS)'},
                                {'vendor_id': '13', 'height_microns': 257000, 'width_microns': 182000, 'name': 'JIS_B5', 'custom_display_name': 'B5 (JIS)'}
                          ]
                     },
                     'page_orientation':
                     {
                          'option':
                          [
                              {'is_default': True, 'type': 'PORTRAIT', 'display_name' : 'portrait'},
                              {'type': 'LANDSCAPE', 'custom_display_name' : 'landscape'},
                              {'type': 'AUTO'}
                          ]
                     },
                     'something':
                     {
                          'option':
                          [
                              {'is_default': True, 'type': 'one'},
                              {'type': 'testval'}
                          ]
                     },
                     'test-reserved-word':
                     {
                          'option':
                          [
                              {'is_default': True, 'type': 'Resolution'},
                              {'type': 'testtwo'}
                          ]
                     },
                     'supported_content_type':
                     [
                          {'content_type': 'application/pdf'}
                     ],
                     'dpi':
                     {
                          'option':
                          [
                              {'is_default': True, 'horizontal_dpi': 600, 'vertical_dpi': 600 },
                              {'horizontal_dpi': 800, 'vertical_dpi': 800 }
                          ]
                     },
                     'empty_options':
                     {
                          'option':
                          [
                          ]
                     }
                     },
                     'version': '1.0'
                    }

def setup_function(function):
    # setup mock requestors
    global printers, printerManagerInstance

    mockRequestorInstance = MockRequestor()
    mockRequestorInstance.setAccount('testaccount2@gmail.com')
    mockRequestorInstance.printers = [{'name': 'Save to Google Drive',
                                       'id': '__test_save_docs',
                                       'capabilities': testCapabilities1},
                                      {'name': 'Save to Google Drive 2',
                                       'displayName': 'Save to Google Drive 2 DisplayName',
                                       'id': '__test_save_docs_2',
                                       'capabilities' : {'printer' : {}}}
                                      ]

    printerManagerInstance = PrinterManager(mockRequestorInstance)
    printers = printerManagerInstance.getPrinters()


def teardown_function(function):
    global requestors
    requestors = None
    logging.shutdown()
    reload(logging)


def test_getAccount():
    global printers
    for printer in printers:
        assert printer.getAccount() == "testaccount2@gmail.com"


def test_getRequestor():
    global printers
    for printer in printers:
        requestor = printer.getRequestor()
        assert requestor.__class__.__name__ == "MockRequestor"
        assert requestor.getAccount() == 'testaccount2@gmail.com'


def test_getMimeBoundary():
    global printers
    for printer in printers:
        assert printer._getMimeBoundary() != 'test_boundry'
        assert len(printer._getMimeBoundary()) > 30
        assert len(printer._getMimeBoundary()) < 50

        printer._mime_boundary = 'test_boundry'
        assert printer._getMimeBoundary() == 'test_boundry'


def test_getCapabilitiesItems():
    global printers
    printer = printers[0]
    correctCapabilities = testCapabilities1
    assert printer._fields['capabilities'] == correctCapabilities
    assert printer._fields['capabilities'] == printer['capabilities']
    del printer._fields['capabilities']
    assert 'capabilities' not in printer._fields
    assert printer['capabilities'] == correctCapabilities
    assert printer._fields['capabilities'] == printer['capabilities']


def test_getCapabilitiesItemsMissing():
    global printers
    printer = printers[1]
    assert 'capabilities' in printer._fields
    assert printer['capabilities'] == {'printer' : {}}


def test_contains():
    global printers
    for printer in printers:
        assert 'testvalue' not in printer
        printer._fields['testvalue'] = 'test'
        assert 'testvalue' in printer
        del printer._fields['testvalue']
        assert 'testvalue' not in printer


def test_fetchDetails():
    global printers
    assert printers[0]._fetchDetails() == {'name': 'Save to Google Drive',
                                           'id': '__test_save_docs',
                                           'capabilities': testCapabilities1}
    assert printers[1]._fetchDetails() == {'displayName': 'Save to Google Drive 2 DisplayName',
                                           'id': '__test_save_docs_2', 'name': 'Save to Google Drive 2',
                                           'capabilities': {'printer' : {}}}


def test_getURI():
    global printers
    assert printers[0].getURI() == Utils._PROTOCOL + "testaccount2%40gmail.com/__test_save_docs"
    assert printers[1].getURI() == Utils._PROTOCOL + "testaccount2%40gmail.com/__test_save_docs_2"


def test_getDisplayName():
    global printers
    assert printers[0].getDisplayName() == "Save to Google Drive"
    assert printers[1].getDisplayName() == "Save to Google Drive 2 DisplayName"


def test_getListDescription():
    global printers
    assert printers[0].getListDescription() == "Save to Google Drive - " + Utils._PROTOCOL + \
        "testaccount2%40gmail.com/__test_save_docs - testaccount2@gmail.com"
    assert printers[1].getListDescription() == "Save to Google Drive 2 DisplayName - " + \
        Utils._PROTOCOL + "testaccount2%40gmail.com/__test_save_docs_2 - testaccount2@gmail.com"


def test_getLocation():
    global printers
    assert printers[0].getLocation() == ''
    printers[0]._fields['tags'] = ['novalue', 'name=value', 'location=test-location']
    assert printers[0].getLocation() == 'test-location'


def test_getCUPSBackendDescription():
    global printers
    assert printers[0].getCUPSBackendDescription() == 'network ' + Utils._PROTOCOL + \
        'testaccount2%40gmail.com/__test_save_docs "Save to Google Drive" "Save to Google Drive" "MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL:' + \
        Utils._PROTOCOL + 'testaccount2%40gmail.com/__test_save_docs"'
    assert printers[1].getCUPSBackendDescription() == 'network ' + Utils._PROTOCOL + \
        'testaccount2%40gmail.com/__test_save_docs_2 "Save to Google Drive 2 DisplayName" "Save to Google Drive 2 DisplayName" "MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL:' + \
        Utils._PROTOCOL + 'testaccount2%40gmail.com/__test_save_docs_2"'
    printers[0]._fields['tags'] = ['novalue', 'name=value', 'location=test-location']
    assert printers[0].getCUPSBackendDescription() == 'network ' + Utils._PROTOCOL + 'testaccount2%40gmail.com/__test_save_docs "Save to Google Drive" "Save to Google Drive @ test-location" "MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL:' + \
        Utils._PROTOCOL + 'testaccount2%40gmail.com/__test_save_docs" "test-location"'


def test_getCUPSDriverDescription():
    global printers
    assert printers[0].getCUPSDriverDescription() == '"cupscloudprint:testaccount2%40gmail.com:__test_save_docs.ppd" en "Google" "Save to Google Drive (testaccount2@gmail.com)" "MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL:' + \
        Utils._PROTOCOL + 'testaccount2%40gmail.com/__test_save_docs"'
    assert printers[1].getCUPSDriverDescription() == '"cupscloudprint:testaccount2%40gmail.com:__test_save_docs_2.ppd" en "Google" "Save to Google Drive 2 DisplayName (testaccount2@gmail.com)" "MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL:' + \
        Utils._PROTOCOL + 'testaccount2%40gmail.com/__test_save_docs_2"'


def test_getPPDName():
    global printers
    assert printers[0].getPPDName(
    ) == "cupscloudprint:testaccount2%40gmail.com:__test_save_docs.ppd"
    assert printers[1].getPPDName(
    ) == "cupscloudprint:testaccount2%40gmail.com:__test_save_docs_2.ppd"


def test_generatePPD():
    global printers
    for printer in printers:
        ppddata = printer.generatePPD()
        assert isinstance(ppddata, basestring)

        # test ppd data is valid
        tempfile = open('/tmp/.ppdfile', 'w')
        tempfile.write(ppddata)
        tempfile.close()

        p = subprocess.Popen(['cupstestppd', '/tmp/.ppdfile'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        testdata = p.communicate()[0]
        print testdata
        os.unlink('/tmp/.ppdfile')
        assert p.returncode == 0


def test_sanitizeText():
    global printers
    for checkReserved in [False, True]:
        assert printers[0]._sanitizeText("", checkReserved) == ""
        assert printers[0]._sanitizeText("TESTSTRING", checkReserved) == "TESTSTRING"
        assert printers[0]._sanitizeText("TEST:; STRING /2", checkReserved) == "TEST___STRING_-2"
        assert printers[0]._sanitizeText("TEST:; STRING /2", checkReserved) == "TEST___STRING_-2"

    assert printers[0]._sanitizeText("Duplex") == "Duplex"
    assert printers[0]._sanitizeText("Duplex", True) == "GCP_Duplex"

    # ensure strips newlines
    assert printers[0]._sanitizeText("Test\ntest2") == "Testtest2"
    assert printers[0]._sanitizeText("Test\r\ntest2") == "Testtest2"


def test_getInternalName():
    global printers
    printerItem = printers[0]

    internalCapabilityTests = []
    # load test file and try all those
    for filelineno, line in enumerate(open('testing/testfiles/capabilitylist')):
        internalCapabilityTests.append({'name': line.decode("utf-8")})

    for internalTest in internalCapabilityTests:
        assert printerItem._getInternalName(
            internalTest, 'capability') not in printerItem._RESERVED_CAPABILITY_WORDS
        assert not printerItem._getInternalName(internalTest, 'capability').startswith(
            printerItem._RESERVED_CAPABILITY_PREFIXES)
        assert ':' not in printerItem._getInternalName(internalTest, 'capability')
        assert ' ' not in printerItem._getInternalName(internalTest, 'capability')
        assert len(printerItem._getInternalName(internalTest, 'capability')) <= 30
        assert len(printerItem._getInternalName(internalTest, 'capability')) >= 1

    for internalTest in internalCapabilityTests:
        for capabilityName in ["psk:JobDuplexAllDocumentsContiguously", "other", "psk:PageOrientation", "cupsFilter"]:
            assert printerItem._getInternalName(
                internalTest, 'option', capabilityName) not in printerItem._RESERVED_CAPABILITY_WORDS
            assert not printerItem._getInternalName(internalTest, 'option', capabilityName).startswith(
                printerItem._RESERVED_CAPABILITY_PREFIXES)
            assert ':' not in printerItem._getInternalName(internalTest, 'option', capabilityName)
            assert ' ' not in printerItem._getInternalName(internalTest, 'option')
            assert len(printerItem._getInternalName(internalTest, 'option', capabilityName)) <= 30
            assert len(printerItem._getInternalName(internalTest, 'option', capabilityName)) >= 1

    # ensure fixed mappings works correctly
    for fixedCapabilityName in printerItem._FIXED_CAPABILITY_MAPPINGS:
        assert printerItem._getInternalName(
            {'name': fixedCapabilityName}, 'capability') == printerItem._FIXED_CAPABILITY_MAPPINGS[fixedCapabilityName]

    for fixedCapabilityName in printerItem._FIXED_OPTION_MAPPINGS:
        for fixedOptionName in printerItem._FIXED_OPTION_MAPPINGS[fixedCapabilityName]:
            assert printerItem._getInternalName({'name': fixedOptionName}, 'option', fixedCapabilityName) == printerItem._FIXED_OPTION_MAPPINGS[
                fixedCapabilityName][fixedOptionName]


def test_encodeMultiPart():
    global printers
    assert isinstance(printers[0]._encodeMultiPart([('test', 'testvalue')]), basestring)
    assert 'testvalue' in printers[0]._encodeMultiPart([('test', 'testvalue')])
    assert 'Content-Disposition: form-data; name="test"' in printers[
        0]._encodeMultiPart([('test', 'testvalue')])


def test_getOverrideCapabilities():
    global printers
    printerItem = printers[0]
    assert printerItem._getOverrideCapabilities("") == {}
    assert printerItem._getOverrideCapabilities("landscape") == {'Orientation': 'Landscape'}
    assert printerItem._getOverrideCapabilities("nolandscape") == {'Orientation': 'Landscape'}
    assert printerItem._getOverrideCapabilities("test=one") == {'test': 'one'}
    assert printerItem._getOverrideCapabilities("test=one anothertest=two") == {
        'test': 'one', 'anothertest': 'two'}
    assert printerItem._getOverrideCapabilities("test=one anothertest=two Orientation=yes") == {
        'test': 'one', 'anothertest': 'two'}


def test_GetCapabilitiesDict():
    global printers
    printerItem = printers[0]
    assert printerItem._getCapabilitiesDict({}, {}, {}) == {'print': {}, 'version': '1.0'}
    assert printerItem._getCapabilitiesDict([{'name': 'test'}], {}, {}) == {'print': {}, 'version': '1.0'}
    assert printerItem._getCapabilitiesDict([{'name': 'Default' + 'test123', 'value': 'STANDARD_MONOCHROME'}, { 'name' : 'Defaulttestname', 'value': 'test1' }],
                                            {'test123':
                                                        {
                                                            'option':
                                                            [
                                                                {'is_default': True, 'vendor_id': '2', 'type': 'STANDARD_COLOR'},
                                                                {'vendor_id': '1', 'type': 'STANDARD_MONOCHROME'}
                                                            ]
                                                        },
                                             'testname':
                                                        {
                                                            'option':
                                                            [
                                                                {'is_default': True, 'vendor_id': '2', 'name': 'test1', "test_param_1" : "test123", "test_param_2" : "test456"},
                                                                {'vendor_id': '1', 'name': 'test2', "test_param_1" : "test1", "test_param_2" : "test2"}
                                                            ]
                                                        },
                                             'testnooption':
                                                        {
                                                            'option':
                                                            [
                                                                {'is_default': True, 'vendor_id': '2', 'horizontal_dpi': 300, 'vertical_dpi' : 300, 'display_name': 'test' },
                                                                {'vendor_id': '2', 'horizontal_dpi': 400, 'vertical_dpi' : 400, 'display_name': 'test123' }
                                                            ]
                                                        }
                                                            
                                                            }, {'test123': 'STANDARD_MONOCHROME'}) == {
                                                                                                    "version": "1.0",
                                                                                                        "print": {
                                                                                                            "testname":{"vendor_id":"2", "test_param_1" : "test123", "test_param_2" : "test456"},
                                                                                                            "test123": {"type": "STANDARD_MONOCHROME"}
                                                                                                        }
                                                                                                    }


def test_attrListToArray():
    global printers
    assert len(list(printers[0]._attrListToArray({}))) == 0


def test_getCapabilities():
    global printers, printerManagerInstance
    printer = printers[1]
    connection = cups.Connection()

    # get test ppd
    ppdid = 'MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL'
    ppds = connection.getPPDs(ppd_device_id=ppdid)
    printerppdname, printerppd = ppds.popitem()

    assert printerManagerInstance.addPrinter(
        printer['name'],
        printer,
        connection,
        printerppdname) is not None
    emptyoptions = printer._getCapabilities(
        printerManagerInstance.sanitizePrinterName(printer['name']), "landscape")
    assert isinstance(emptyoptions, dict)
    assert isinstance(emptyoptions['print'], dict)
    assert len(emptyoptions['print']) == 0
    connection.deletePrinter(printerManagerInstance.sanitizePrinterName(printer['name']))


def test_submitJob():
    global printers, printerManagerInstance
    printer = printers[0]
    connection = cups.Connection()
    testprintername = printerManagerInstance.sanitizePrinterName(printer['name'])

    # get test ppd
    ppdid = 'MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL'
    ppds = connection.getPPDs(ppd_device_id=ppdid)
    printerppdname, printerppd = ppds.popitem()

    assert printerManagerInstance.addPrinter(
        printer['name'],
        printer,
        connection,
        printerppdname) is not None

    # test submitting job
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page.pdf',
        open('testing/testfiles/Test Page.pdf').read(),
        'Test Page',
        testprintername) == True
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page Doesnt Exist.pdf',
        '',
        'Test Page',
        testprintername) == False
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page Corrupt.pdf',
        open('testing/testfiles/Test Page Corrupt.pdf').read(),
        'Test Page',
        testprintername, 'landscape') == False

    # copy for rotating
    tmpDir = os.getenv('TMPDIR')
    if not tmpDir:
        tmpDir = "/tmp"
    tmpFile = os.path.join(tmpDir, 'Test Page.pdf')
    shutil.copy('testing/testfiles/Test Page.pdf', tmpFile)

    # test submitting job with rotate
    assert printer.submitJob(
        'pdf',
        tmpFile,
        open(tmpFile).read(),
        'Test Page',
        testprintername,
        "landscape") == True
    assert printer.submitJob(
        'pdf',
        tmpFile,
        open(tmpFile).read(),
        'Test Page',
        testprintername,
        "nolandscape") == True

    os.unlink(tmpFile)

    # test submitting job with no filename
    assert printer.submitJob(
        'pdf',
        '',
        'data',
        '',
        testprintername) == True

    # test submitting job with no name
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page.pdf',
        open('testing/testfiles/Test Page.pdf').read(),
        '',
        testprintername) == True
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page Doesnt Exist.pdf',
        '',
        '',
        testprintername) == False

    # png
    assert printer.submitJob(
        'png',
        'testing/testfiles/Test Page.png',
        open('testing/testfiles/Test Page.png').read(),
        'Test Page',
        testprintername) == True
    assert printer.submitJob(
        'png',
        'testing/testfiles/Test Page Doesnt Exist.png',
        '',
        'Test Page',
        testprintername) == False

    # ps
    assert printer.submitJob(
        'ps',
        'testing/testfiles/Test Page.ps',
        open('testing/testfiles/Test Page.ps').read(),
        'Test Page',
        testprintername) == False
    assert printer.submitJob(
        'ps',
        'testing/testfiles/Test Page Doesnt Exist.ps',
        '',
        'Test Page',
        testprintername) == False

    # test failure of print job
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page.pdf',
        open('testing/testfiles/Test Page.pdf').read(),
        'FAIL PAGE',
        testprintername) == False

    # test failure of print job with exception
    assert printer.submitJob(
        'pdf',
        'testing/testfiles/Test Page.pdf',
        open('testing/testfiles/Test Page.pdf').read(),
        'TEST PAGE WITH EXCEPTION',
        testprintername) == False

    # delete test printer
    connection.deletePrinter(testprintername)


@pytest.mark.skipif(
    os.getuid() == 0,
    reason="will only pass if running tests as non-root user")
def test_submitJobFileCreationFails():
    global printers, printerManagerInstance
    printer = printers[0]
    connection = cups.Connection()
    testprintername = printerManagerInstance.sanitizePrinterName(printer['name'])

    # get test ppd
    ppdid = 'MFG:Google;DRV:GCP;CMD:POSTSCRIPT;DES:GoogleCloudPrint;MDL'
    ppds = connection.getPPDs(ppd_device_id=ppdid)
    printerppdname, printerppd = ppds.popitem()

    assert printerManagerInstance.addPrinter(
        printer['name'],
        printer,
        connection,
        printerppdname) is not None

    # delete test printer
    connection.deletePrinter(testprintername)

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
import json
import urllib
import cups
import os
import stat
import grp
import pytest
import logging
import sys
sys.path.insert(0, ".")

from auth import Auth
from mockrequestor import MockRequestor
from oauth2client import client
from oauth2client import multistore_file
from ccputils import Utils


def setup_function(function):
    # setup mock requestors
    global requestors
    requestors = []

    # account without special chars
    mockRequestorInstance1 = MockRequestor()
    mockRequestorInstance1.setAccount('testaccount1')
    mockRequestorInstance1.printers = []
    requestors.append(mockRequestorInstance1)

    Auth.config = '/tmp/cloudprint.conf'


def teardown_function(function):
    if os.path.exists(Auth.config):
        os.unlink(Auth.config)
    logging.shutdown()
    reload(logging)


def test_fixConfigPermissions():
    configfile = open(Auth.config, "w")
    configfile.close()

    os.chmod(Auth.config, 0000)
    assert '0000' == oct(os.stat(Auth.config)[stat.ST_MODE])[-4:]
    assert True == Utils.FixFilePermissions(Auth.config)[0]
    assert '0660' == oct(os.stat(Auth.config)[stat.ST_MODE])[-4:]

    origconfig = Auth.config
    Auth.config = '/tmp/filethatdoesntexist'
    assert (False, False) == Utils.FixFilePermissions(Auth.config)
    Auth.config = origconfig


@pytest.mark.skipif(
    grp.getgrnam('lp').gr_gid not in (os.getgroups()) and os.getuid() != 0,
    reason="will only pass if running user part of lp group or root")
def test_fixConfigOwnerships():
    configfile = open(Auth.config, "w")
    configfile.close()

    assert Utils.GetLPID() != os.stat(Auth.config).st_gid
    assert True == Utils.FixFilePermissions(Auth.config)[1]
    assert Utils.GetLPID() == os.stat(Auth.config).st_gid


def test_setupAuth():
    testUserName = 'testaccount1'

    # create initial file
    assert os.path.exists(Auth.config) == False
    assert Auth.SetupAuth(False) == (False, False)
    assert os.path.exists(Auth.config) == True

    # ensure permissions are correct after creating config
    assert '0660' == oct(os.stat(Auth.config)[stat.ST_MODE])[-4:]

    # add dummy details
    storage = multistore_file.get_credential_storage(
        Auth.config,
        Auth.clientid,
        'testuseraccount',
        ['https://www.googleapis.com/auth/cloudprint'])

    credentials = client.OAuth2Credentials('test', Auth.clientid,
                                           'testsecret', 'testtoken', 1,
                                           'https://www.googleapis.com/auth/cloudprint', testUserName)
    storage.put(credentials)

    # ensure permissions are correct after populating config
    assert '0660' == oct(os.stat(Auth.config)[stat.ST_MODE])[-4:]

    # re-run to test getting credentials
    requestors, storage = Auth.SetupAuth(False)
    assert requestors is not None
    assert storage is not None

    # check deleting account
    assert Auth.DeleteAccount(testUserName) is None
    requestors, storage = Auth.SetupAuth(False)
    assert requestors == False
    assert storage == False

def test_setupAuthInteractive():
    
    # ensure running setup in interactive mode tries to read stdin
    with pytest.raises(IOError):
        Auth.SetupAuth(True)

def test_renewToken():
    global requestors
    storage = multistore_file.get_credential_storage(
        Auth.config,
        Auth.clientid,
        'testuseraccount',
        ['https://www.googleapis.com/auth/cloudprint'])
    
    credentials = client.OAuth2Credentials('test', Auth.clientid,
                                           'testsecret', 'testtoken', 1,
                                           'https://www.googleapis.com/auth/cloudprint', 'testaccount1')
    
    # test renewing token exits in non-interactive mode
    with pytest.raises(SystemExit):
        Auth.RenewToken(False, requestors[0], credentials,storage, 'test')
        
    # test renewing interactively tries to read from stdin
    with pytest.raises(IOError):
        assert Auth.RenewToken(True, requestors[0], credentials,storage, 'test') == False

@pytest.mark.skipif(
    grp.getgrnam('lp').gr_gid not in (os.getgroups()) and os.getuid() != 0,
    reason="will only pass if running user part of lp group or root")
def test_setupAuthOwnership():
    assert Auth.SetupAuth(False) == (False, False)

    # ensure ownership is correct after creating config
    assert Utils.GetLPID() == os.stat(Auth.config).st_gid

    # add dummy details
    storage = multistore_file.get_credential_storage(
        Auth.config,
        Auth.clientid,
        'testuseraccount',
        ['https://www.googleapis.com/auth/cloudprint'])

    credentials = client.OAuth2Credentials('test', Auth.clientid,
                                           'testsecret', 'testtoken', 1,
                                           'https://www.googleapis.com/auth/cloudprint', 'testaccount1')
    storage.put(credentials)

    # ensure ownership is correct after populating config
    assert Utils.GetLPID() == os.stat(Auth.config).st_gid

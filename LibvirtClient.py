#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Class for sending requests to libvirt
"""

import libvirt
import logging

LOGGER = logging.getLogger('LibvirtClient')



class LibvirtClient:
    """
.. class:: LibvirtClient
    """

    def __init__(self, uri, username, password):
        """
        Constructor, creating the class. It requires specifying a URI and
        a username and password for communicating with the hypervisor.
        The constructor will throw an exception if an invalid libvirt URI
        was specified.

        :param uri: libvirt URI
        :type uri: str
        :param username: API username
        :type username: str
        :param password: corresponding password
        :type password: str
        """
        if self.validate_uri(uri):
            self.uri = uri
        else:
            raise ValueError("Invalid URI string specified!")
        self.username = username
        self.password = password



    def validate_uri(self, uri):
        """
        Verifies a libvirt URI and throws an exception if the URI is invalid.
        This is done by checking if the URI contains one of the well-known
        libvirt protocols.

        :param uri: a libvirt URI
        :type uri: str
        """
        prefixes = {
            "lxc", "qemu", "xen", "hyperv", "vbox", "openvz", "uml", "phyp",
            "vz", "bhyve", "esx", "vpx", "vmwareplayer", "vmwarews",
            "vmwarefusion"
        }
        for prefix in prefixes:
            if prefix in uri and "://" in uri:
                return True
        return False



    def connect(self):
        """This function establishes a connection to the hypervisor"""
        auth = [
            [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE],
            self.retrieve_credentials, None
            ]
        return libvirt.openAuth(self.uri, auth, 0)



    def retrieve_credentials(self, credentials, user_data):
        """
        Retrieves the libvirt credentials in a strange format and hand it to
        the API in order to communicate with the hypervisor.
        To be honest, I have no idea why this has to be done this way. I have
        taken this function from the official libvirt documentation.

        :param credentials: libvirt credentials object
        :param user_data: some data that will never be used
        :type user_data: None
        """
        #get credentials for libvirt
        for credential in credentials:
            if credential[0] == libvirt.VIR_CRED_AUTHNAME:
                credential[4] = self.username
                if len(credential[4]) == 0:
                    credential[4] = credential[3]
            elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
                credential[4] = self.password
            else:
                return -1
        return 0



    def manage_snapshot(self, vm_name, snapshot_title, snapshot_text, remove_snapshot=False):
        """
        Creates/removes a snapshot for a particular virtual machine.
        This requires specifying a VM, comment title and text.
        There are also two alias functions.

        :param vm_name: Name of a virtual machine
        :type vm_name: str
        :param snapshot_title: Snapshot title
        :type snapshot_title: str
        :param snapshot_text: Snapshot text
        :type snapshot_text: str
        :param remove_snapshot: Removes a snapshot if set to True
        :type remove_snapshot: bool

        """
        #connect to hypervisor
        conn = self.connect()

        if conn == None:
            LOGGER.error("Unable to establish connection to hypervisor!")
            return False

        try:
            target_vm = conn.lookupByName(vm_name)
            if remove_snapshot:
                #remove snapshot
                target_snap = target_vm.snapshotLookupByName(snapshot_title, 0)
                return target_snap.delete(0)
            else:
                #create snapshot
                snap_xml = """<domainsnapshot><name>{}</name><description>{}
                    "</description></domainsnapshot>""".format(
                        snapshot_title, snapshot_text
                    )
                return target_vm.snapshotCreateXML(snap_xml, 0)
        except ValueError as err:
            if remove_snapshot:
                LOGGER.error("Unable to remove snapshot: '{}'".format(err))
            else:
                LOGGER.error("Unable to create snapshot: '{}'".format(err))



    #Aliases
    def create_snapshot(self, vm_name, snapshot_title, snapshot_text):
        """
        Creates a snapshot for a particular virtual machine.
        This requires specifying a VM, comment title and text.

        :param vm_name: Name of a virtual machine
        :type vm_name: str
        :param snapshot_title: Snapshot title
        :type snapshot_title: str
        :param snapshot_text: Snapshot text
        :type snapshot_text: str
        """
        return self.manage_snapshot(vm_name, snapshot_title, snapshot_text)

    def remove_snapshot(self, vm_name, snapshot_title):
        """
        Removes a snapshot for a particular virtual machine.
        This requires specifying a VM and a comment title.

        :param vm_name: Name of a virtual machine
        :type vm_name: str
        :param snapshot_title: Snapshot title
        :type snapshot_title: str
        """
        return self.manage_snapshot(
            vm_name, snapshot_title, "", remove_snapshot=True
        )



    def has_snapshot(self, vm_name, snapshot_title):
        """
        Returns whether a particular virtual machine is currently protected
        by a snapshot. This requires specifying a VM name.

        :param vm_name: Name of a virtual machine
        :type vm_name: str
        :param snapshot_title: Snapshot title
        :type snapshot_title: str
        """
        #connect to hypervisor
        conn = self.connect()

        if conn == None:
            raise ValueError("Unsable to establish connection to hypervisor!")
        try:
            target_vm = conn.lookupByName(vm_name)
            target_snapshots = target_vm.snapshotListNames(0)
            if snapshot_title in target_snapshots:
                return True
        except Exception as err:
            raise err
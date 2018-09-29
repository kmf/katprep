#! -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging
import pytest

from .utilities import load_config


@pytest.fixture
def nonexisting_vm():
    return "giertz.pinkepank.loc"


@pytest.fixture(params=['libvirt', 'pyvmomi'])
def virtualisation(request):
    return request.params


@pytest.fixture(scope="session")
def virtConfigFile(virtualisation):
    if virtualisation == 'libvirt':
        return "libvirt_config.json"
    elif virtualisation == 'pyvmomi':
        return "pyvmomi_config.json"


@pytest.fixture(scope="session")
def virtConfig(virtConfigFile):
    return load_config(virtConfigFile)


@pytest.fixture(scope="session")
def virtClass(virtualisation):
    if virtualisation == 'libvirt':
        LibvirtClient = pytest.importorskip("katprep.clients.LibvirtClient")
        return LibvirtClient.LibvirtClient
    elif virtualisation == 'pyvmomi':
        PyvmomiClient = pytest.importorskip("katprep.clients.PyvmomiClient")
        return PyvmomiClient.PyvmomiClient


@pytest.fixture
def virtClient(virtualisation, virtConfig, virtClass):
    if virtualisation == 'libvirt':
        address = virtConfig["config"]["uri"],
    elif virtualisation == 'pyvmomi':
        address = virtConfig["config"]["hostname"],

    return virtClass(
        logging.ERROR,
        address,
        virtConfig["config"]["api_user"],
        virtConfig["config"]["api_pass"]
    )

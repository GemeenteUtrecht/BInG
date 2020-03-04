================================
BInG - Beheer Inrichting Gebruik
================================

:Version: 0.7.0.dev0
:Source: https://github.com/GemeenteUtrecht/BInG
:Keywords: GU, Gemeente Utrecht, BInG, formulier
:PythonVersion: 3.7

|build-status| |requirements|

A consumer application managing BInG requests and meetings, build on top of the
ZGW APIs.

Developed by `Maykin Media B.V.`_ for Gemeente Utrecht Proeftuin.


Introduction
============

The 'Beheer Ingebruikname Gebruik' is responsible for verifying changes in the
public space in the municipality of Utrecht. It checks for managability,
how it's setup and how it's used.

Projects can be submitted for the 'BInG toets' by anyone, while staff can manage
these projects:

* planning meetings
* adding conclusions/results to the projects
* connect with external parties for checks, such as the fire department

https://www.utrecht.nl/ondernemen/vergunningen-en-regels/beheerinrichtinggebruik/handboek-openbare-ruimte/

Documentation
=============

See ``INSTALL.rst`` for installation instructions, available settings and
commands.

External services
=================

The application requires external APIs. The easiest way is to consume these
via an `NLX`_ outway.

The consumed services are:

* ZRC (v0.14.0)
* DRC (v0.11.3)
* ZTC (v0.11.1)
* BRC (v0.9.0)
* NRC (v0.5.0)

Go to https://directory.nlx.io/ and filter on organization ``gemeente-utrecht``

References
==========

* `Issues <https://github.com/GemeenteUtrecht/BInG/issues>`_
* `Code <https://github.com/GemeenteUtrecht/BInG>`_


.. |build-status| image:: https://travis-ci.org/GemeenteUtrecht/BInG.svg?branch=develop
    :alt: Build status
    :target: https://travis-ci.org/GemeenteUtrecht/BInG

.. |requirements| image:: https://requires.io/github/GemeenteUtrecht/BInG/requirements.svg?branch=master
     :target: https://requires.io/github/GemeenteUtrecht/BInG/requirements/?branch=master
     :alt: Requirements status

.. _testomgeving: http://bing.k8s.dc1.proeftuin.utrecht.nl

.. _Maykin Media B.V.: https://www.maykinmedia.nl

.. _NLX: https://docs.nlx.io

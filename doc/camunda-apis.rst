====================================
Camunda making calls to APIs for ZGW
====================================

Technical specs to make calls from Camunda to the APIs for Zaakgericht Werken.

Submitting a project
====================

A form collects the details for a project. At the end of the form, a process
instance is kicked off. A set of API calls are required to register the details
with the ZRC.

1. Create ``Zaak`` (operation ``zaak_create``)
2. Set initial status (operation ``status_create``)
3. Relate the uploaded documents with the ``Zaak``

The variables collected in the form are:

* Project ID
* Date the form was submitted
* Name of the project
* Type of procedure (``versneld`` or ``regulier``)
* List of documents uploaded to the DRC
* Preferred meeting date (zaak URL)

Additional information from configuration:

* ``RSIN`` of the municipality of Utrecht
* ``URL`` of the "aanvraag" case type

Relevant Python code:

**Creating the ZAAK and initial status**

.. code-block:: python
    :lineno:

    zrc_client = get_zrc_client(
        scopes=["zds.scopes.zaken.aanmaken"],
        zaaktypes=[config.zaaktype_aanvraag]
    )
    ztc_client = get_ztc_client()

    zaaktype_url = config.zaaktype_aanvraag
    startdatum = timezone.localdate(self.created).isoformat()

    zaak = zrc_client.create(
        "zaak",
        {
            "bronorganisatie": config.organisatie_rsin,
            "identificatie": f"BING-{self.project_id}",
            "zaaktype": zaaktype_url,
            "verantwoordelijkeOrganisatie": config.organisatie_rsin,
            "startdatum": startdatum,
            "omschrijving": f"BInG aanvraag voor {self.name}",
        },
    )

    self.zaak = zaak["url"]
    self.save(update_fields=("zaak",))

    # set the initial status
    zaaktype = ztc_client.retrieve("zaaktype", url=zaaktype_url)
    if not zaaktype["statustypen"]:
        logger.warning("Zaaktype %s has no statustypen!", zaaktype_url)
        return

    status_type = zaaktype["statustypen"][0]
    zrc_client.create(
        "status",
        {
            "zaak": self.zaak,
            "statusType": status_type,
            "datumStatusGezet": timezone.localtime().isoformat(),
            "statustoelichting": "Aanvraag ingediend",
        },
    )

**Relate documents**

.. code-block:: python
    :lineno:

    drc_client.create(
        "objectinformatieobject",
        {
            "informatieobject": document_url,
            "object": zaak_url,
            "objectType": "zaak",
            "beschrijving": "Aangeleverd stuk door aanvrager",
        },
    )

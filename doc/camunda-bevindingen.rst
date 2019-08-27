===================
Camunda bevindingen
===================

* Fetching open tasks, limiting by some business key works well
* Matching tasks via process instances to the underlying Project: ok, we can
  link data
* ``task/:id/form-variables`` geeft me niet de mogelijke enum waarden terug
* ``task/:id/form-variables`` geef me ook de resterende proces variables terug,
  die niet relevant zijn (enige die boeide was dus "Procedure")
* ``task/:id/claim`` eist een user ID om te claimen, dat wordt interessant als
  een taakapplicatie lokale users heeft die niet bekend zijn in Camunda...
  system user/service accounts maken per applicatie?
* ``task/:id/rendered-form`` is op zich interessant, maar styling-wise kan dat
  een nope gaan worden + het lijkt erop dat daar angular controls in zitten...
  doen we dus niet iets mee

Task handlers
=============

Generieke task handler of specifiek task handler waarbij je routing kan doen

-> introspectie van process definitie XML
-> usertasks extracten
-> usertask keys mappen op task handler in code (registry bouwen)

Code refactoring BInG
=====================

Er is momenteel een code path die het volgende doet:

* aanvraagprocedure versneld:
    * ontkoppel aanvraag van eventuele bestaande vergadering
    * indien producere regulier was: stuur een notificatie naar de aanvrager
* aanvraagprocedure regulier:
    * indien producere versneld was: stuur een notificatie naar de aanvrager

Dit is geschikt om te automatiseren via Camunda.

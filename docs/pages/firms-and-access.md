---
title: Firms and access
nav_order: 6
permalink: /firms-and-access/
---

# Firms and access

Nyayrithm is sold to law firms. This page explains how a firm is set up, who can do what, and
how people are invited.

## Getting a firm onto the platform

Billing is manual for now. The platform operator creates the firm in the admin portal, chooses
its plan, enters the seats and the date it is paid until (with an invoice reference), and
names the first owner. That person is emailed an invitation. When they accept, the firm is
live and they can invite everyone else.

A person who signs up without an invitation sees a page explaining that Nyayrithm is used
through a firm's subscription. They cannot create a firm themselves.

## Roles inside a firm

| | Owner | Admin | Attorney |
|---|---|---|---|
| Create cases, upload evidence, run proceedings | ✓ | ✓ | ✓ |
| See every case in the firm | ✓ | ✓ | only own and shared |
| Share a case with a colleague | any | any | cases they created |
| Delete a case | any | any | cases they created |
| Invite attorneys and admins | ✓ | ✓ | |
| Invite owners | ✓ | | |
| Change roles | ✓ (anyone) | attorneys and admins | |
| Remove people | ✓ (anyone but the last owner) | attorneys | |
| See the firm's plan and usage | ✓ | ✓ | read-only |

A firm always keeps at least one owner.

## Cases, sharing and what "inherits" means

A case belongs to the firm. Everything under it (its evidence, proceedings, agents and turns)
inherits the case's visibility. If an attorney can see a case, they can see all of that; if
they cannot, those ids do not exist as far as they are concerned: the API answers *not found*,
exactly as for an id that was never real, so identifiers cannot be probed.

To bring a colleague onto a case, share it with them. Sharing grants access to the case and
everything under it, not the ability to share it further or delete it.

## Invitations

- An invitation names an **email address** and a **role**.
- It carries a random, single-use link. Only a hash of the token is stored.
- It **expires after seven days**. Re-sending issues a new link and kills the old one.
- The person must sign in with **that email address** to accept; anyone else holding the link
  is refused.
- A pending invitation **holds a seat**, so a firm cannot over-invite. Accepting does not need
  a second seat.
- Owners and admins can see, re-send and withdraw pending invitations. The link is shown to
  the inviter once, at creation, in case the email is slow.

People can belong to more than one firm. A switcher in the sidebar chooses which firm they are
acting for; the choice is sent with every request and checked by the server.

## Plans and what they enforce

| Limit | Enforced when |
|---|---|
| Seats | an invitation is created or accepted |
| Subscription status and paid-until date | a case is created, a proceeding is created or started |
| Turns per proceeding | a proceeding is created |
| Simulations per month | a proceeding is started for the first time |
| Tokens per month | a proceeding is started **and before every turn** |
| Evidence storage | a file is uploaded |

When the token allowance runs out mid-proceeding, the proceeding **pauses** with a reason, the
browser is told, and it can be resumed when the allowance renews or the plan is raised. A
lapsed subscription blocks creating and running things, but never blocks *reading*: a firm
can always see its own work.

A suspended firm is locked out entirely.

## Isolation, in practice

The firm boundary is enforced in one place, the access service, used by every route and by
the live WebSocket. Tests exercise every route as an outsider, as a colleague, as an
owner and as a platform administrator, and a deliberately broken filter makes them fail.

The platform administrator role grants **no access** to firm data. It is not an admin who can
read everything: the operator's tools return counts and usage only.

## Development accounts

In a development stack the dev realm contains a firm owner and an attorney in a seeded
"Dev Firm", alongside a platform admin. They are listed on the development login screens and
exist only in the dev compose configuration. See [Running locally]({{ '/running-locally/' | relative_url }}).

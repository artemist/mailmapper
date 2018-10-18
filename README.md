# MailMapper

Currently, git can't remove names from committers in history. This can be a problem for trans people, who have previous names doxxed,
companies, who may need to remove committer names for GDPR compliance, and anyone who changes there name. Git provides a tool for changing names,
called a mailmap, which lets one rewrite what names and emails are displayed in shortlog and optionally log. However, the names are still
stored in the history and mailmaps must be stored per machine or per repository.


## The Solution

Our solution is to replace names with NaCl public keys, like `E5PO3SAIC6DK57SSJKTR3OREKUHZZKLSEHSLV4NPAA66KTQ2UEIQ`.
One can generate a public key and set their commit name to the public key. Then, they can publish a statement signed by the key
stating their name and email. This will be stored uploaded to a database and distributed to all script users.
Anyone else using the script will download the list of all users, verify their statements against the keys, then make a mailmap which maps
all keys to their most recent verified name.

## Overview

This script is still a work in progress and is not past the PoC stage.

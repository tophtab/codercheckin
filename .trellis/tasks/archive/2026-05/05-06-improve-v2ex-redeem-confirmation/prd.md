# Improve V2EX Redeem Confirmation

## Goal

Make V2EX daily check-in success detection more reliable by confirming the final mission page state after redeem and by treating balance parsing as supplemental information instead of the source of truth.

## Requirements

- After requesting `/mission/daily/redeem?once=...`, fetch `/mission/daily` again and treat the check-in as successful when the final page contains the already-claimed marker.
- Keep accepting an immediate redeem success page if V2EX returns the success marker directly.
- If the final mission page indicates the cookie is unauthenticated, report failure.
- If redeem succeeds but `/balance` cannot be parsed, do not fail the check-in. Log the balance parsing failure and still send the normal notification.
- Add focused tests for final mission-page confirmation and balance parsing failure after successful redeem.

## Out of Scope

- Browser automation.
- Replacing the HTTP client.
- Changing Cookie Cloud behavior.

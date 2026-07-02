# Classify without booking context lookup or urgency axis

The classifier operates on the raw message only — it does not look up booking state before classifying, and urgency is not a separate output dimension.

In production, booking context (check-in date, property, guest history) would be retrieved before classification to improve accuracy, and urgency would be a separate axis from category since they drive different SLAs (a maintenance issue mid-stay is different from one a week out). Both were deliberately cut to stay within scope for this build.

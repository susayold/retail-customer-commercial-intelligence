# Limitations and safe claims

## Mandatory limitations

- frequent-shopper panel, not all retailer customers;
- left censoring: first observed transaction is not acquisition;
- right censoring: late campaign post-periods may be incomplete;
- demographic coverage is partial and must be reported;
- store attributes are limited; do not invent geography or format;
- no verified region or channel fields are present in the source;
- promotion states are not randomly assigned;
- campaign recipients may be targeted;
- no campaign ROI or campaign cost is available;
- no COGS, margin or campaign cost;
- no inventory, replenishment or stockout fields;
- source quantity anomalies require flags;
- synthetic dates must not be interpreted as seasonality.
- the current modeled promotion universe has no valid `none` reference; comparisons remain restricted to observed promotion states;
- campaign post-period censoring means unobservable follow-up is blank, not zero;

## Claims never to make without new verified data

Market share, total retailer revenue, true store performance, causal campaign lift, causal promotion uplift, campaign ROI, profit margin, inventory optimization, stockout reduction and true customer lifetime value.

## Safe language

Observed panel spend, panel household engagement, first observed purchase, category penetration within the panel, promotion-associated activity, campaign-recipient behavior and observed customer value.

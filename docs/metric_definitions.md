# Metric Definitions

| Metric | Definition | Business use |
|---|---|---|
| Net Revenue | `gross_revenue - discount_amount + shipping_revenue - refund_amount` | Revenue after discounts and refunds. |
| Gross Profit | Net revenue minus product cost for completed orders. | Contribution before operating costs. |
| Gross Margin % | Gross profit ÷ net revenue. | Monetization quality. |
| Completed Orders | Distinct orders where `order_status = 'Completed'`. | Fulfilled transaction volume. |
| AOV | Net revenue ÷ completed orders. | Basket monetization. |
| Conversion Rate | Converted sessions ÷ all sessions. | End-to-end funnel efficiency. |
| Return Rate | Returned orders ÷ all orders. | Quality and expectation-setting signal. |
| Repeat Purchase Rate | Customers with at least two completed orders ÷ purchasing customers. | Loyalty signal. |
| 90-Day Churn | Purchasing customers whose most recent completed order was more than 90 days before 2026-01-01. | Reactivation audience sizing. |
| Month-1 Retention | Customers active one calendar month after first order ÷ customers in the original cohort. | Early repeat behavior. |
| 90-Day Revenue / Acquired Customer | Completed-order net revenue in the first 90 days after signup ÷ all matured customers acquired by the channel. | Acquisition quality without survivorship bias. |
| MoM Revenue Growth | Current-month net revenue ÷ prior-month net revenue − 1. | Trading momentum. |

## Funnel logic

The funnel is strictly nested:

`Session → Product view → Add to cart → Checkout → Order`

Step conversion rates use the immediately preceding stage as the denominator. Overall conversion uses all sessions.

## RFM segmentation

Customers with completed orders receive quintile scores for recency, frequency, and monetary value. The named segments are ordered so that recently active high-frequency customers become **Champions**, old high-frequency customers become **At Risk**, and old low-frequency customers become **Hibernating**. This avoids hiding valuable lapsed customers inside a generic loyalty group.


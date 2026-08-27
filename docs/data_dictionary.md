# Data Dictionary

The repository uses a reproducible synthetic dataset designed to behave like a mid-sized German e-commerce business. It contains no personal data.

## `customers.csv`

| Column | Type | Description |
|---|---|---|
| `customer_id` | text | Anonymous customer key. |
| `signup_date` | date | First known customer registration date. |
| `acquisition_channel` | text | Channel credited with acquiring the customer. |
| `state` / `region` / `city` | text | German geographic attributes used for regional analysis. |
| `preferred_device` | text | Most frequently used device class. |
| `marketing_consent` | integer | 1 when the synthetic customer can receive marketing. |
| `loyalty_score` | decimal | Latent simulation attribute used to produce realistic repeat behavior. Not used as a reported KPI. |

## `products.csv`

| Column | Type | Description |
|---|---|---|
| `product_id` / `sku` | text | Product keys. |
| `product_name` | text | Synthetic product label. |
| `category` / `subcategory` | text | Merchandise hierarchy. |
| `brand` | text | Synthetic brand. |
| `unit_price` / `unit_cost` | decimal | List price and product cost in EUR. |
| `launch_date` | date | Product launch date. |

## `sessions.csv`

| Column | Type | Description |
|---|---|---|
| `session_id` | text | Web session key. |
| `customer_id` | text, nullable | Known customer key; null represents a guest session. |
| `session_date` | date | Session date. |
| `channel` / `campaign` | text | Session-level marketing source. |
| `device` | text | Mobile, Desktop, or Tablet. |
| `pages_viewed` | integer | Pages in the session. |
| `session_duration_seconds` | integer | Session duration. |
| `viewed_product` | integer | 1 when the session reached a product page. |
| `added_to_cart` | integer | 1 when at least one product was added. |
| `checkout_started` | integer | 1 when checkout began. |
| `converted` | integer | 1 when an order was created. |
| `order_id` | text, nullable | Order key for converted sessions. |

## `orders.csv`

| Column | Type | Description |
|---|---|---|
| `order_id` / `session_id` / `customer_id` | text | Transaction and relationship keys. |
| `order_date` | date | Order creation date. |
| `channel` / `campaign` / `device` | text | Conversion context. |
| `state` / `region` | text | Shipping-region attributes. |
| `order_status` | text | Completed, Returned, or Cancelled. |
| `customer_order_number` | integer | Purchase sequence for known customers. |
| `days_since_previous_order` | integer, nullable | Days since the prior completed or attempted purchase. |
| `gross_revenue` | decimal | Sum of line-item price × quantity. |
| `discount_amount` | decimal | Order-level discount. |
| `shipping_revenue` | decimal | Shipping fee charged. |
| `refund_amount` | decimal | Refunded customer amount. |
| `net_revenue` | decimal | Gross revenue − discount + shipping − refund. |
| `cost_of_goods` | decimal | Product cost before return handling. |
| `gross_profit` | decimal | Net revenue − COGS for completed orders; zero for returned/cancelled orders. |

## `order_items.csv`

| Column | Type | Description |
|---|---|---|
| `order_item_id` | text | Line-item key. |
| `order_id` / `product_id` | text | Relationship keys. |
| `quantity` | integer | Units purchased. |
| `unit_price` / `unit_cost` | decimal | Captured unit economics in EUR. |
| `line_gross_revenue` | decimal | Unit price × quantity. |
| `line_cost` | decimal | Unit cost × quantity. |

## Modeling notes

- All dates are ISO `YYYY-MM-DD`.
- Financial values are stored as numeric EUR values, not formatted strings.
- A session can be anonymous. Customer retention and RFM analyses use only known customers with completed orders.
- Returned and cancelled orders retain their gross demand but contribute zero net revenue after the full refund.
- The simulation deliberately embeds behavioral differences by channel, device, category, and customer affinity so analysis yields decision-relevant patterns.


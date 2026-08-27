// Create a text parameter named DataRoot before using these queries.
// Example value: C:\repos\ecommerce-customer-intelligence\data\raw
// Paste each let/in block into its own blank query and name it as shown.

// Query: Customers
let
    Source = Csv.Document(File.Contents(DataRoot & "\\customers.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {{"customer_id", type text}, {"signup_date", type date}, {"acquisition_channel", type text}, {"state", type text}, {"region", type text}, {"city", type text}, {"preferred_device", type text}, {"marketing_consent", Int64.Type}, {"loyalty_score", type number}})
in
    Types

// Query: Products
let
    Source = Csv.Document(File.Contents(DataRoot & "\\products.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {{"product_id", type text}, {"sku", type text}, {"product_name", type text}, {"category", type text}, {"subcategory", type text}, {"brand", type text}, {"unit_price", Currency.Type}, {"unit_cost", Currency.Type}, {"launch_date", type date}})
in
    Types

// Query: Sessions
let
    Source = Csv.Document(File.Contents(DataRoot & "\\sessions.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {{"session_id", type text}, {"customer_id", type text}, {"session_date", type date}, {"channel", type text}, {"campaign", type text}, {"device", type text}, {"state", type text}, {"region", type text}, {"pages_viewed", Int64.Type}, {"session_duration_seconds", Int64.Type}, {"viewed_product", Int64.Type}, {"added_to_cart", Int64.Type}, {"checkout_started", Int64.Type}, {"converted", Int64.Type}, {"order_id", type text}})
in
    Types

// Query: Orders
let
    Source = Csv.Document(File.Contents(DataRoot & "\\orders.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {{"order_id", type text}, {"session_id", type text}, {"customer_id", type text}, {"order_date", type date}, {"channel", type text}, {"campaign", type text}, {"device", type text}, {"state", type text}, {"region", type text}, {"order_status", type text}, {"customer_order_number", Int64.Type}, {"days_since_previous_order", Int64.Type}, {"gross_revenue", Currency.Type}, {"discount_amount", Currency.Type}, {"shipping_revenue", Currency.Type}, {"refund_amount", Currency.Type}, {"net_revenue", Currency.Type}, {"cost_of_goods", Currency.Type}, {"gross_profit", Currency.Type}})
in
    Types

// Query: Order Items
let
    Source = Csv.Document(File.Contents(DataRoot & "\\order_items.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {{"order_item_id", type text}, {"order_id", type text}, {"product_id", type text}, {"quantity", Int64.Type}, {"unit_price", Currency.Type}, {"unit_cost", Currency.Type}, {"line_gross_revenue", Currency.Type}, {"line_cost", Currency.Type}})
in
    Types

